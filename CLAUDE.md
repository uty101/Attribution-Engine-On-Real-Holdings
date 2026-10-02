## 0. How this repo is run

Session 0 (this session) writes the plan and scaffolding only: no parser code, no attribution code, no data pulls. After session 0, session number equals section number: Session N builds all of Section N of `PLAN.md`, every step in it, in one session, and nothing from any other section. A reviewer (Claude in chat) reads the repo once per section and either approves it or returns fixes. You never start the next section until a new session tells you to.

Rules that hold for every session:

1. **No design choices.** Every parameter, definition, signature, schema, convention and file path is fixed in this document, in `PLAN.md` or in a later instruction file. If something is genuinely unspecified, append it to `decisions/OPEN.md` with 2 concrete options, finish every other step in the section that does not depend on it, and report it in the review file. Do not pick an option yourself.
2. **Commits.** One commit per step, message `step X.Y: <one line>`, on `main`. Push once at the end of the section. Never force push, never rewrite history, never amend a pushed commit. Stage files by explicit path; never `git add -A` or `git add .`.
3. **One review file per section**: `review/section_N.md`, following `review/TEMPLATE.md` exactly.
4. **Stop conditions.** Stop the section, write the review and status files, and push if any of these happen: a data pull fails; a test from an earlier section fails; a cross-check or gate in this document fails its stated threshold; a result can only be produced by making a design choice; a step would need a file or function outside that section's scope. Do not work around any of them.
5. **Tests are fixed.** Never loosen a tolerance, skip, xfail, or rewrite a test so that it passes. If a test in this document is wrong, stop under rule 4 and say why.
6. **Config is fixed.** Every parameter lives in `config.toml`. No numeric parameter is hard-coded in `attrib/`. The only exception is a constant written inside a formula in this document or an instruction file, which may be a literal with a comment citing the section where the formula is written. Do not change a value set in this document.
7. **Tests build what they read.** No test may depend on `outputs/` or `data/processed/` already existing. Tests read only `data/raw/` (committed), `tests/fixtures/` (committed) or synthetic data they generate. The full suite runs offline: `pytest -p socket --disable-socket` must pass.
8. **No network outside `scripts/pull_data.py`.** Nothing in `attrib/` or `tests/` touches the network. `attrib/edgar.py` holds the HTTP client and parsers, but only `scripts/pull_data.py` ever calls the client; tests drive the client with a fake session object.
9. **Determinism.** Every random draw uses `numpy.random.default_rng(seed)` with a seed from `config.toml`. Running the same section twice produces byte-identical CSV outputs and byte-identical PDFs. CSV float format is `%.10g`, line endings LF, UTF-8, no index column unless a schema in Section 7 names one.
10. **Evidence, not summaries.** Every numeric claim in a review file is backed by raw rows printed with `DataFrame.to_string()`, never by a description of them.
11. **Instructions and status live in the repo.** Every session's instructions are a file committed to `instructions/` before the session starts: `instructions/00_kickoff.md` (this document), then `instructions/NN_<name>.md` for each later session. The session prompt only names the file. Read that file from the repo and follow it; never edit an instruction file. Reviewer comments on a finished section arrive inside the next instruction file. Every session ends by writing `instructions/NN_<name>.status.md` with: outcome (completed or stopped), the last step reached, the reason for any stop, every question or blocker for the reviewer, and the output of `git log origin/main --oneline -3`; then commit and push it and stop. This applies to sessions that stop early or hit rule 4: the status file is always written and always pushed. Nothing is relayed by chat.
12. **Fresh-clone check at the end of every section from Section 1 on.** Clone the pushed repo into a short temp path, create a venv with `uv`, install from `requirements-lock.txt` then `pip install -e . --no-deps`, run `pytest -p socket --disable-socket -q`, and paste the full output into the review file.
13. **Precedence.** A later instruction file beats `PLAN.md`, which beats this document, which beats the source doc.
14. **Do not stage `CLAUDE.md` or `PLAN.md`** after session 0 unless an instruction file says to. If your own safety check refuses to edit `CLAUDE.md`, report it in the status file and the owner will commit it.
15. **Secrets.** `SEC_USER_AGENT` (format `Utkarsh Malhotra <email>`) and the optional `OPENFIGI_API_KEY` are read from the environment only. They never appear in any committed file, log or review. If `SEC_USER_AGENT` is unset when a pull needs it, stop under rule 4.

---

## 4. Conventions

1. **Holdings date.** A 13F or N-PORT book is the book at its period date. The 45-day filing lag does not matter for ex-post attribution and is reported only as a data fact.
2. **Equity rows only.** 13F: keep rows with `sshPrnamtType` = SH and no `putCall`. N-PORT: keep `invstOrSec` rows with `assetCat` = EC (equity common) and `units` = NS (number of shares). Everything else (options, principal amounts, futures, cash, money market, collateral) is dropped and its value reported.
3. **Aggregation.** Rows with the same 9-character CUSIP in the same book are summed (value and shares). CUSIPs are upper-cased; any CUSIP that is not 9 alphanumeric characters is reported and dropped.
4. **Amendments.** For each 13F period: start from the latest original 13F-HR; if a 13F-HR/A with `amendmentType` RESTATEMENT exists, the latest one replaces the book entirely; each 13F-HR/A with `amendmentType` NEW HOLDINGS filed after the book in use is appended. For N-PORT, if several NPORT-P filings exist for one period, use the latest by filing date.
5. **Weights.** w_i = value_i / Σ value over all kept equity rows in that book, including rows that later land in Unmapped or Unpriced. Weights in every book sum to 1.
6. **Buckets.** 14 buckets: the 12 FF12 industries in French's order (NoDur, Durbl, Manuf, Enrgy, Chems, BusEq, Telcm, Utils, Shops, Hlth, Money, Other), then Unmapped (no ticker), then Unpriced (ticker but no usable price at the start of the quarter). A mapped ticker with no SIC goes to Other and is logged. SIC codes in no FF12 range go to Other, as in French's own convention.
7. **Prices.** Adjusted close only. yfinance ticker = OpenFIGI ticker with `/` replaced by `-` (BRK/B → BRK-B).
8. **Position return over a quarter.** r_i = P_i(end) / P_i(q_start) − 1, with P_i(end) the adjusted close at the quarter's end date. If the price series ends before the quarter's end date, P_i(end) is the last available close (the position is held as cash at 0 return after that). If there is no price on q_start, the position goes to Unpriced.
9. **Book return.** The priced, mapped part of a book is held buy-and-hold through the quarter. Unmapped and Unpriced each earn that book's priced, mapped return, so the book return equals the priced, mapped return and r = Σ_s w_s r_s holds exactly over the 14 buckets.
10. **Sector return.** r_s = Σ_{i∈s} w_i r_i / Σ_{i∈s} w_i for each FF12 bucket with positive weight.
11. **Empty buckets.** If the fund has 0 weight in a bucket, r_s^P := r_s^B (selection 0 there). If the benchmark has 0 weight, r_s^B := r_B. If both are 0 the bucket contributes nothing.
12. **Monthly book returns.** Within each quarter the buy-and-hold value path is V_d = Σ_i w_i P_i(d) / P_i(q_start) over priced, mapped positions, renormalised to their weight sum, with delisted names held flat after their last close. The monthly return is the change in V between month-end trading days, where the quarter-start date stands in for the first month's start. Compounding the 3 monthly returns of a quarter gives the quarter's book return to 1e-12.
13. **Monthly stock returns.** Calendar-month periods from month-end adjusted closes. Never `DateOffset` arithmetic.
14. **NAV return.** Quarterly NAV return = adjusted close at q(h_{t+1}) / adjusted close at q(h_t) − 1, on the NAV ticker. Monthly NAV returns use month-end adjusted closes.
15. **Factors and rf.** French data is in percent and is divided by 100. rf is French's RF column. Excess return = return − RF for the same calendar month.
16. **Annualisation.** Monthly volatility × √12. Monthly covariance × 12 for annual tracking error. Daily covariance × 21 for monthly.
17. **Active share level.** Active share is computed on issuer level, the first 6 characters of the CUSIP, so share classes of the same issuer (GOOG and GOOGL) net against each other.
18. **Risk weights.** Risk uses the priced, mapped positions of each book renormalised to sum to 1 on each side. The excluded weight is reported next to every tracking-error figure.
19. **Failed gate.** A fund that fails the NAV gate (Section 5.4) keeps its row in Table 4 and is excluded from Tables 1 to 3, Charts 1 to 3 and `answers.csv`, with a line saying why.

---

## 6. Signatures and schemas (fixed)

### 6.1 Signatures

```python
# attrib/config.py
@dataclass(frozen=True)
class Config: ...                                   # one nested frozen dataclass per config table
def load_config(path: str | Path = "config.toml") -> Config

# attrib/edgar.py
class EdgarClient:
    def __init__(self, user_agent: str, min_interval: float, retries: int, session=None) -> None
    def get_json(self, url: str) -> dict
    def get_bytes(self, url: str) -> bytes
def list_13f_filings(client: EdgarClient, cik: int) -> pd.DataFrame          # FILINGS_13F
def find_infotable_name(index_json: dict) -> str
def parse_13f_infotable(xml: bytes, filing_date: date) -> pd.DataFrame       # HOLDINGS_RAW_13F
def resolve_13f_books(filings: pd.DataFrame, tables: dict[str, pd.DataFrame], dates: list[date]) -> pd.DataFrame  # HOLDINGS
def list_nport_filings(client: EdgarClient, series_id: str) -> pd.DataFrame  # FILINGS_NPORT
def parse_nport(xml: bytes) -> tuple[dict, pd.DataFrame]                     # (header, HOLDINGS_RAW_NPORT)
def resolve_nport_books(filings: pd.DataFrame, raw: pd.DataFrame, dates: list[date]) -> pd.DataFrame  # HOLDINGS
def units_check(book: pd.DataFrame) -> float                                # median implied price

# attrib/mapping.py
def parse_siccodes12(text: str) -> pd.DataFrame                             # industry, sic_lo, sic_hi
def sic_to_ff12(sic: int | None, table: pd.DataFrame) -> str
def build_security_map(figi: pd.DataFrame, overrides: pd.DataFrame, tickers: pd.DataFrame, sic: pd.DataFrame, ff12: pd.DataFrame) -> pd.DataFrame  # SECURITY_MAP

# attrib/returns.py
def quarter_calendar(price_index: pd.DatetimeIndex, dates: list[date]) -> pd.DataFrame   # QUARTERS
def book_quarter(book: pd.DataFrame, smap: pd.DataFrame, prices: pd.DataFrame, q_start, q_end) -> pd.DataFrame  # POSITION_RETURNS
def bucket_table(pos: pd.DataFrame) -> pd.DataFrame                          # BUCKETS
def book_monthly(book: pd.DataFrame, smap: pd.DataFrame, prices: pd.DataFrame, q_start, q_end) -> pd.Series

# attrib/reconstruction.py
def reconstruction_table(book_q: pd.DataFrame, nav: pd.DataFrame, cal: pd.DataFrame) -> pd.DataFrame  # TABLE4
def gate(table4: pd.DataFrame, threshold: float) -> pd.DataFrame

# attrib/brinson.py
def brinson_fachler(wP: pd.Series, rP: pd.Series, wB: pd.Series, rB: pd.Series) -> pd.DataFrame  # index bucket; allocation, selection, interaction

# attrib/linking.py
def carino(rP: pd.Series, rB: pd.Series, effects: pd.DataFrame) -> pd.DataFrame
def menchero(rP: pd.Series, rB: pd.Series, effects: pd.DataFrame) -> pd.DataFrame

# attrib/factors.py
def returns_based(excess: pd.Series, factors: pd.DataFrame, maxlags: int) -> dict
def rolling_betas(excess: pd.Series, factors: pd.DataFrame, window: int) -> pd.DataFrame
def factor_contrib_by_year(excess: pd.Series, factors: pd.DataFrame, fit: dict) -> pd.DataFrame  # TABLE2
def stock_betas(monthly_excess: pd.DataFrame, factors: pd.DataFrame, end_month, window: int, min_obs: int) -> pd.DataFrame
def holdings_exposure(weights: pd.Series, betas: pd.DataFrame, buckets: pd.Series) -> pd.Series

# attrib/risk.py
def active_share(wP_issuer: pd.Series, wB_issuer: pd.Series) -> float
def fill_daily(returns_d: pd.DataFrame, buckets: pd.Series) -> tuple[pd.DataFrame, pd.Series]
def active_cov(returns_d: pd.DataFrame, q, months: int, max_cond: float) -> tuple[pd.DataFrame, dict]
def te_decomposition(a: pd.Series, sigma_m: pd.DataFrame) -> pd.DataFrame   # ticker, a, mcte, cte

# attrib/report.py
def build_report(fund_id: str, results: dict, out_path: Path) -> Path

# attrib/__init__.py
def attribute(holdings_path, benchmark_path, start, end, data_dir="data", out_dir="outputs/reports", fund_name=None) -> Path
```

### 6.2 Schemas (CSV column order fixed)

- **FILINGS_13F**: entity, cik, accession, form, filing_date, period_date, amendment_type, infotable_name
- **FILINGS_NPORT**: entity, series_id, accession, filing_date, period_date
- **HOLDINGS_RAW_13F**: name, title_class, cusip, value_raw, value_usd, shares, ssh_type, put_call
- **HOLDINGS_RAW_NPORT**: entity, accession, period_date, name, title, cusip, isin, balance, units, val_usd, pct_val, asset_cat, issuer_cat, inv_country
- **HOLDINGS** (canonical, also the user-facing input schema for `attribute()`): entity, period_date, cusip, name, value_usd, shares. A user file may omit entity.
- **SECURITY_MAP**: cusip, ticker, yf_ticker, figi_name, cik, sic, ff12, map_status, source
- **QUARTERS**: t, holdings_date, q_start, q_end
- **POSITION_RETURNS**: entity, t, cusip, issuer6, ticker, bucket, weight, r, delisted_in_quarter, last_price_date
- **BUCKETS**: entity, t, bucket, weight, r
- **TABLE4** (`outputs/tables/reconstruction.csv`): entity, t, q_start, q_end, book_return, nav_return, gap
- **coverage** (`outputs/tables/coverage.csv`): entity, period_date, filing_date, lag_days, n_rows_raw, n_rows_kept, dropped_value_usd, total_value_usd, median_implied_price, amendments_used, unmapped_weight, unpriced_weight, other_nosic_weight
- **brinson_quarterly.csv**: fund, t, bucket, wP, wB, rP, rB, allocation, selection, interaction
- **linked.csv** (Table 1): fund, method, bucket, allocation, selection, interaction, total
- **factor_fit.csv**: series_id, series_kind (book, nav), coef, value, se_hac, t_hac, r2, resid_vol_ann, n_months
- **factor_by_year.csv** (Table 2): series_id, year, excess_return, mkt, smb, hml, rmw, cma, umd, alpha, residual, r2_full
- **rolling_betas.csv**: series_id, month_end, mkt, smb, hml, rmw, cma, umd
- **holdings_exposures.csv**: fund, holdings_date, side (fund, benchmark, active), mkt, smb, hml, rmw, cma, umd
- **risk_quarterly.csv** (Table 3): fund, holdings_date, active_share, te_exante, excluded_weight_fund, excluded_weight_bench, n_names, max_fill_share, delta_lw, ridged
- **cte_positions.csv**: fund, holdings_date, ticker, bucket, a, mcte, cte
- **cte_sectors.csv**: fund, holdings_date, bucket, cte
- **bootstrap.csv**: fund, series (allocation, selection, interaction, gap), mean, p05, p95
- **answers.csv**: question, fund, figure, value, interval_lo, interval_hi, source_table, source_row

---

## Amendments

1. Python 3.12 everywhere. The lock is built with `uv pip compile pyproject.toml --extra dev --universal --python-version 3.12 -o requirements-lock.txt`, and every venv with `uv venv --python 3.12` (`instructions/01_section_1.md`, Section B, OPEN-04).
2. Build backend: `[build-system] requires = ["setuptools>=68"]`, `build-backend = "setuptools.build_meta"`; `[tool.setuptools] packages = ["attrib"]` (`instructions/01_section_1.md`, Section B, OPEN-03).
3. `EdgarClient.__init__(self, user_agent: str, min_interval: float, retries: int, backoff: Sequence[float], session=None)`; `len(backoff)` must equal `retries`, else `ValueError` (`instructions/01_section_1.md`, Section B, OPEN-06).
4. OPEN-01 to OPEN-30 are decided in `instructions/01_section_1.md` Section B; that table is binding.
5. `EdgarClient.__init__(self, user_agent: str, min_interval: float, retries: int, backoff: Sequence[float], timeout: float, session=None)`; `timeout` is `[edgar] timeout_s` and is passed to every `get`; `requests.Timeout` and `requests.ConnectionError` retry exactly like HTTP 5xx. This supersedes line 3 on the signature (`instructions/01b_section_1_completion.md`, Section B and step 1.2b).
6. Rule 9: the CSV float format is `%.17g`, not `%.10g` (`instructions/01b_section_1_completion.md`, Section B).
7. H starts at 2019-09-30: 28 holdings dates and 28 return quarters (Q4 2019 to Q3 2026), `sample.first_holdings_date = "2019-09-30"`. Read 28 wherever 30 holdings dates or 30 quarters are written (`instructions/01b_section_1_completion.md`, Section B).
8. HOLDINGS: entity, period_date, cusip, isin, sec_id, name, value_usd, shares. `sec_id` is the CUSIP when it is a valid 9-character CUSIP, else the ISIN when it is a valid 12-character ISIN; a row with neither is dropped and its value counted in `dropped_value_usd`. 13F rows have `isin` blank and `sec_id` = `cusip`. Aggregation (Convention 4.3) is by `sec_id` (`instructions/01b_section_1_completion.md`, step 1.4b).
9. `list_nport_filings` keeps `NPORT-P` and `NPORT-P/A`; for each period the latest filing by filing date wins, whether original or amendment (`instructions/01b_section_1_completion.md`, Section B and step 1.4b).
10. Convention 4.17, for Section 6: the active share issuer key is the SEC CIK from SECURITY_MAP; a row with no CIK is its own issuer, keyed by `sec_id` (`instructions/01b_section_1_completion.md`, Section B).
