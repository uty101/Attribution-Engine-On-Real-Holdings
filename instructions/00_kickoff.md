# instructions/00_kickoff.md — Session 0 instructions for Claude Code

Repo: https://github.com/uty101/Attribution-Engine-On-Real-Holdings
Project: Performance and Risk Attribution Engine on real 13F holdings (quant project 4 of the home-built series)
Source doc: `Project Outline/04_Attribution_Engine.docx`

This document is the specification. Nothing in it is yours to redesign. Where it corrects or tightens the source doc, this document wins.

---

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

## 1. What the project answers

1. For each fund, how much of the excess return over its benchmark across the full window came from sector allocation, stock selection and interaction, and are the mean quarterly allocation and selection effects distinguishable from 0?
2. How much of each fund's monthly return is explained by market, size, value, profitability, investment and momentum, how did those exposures drift, and how much is residual?
3. How concentrated is each fund's active risk: active share, ex-ante tracking error, and which positions and sectors contribute most to tracking error?
4. How far does the return of the quarter-start 13F book miss the fund's reported NAV return each quarter, and what does the size and sign of that gap say about intra-quarter trading, cash, fees and holdings the 13F cannot see?

---

## 2. Corrections to the source doc (already applied below)

1. **CUSIP to ticker.** SEC `company_tickers.json` and company facts carry no CUSIP. Mapping is CUSIP → ticker via the OpenFIGI mapping API, ticker → CIK via `company_tickers.json`, CIK → SIC via the EDGAR submissions API.
2. **Benchmark history.** The iShares holdings CSV is today's file only and cannot give 2019 snapshots. Benchmark holdings come from the ETF's own Form N-PORT filings on EDGAR (quarter end, keyed by CUSIP). Fund and benchmark therefore join on CUSIP.
3. **13F is filed by the manager, not the fund.** Funds are single-strategy managers whose 13F book should track one mutual fund, and each is gated (Section 5.4) on how closely its 13F book tracks the fund's NAV. A fund that fails the gate is reported as failed and kept out of the attribution results.
4. **Reported returns.** Fact sheets are manual PDFs. The fund's reported return is the NAV total return from yfinance adjusted close on the fund's institutional share class, net of fees.
5. **13F value units.** Values are in thousands of dollars for filings made before 2023-01-03 and in dollars from then on. The parser converts on filing date and checks the result (Section 5.1).
6. **Sectors.** SIC does not map to 11 GICS-style buckets without invented rules. Sectors are the Fama-French 12 industries, a published SIC mapping from the same library as the factors, applied identically to fund and benchmark and labelled FF12, never GICS.
7. **Delisted names and missing prices** get fixed rules (Section 4) and their weight is reported every quarter.
8. **Brinson identity.** It holds only if both sides' weights sum to 1 over the same buckets. Unmapped and Unpriced are explicit buckets on both sides, and empty-sector returns have fixed fill rules.
9. **Carino** k_t is 0/0 when r_P,t = r_B,t; the limit is used. **Menchero** is written out (Section 5.6) since the source doc only names it. "Agree to a few bp" becomes a measured figure, not a test.
10. **Table 2 by year.** 6 betas cannot be estimated from 12 monthly points. Table 2 uses full-sample betas; rolling 36-month betas are for Chart 2 only.
11. **Project 1 dependency dropped.** Project 1 is not producing characteristic z-scores. Holdings-based exposures come from each stock's own 36-month factor betas.
12. **Project 3 dependency pinned.** `pc.cov.cov_lw_cc`, `pc.cov.condition_cov`, `pc.cov.window_daily` and `pc.stats.stationary_bootstrap_indices` are imported from project 3, installed as a git dependency pinned to commit `88e865d8202023cd495dd9866c49e6adbc9f4654`. `pc.cov.estimate_cov` is not used because it needs project 3's config.
13. **Small sample.** About 30 quarters. Mean quarterly effects get stationary bootstrap intervals; no selection skill is claimed when an interval contains 0.
14. **PDF.** weasyprint needs GTK and Pango, which is painful on Windows. Reports are built with reportlab using `invariant=1` so output is byte-identical between runs.
15. **Entry point and the no-network rule.** `attribute()` reads local data only. `scripts/pull_data.py --holdings` fetches what a new holdings file needs.
16. **Window.** The source doc says both 5 years and 28 quarters. The window is every quarter end from 2019-03-31 to 2026-06-30 (30 holdings dates, 30 return quarters, Q2 2019 to Q3 2026). Holdings are dated by period date, not filing date; that is correct for ex-post attribution and is not look-ahead.
17. **Report length.** 7 exhibits do not fit 2 pages. The report is at most 4 A4 pages.

---

## 3. Funds, benchmarks, data and sample

### 3.1 Entities

| id | type | name | 13F filer CIK | NAV ticker | benchmark id |
|---|---|---|---|---|---|
| akre | fund | Akre Capital Management (Akre Focus Fund) | 1112520 | AKRIX | ivv |
| jensen | fund | Jensen Investment Management (Jensen Quality Growth Fund) | 1106129 | JENIX | ivv |
| polen | fund | Polen Capital Management (Polen Growth Fund) | 1034524 | POLIX | iwf |
| ivv | benchmark | iShares Core S&P 500 ETF | n/a | IVV | n/a |
| iwf | benchmark | iShares Russell 1000 Growth ETF | n/a | IWF | n/a |

Benchmark N-PORT series are resolved from the ticker via `company_tickers_mf.json` (fields cik, seriesId, classId, symbol). The resolved CIK and series ID are written to `data/raw/sec/series_resolved.csv` and printed in the review. Polen's 13F carries over 200 positions against a fund of about 25; it is expected to be the fund most at risk of failing the gate.

### 3.2 Sources

| need | source | committed as |
|---|---|---|
| 13F filing list | `https://data.sec.gov/submissions/CIK{cik:010d}.json` (plus each `filings.files` page) | `data/raw/edgar/13f/filings_{id}.csv` |
| 13F information table | filing `index.json` under `https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/`; the information table is the XML file whose name is not `primary_doc.xml` | `data/raw/edgar/13f/{id}/{period}_{accession}.xml` |
| N-PORT filing list | `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={seriesId}&type=NPORT-P&dateb=&owner=include&count=100&output=atom` | `data/raw/edgar/nport/filings_{id}.csv` |
| N-PORT holdings | `primary_doc.xml` of each NPORT-P filing | parsed fields in `data/raw/edgar/nport/holdings_{id}.csv`; source sha256 in the manifest; XML not committed except the 1 test fixture |
| tickers | `https://www.sec.gov/files/company_tickers.json`, `https://www.sec.gov/files/company_tickers_mf.json` | `data/raw/sec/` as downloaded |
| SIC | submissions JSON field `sic` and `sicDescription` per CIK | `data/raw/sec/sic.csv` (cik, name, sic, sic_description) |
| CUSIP → ticker | `https://api.openfigi.com/v3/mapping`, jobs `{"idType":"ID_CUSIP","idValue":cusip,"exchCode":"US"}` | `data/raw/openfigi/mapping.csv` |
| prices | yfinance `auto_adjust=True`, daily, 2015-12-01 to 2026-09-30 inclusive (`end="2026-10-01"`, yfinance end is exclusive) | `data/raw/prices/adjclose.parquet` (dates × tickers) |
| NAV and ETF prices | same call for AKRIX, JENIX, POLIX, IVV, IWF | `data/raw/prices/nav_adjclose.csv` |
| factors | Ken French `F-F_Research_Data_5_Factors_2x3_CSV.zip` and `F-F_Momentum_Factor_CSV.zip`, monthly block only | `data/raw/french/ff5_monthly.csv`, `data/raw/french/mom_monthly.csv` |
| FF12 map | Ken French `Siccodes12.zip` | `data/raw/french/Siccodes12.txt` |

French files live under `https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/`.

### 3.3 Sample

- Holdings dates H: the 30 calendar quarter ends from 2019-03-31 to 2026-06-30.
- Every entity must have holdings for every date in H. If any is missing, stop under rule 4 and list the gaps.
- Every N-PORT filing used must have a reporting period date equal to a calendar quarter end in H. Any other date is ignored. If a date in H has no N-PORT filing, stop under rule 4.
- Quarter end trading day q(h): the last date ≤ h in the IVV price index.
- Return quarter t runs from q(h_t) close to q(h_{t+1}) close, where h_{t+1} is the next calendar quarter end. The last return quarter runs from q(2026-06-30) to q(2026-09-30).
- Monthly series: calendar months from April 2019 to the earlier of September 2026 and the last month in the French files.

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

## 5. Methods (fixed)

### 5.1 13F and N-PORT parsing (`attrib/edgar.py`)

- XML is parsed with lxml, namespace-agnostic (match on local names). Pre-2013 text filings are out of scope; none fall in the window.
- 13F fields kept per row: nameOfIssuer, titleOfClass, cusip, value, sshPrnamt, sshPrnamtType, putCall (may be absent).
- Units: `value_usd = value × 1000` if filing date < 2023-01-03, else `value_usd = value`.
- Units check per filing, after conversion: implied price p_i = value_usd / shares over kept rows; the median p_i must lie in [1, 5000]. Outside that range, stop under rule 4 and print the filing.
- N-PORT fields kept per row: name, title, cusip, isin, balance, units, valUSD, pctVal, assetCat, issuerCat, invCountry. The filing header gives seriesId and repPdDate.
- Client: `requests.Session` with header `User-Agent: $SEC_USER_AGENT`, at most 5 requests a second (minimum interval 0.2 s), up to 3 retries with waits of 2, 4 and 8 s on HTTP 429 or 5xx, then fail.

### 5.2 Mapping (`attrib/mapping.py`)

- OpenFIGI: batches of 10 jobs without a key (25 requests a minute) or 100 with `OPENFIGI_API_KEY` (25 requests per 6 s). From each job's results take the first entry with `marketSector` = Equity. No result gives `ticker` blank and `status` = no_match.
- Overrides: `data/manual/overrides.csv` (Section 7) is applied after OpenFIGI. It starts empty; the reviewer fills it in a later instruction file.
- ticker → CIK: exact match on `company_tickers.json` ticker after `-` and `/` are both normalised to `-`.
- CIK → SIC: submissions JSON. No CIK or no SIC gives FF12 bucket Other, logged with reason.
- SIC → FF12: parse `Siccodes12.txt` ranges.

### 5.3 Book returns (`attrib/returns.py`)

Conventions 4.5 to 4.14. Outputs per entity and quarter: bucket weights, bucket returns, book return, unmapped weight, unpriced weight, delisted-in-quarter weight.

### 5.4 Reconstruction error and gates (`attrib/reconstruction.py`)

- Gap_t = book return_t − NAV return_t, per fund and quarter.
- **Benchmark check.** For ivv and iwf, the gap against the ETF's own NAV ticker. If any quarter's |gap| > 0.01, stop under rule 4: a gap that size points at a parsing or mapping bug, not at index rebalancing.
- **Fund gate.** Pearson correlation of quarterly book return with NAV return over the full window, per fund. Pass if ≥ 0.90.
- Statistics per fund: mean gap, standard deviation, mean |gap|, annualised tracking error of the gap (std × 2), correlation, and a 90% stationary bootstrap interval for the mean gap (Section 5.9).

### 5.5 Brinson-Fachler single period (`attrib/brinson.py`)

Over the 14 buckets s, fund P, benchmark B, r_B the benchmark book return:

- Allocation_s = (w_s^P − w_s^B)(r_s^B − r_B)
- Selection_s = w_s^B (r_s^P − r_s^B)
- Interaction_s = (w_s^P − w_s^B)(r_s^P − r_s^B)
- Σ_s (Allocation_s + Selection_s + Interaction_s) = r_P − r_B, tested to 1e-10.

### 5.6 Multi-period linking (`attrib/linking.py`)

d_t = r_P,t − r_B,t. R_P = Π(1 + r_P,t) − 1, R_B likewise, D = R_P − R_B, T the number of quarters.

**Carino.** k_t = [ln(1 + r_P,t) − ln(1 + r_B,t)] / d_t, and k_t = 1/(1 + r_P,t) when |d_t| < 1e-12. k = [ln(1 + R_P) − ln(1 + R_B)] / D, and k = 1/(1 + R_P) when |D| < 1e-12. Linked effect = Σ_t (k_t / k) effect_t.

**Menchero.** M = (D / T) / [(1 + R_P)^(1/T) − (1 + R_B)^(1/T)], and M = (1 + R_P)^((T − 1)/T) when |D| < 1e-12. α_t = [(D − M Σ_t d_t) / Σ_t d_t²] × d_t, and α_t = 0 when Σ_t d_t² < 1e-24. Linked effect = Σ_t (M + α_t) effect_t.

Both linked sets sum to D, tested to 1e-12 on synthetic data and 1e-10 on real data. The Carino minus Menchero difference per sector and effect is reported, not tested.

### 5.7 Returns-based factor attribution (`attrib/factors.py`)

- Model: r_P,t − RF_t = α + β_M MktRF_t + β_S SMB_t + β_V HML_t + β_R RMW_t + β_C CMA_t + β_U UMD_t + ε_t, OLS, on monthly data.
- Run for each fund's book series and its NAV series, and for each benchmark's book series as a sanity check.
- Full sample: statsmodels OLS with HAC standard errors, `maxlags = 3`.
- Rolling: 36-month windows, complete windows only, for Chart 2.
- Table 2 by calendar year, full-sample betas: contribution_j,y = Σ_{t∈y} β̂_j f_j,t; alpha_y = α̂ × months in year y; residual_y = Σ_{t∈y} ε̂_t; plus the year's excess return, the full-sample R², and the annualised residual volatility std(ε̂) × √12.

### 5.8 Holdings-based exposures (`attrib/factors.py`)

- Stock betas β_i at each holdings date h: OLS of the stock's monthly excess returns on the 6 factors over the 36 calendar months ending at h's month, if at least 24 months are present.
- A stock with fewer than 24 months takes the mean beta of the stocks in the same FF12 bucket that have valid betas at h.
- Exposure β_P,j = Σ_i w_i β_i,j over priced, mapped positions renormalised to sum to 1. Same for the benchmark; active = fund − benchmark.

### 5.9 Bootstrap

`pc.stats.stationary_bootstrap_indices(n, mean_block, reps, seed)` with mean_block = 4 quarters, reps = 10000, seed from config. Interval = 5th and 95th percentiles of the resampled mean. Applied to the quarterly total allocation, selection and interaction series per fund, and to the reconstruction gap per fund.

### 5.10 Active share and tracking error (`attrib/risk.py`)

- AS = ½ Σ_k |w_k^P − w_k^B| over issuers k (Convention 4.17), using all mapped positions; unmapped weight is reported beside it.
- Covariance at holdings date h: daily simple returns of the union of both books' priced, mapped tickers, rows from `pc.cov.window_daily(returns_d, q(h), 36)`.
- Fill: a missing daily return for ticker i is filled with the equal-weight mean that day of the other tickers in i's FF12 bucket that have a return that day; if none, the equal-weight mean of all tickers with a return that day. The fill share per ticker is logged.
- Σ_d = `pc.cov.cov_lw_cc(X, ddof=0)`, then `pc.cov.condition_cov(Σ_d, max_cond)`, then Σ_m = 21 Σ_d.
- a = w^P − w^B on that ticker set. TE = √(12 a′ Σ_m a). MCTE_i = 12 (Σ_m a)_i / TE. CTE_i = a_i MCTE_i. Σ_i CTE_i = TE, tested to 1e-12.
- Sector CTE = Σ of CTE_i within the FF12 bucket.
- Realised tracking error: std of monthly book active returns × √12 over the full window, reported beside the ex-ante average.

### 5.11 Report (`attrib/report.py`)

reportlab, A4, Helvetica, `invariant=1`, at most 4 pages. Page 1: fund, benchmark, window, data coverage line, Table 1, Chart 1. Page 2: Table 2, Chart 2. Page 3: Table 3, Chart 3. Page 4: Table 4 and the 13F limits paragraph. Charts are matplotlib PNGs at 150 dpi with `metadata={"Software": None}`, embedded from memory. Figures shown in a table or chart are not restated in prose on the page.

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

## 7. config.toml contents

```toml
[run]
bootstrap_seed = 20261002

[sample]
first_holdings_date = "2019-03-31"
last_holdings_date = "2026-06-30"
last_return_date = "2026-09-30"
price_start = "2015-12-01"
price_end_exclusive = "2026-10-01"

[entities.akre]
type = "fund"
cik = 1112520
nav_ticker = "AKRIX"
benchmark = "ivv"
[entities.jensen]
type = "fund"
cik = 1106129
nav_ticker = "JENIX"
benchmark = "ivv"
[entities.polen]
type = "fund"
cik = 1034524
nav_ticker = "POLIX"
benchmark = "iwf"
[entities.ivv]
type = "benchmark"
etf_ticker = "IVV"
[entities.iwf]
type = "benchmark"
etf_ticker = "IWF"

[edgar]
min_interval_s = 0.2
retries = 3
backoff_s = [2, 4, 8]
units_switch_date = "2023-01-03"
implied_price_lo = 1.0
implied_price_hi = 5000.0

[openfigi]
batch_no_key = 10
batch_with_key = 100
min_interval_no_key_s = 2.4
min_interval_with_key_s = 0.24

[gates]
fund_nav_corr_min = 0.90
benchmark_gap_max = 0.01

[linking]
zero_tol = 1e-12

[factors]
names = ["mkt", "smb", "hml", "rmw", "cma", "umd"]
hac_maxlags = 3
rolling_window = 36
stock_beta_window = 36
stock_beta_min_obs = 24

[risk]
cov_months = 36
daily_to_monthly = 21
months_per_year = 12
max_cond = 1e6
top_n_positions = 15

[bootstrap]
mean_block = 4
reps = 10000
lo = 0.05
hi = 0.95

[report]
dpi = 150
max_pages = 4
```

`data/manual/overrides.csv` columns: kind (ticker, quarter_return), cusip, period_date, value, source_note. Starts with the header only.

---

## 8. Section list (PLAN.md expands exactly these; add or remove nothing)

### Section 1 — Foundation and EDGAR holdings
- 1.1 `attrib/config.py`, `config.toml`. Tests: key set equality both ways against Section 7; every fund's benchmark id exists; dates parse and are calendar quarter ends.
- 1.2 `EdgarClient`. Tests with a fake session: User-Agent header sent; minimum interval respected (fake clock); 429 then 200 retries with the configured waits; 3 failures raise.
- 1.3 13F parsing: `list_13f_filings`, `find_infotable_name`, `parse_13f_infotable`, `units_check`, `resolve_13f_books`. Fixtures in `tests/fixtures/`: Akre's information table for period 2023-06-30 (accession 0001112520-23-000013, dollars) and Akre's for period 2022-06-30 (thousands). Tests: units rule on both; put/call and PRN rows dropped (synthetic XML); duplicate CUSIP rows summed (synthetic); RESTATEMENT replaces and NEW HOLDINGS appends (synthetic filings table); median implied price in range for both fixtures.
- 1.4 N-PORT: `list_nport_filings`, `parse_nport`, `resolve_nport_books`. One real IVV `primary_doc.xml` committed as a fixture. Tests: only EC with NS units kept; header seriesId and repPdDate read; latest filing wins for a duplicated period (synthetic).
- 1.5 `scripts/pull_data.py --stage edgar`: filings lists, 13F information tables, N-PORT holdings for all 5 entities, `series_resolved.csv`, and `data/raw/MANIFEST.json` (pull time UTC, library versions, row counts, sha256 per committed file, sha256 per downloaded-but-not-committed N-PORT XML). Test: manifest hashes match committed files.
- 1.6 `outputs/tables/coverage.csv` (columns through `amendments_used`; mapping columns stay blank until Section 2) and `data/processed/holdings_{id}.csv`. Checks: Section 3.3 date rules and the 5.1 units check for every book. Review evidence: the full coverage table; for the Akre 2023-06-30 book, the 5 largest positions printed both as parsed rows and as the raw XML `infoTable` elements, so the reviewer can check them against the filing on EDGAR.

### Section 2 — Mapping, sectors, prices and factors
- 2.1 `pull_data.py --stage sec` and `--stage figi`: ticker files, SIC for every mapped CIK, OpenFIGI mapping for every CUSIP in any book.
- 2.2 `attrib/mapping.py`. Tests: FF12 parse gives 3571 → BusEq, 2834 → Hlth, 6021 → Money, 1311 → Enrgy, 4911 → Utils, 9999 → Other, and every range lands in exactly 1 industry; ticker normalisation BRK/B → BRK-B; overrides beat OpenFIGI.
- 2.3 `pull_data.py --stage prices` and `--stage french`. Tests: French loader returns decimals (a known month printed in percent and in decimals); price panel index is sorted and unique.
- 2.4 `attrib/returns.py` calendar and loaders only (no book returns yet): `quarter_calendar`, daily and monthly stock returns. Tests: 30 rows in QUARTERS; q_start of t+1 equals q_end of t; month-end selection uses calendar periods.
- 2.5 Fill the mapping columns of `coverage.csv`. Write for the reviewer: `outputs/tables/unmapped_top.csv` (20 largest unmapped CUSIPs by maximum weight across books, with name and every period held), `outputs/tables/unpriced_top.csv` (same for unpriced), `outputs/tables/large_moves.csv` (every held ticker-quarter with a daily |return| > 25%, with date, return, weight, entity). Review evidence: all 3 files in full, and the unmapped and unpriced weight per entity per quarter. This section ends there; overrides arrive in instruction 03.

### Section 3 — Book returns and reconstruction
- 3.1 Apply `data/manual/overrides.csv` (from instruction 03). Test: every override row changes exactly the rows it names.
- 3.2 `book_quarter`, `bucket_table`, `book_monthly`. Tests: hand-built 3-stock, 1-quarter case to 1e-12; delisted-mid-quarter case; Σ w_s r_s equals the book return to 1e-12 on every real book; 3 monthly returns compound to the quarterly return to 1e-12.
- 3.3 Benchmark check (Section 5.4) for ivv and iwf. Review evidence: all 60 quarter rows.
- 3.4 `attrib/reconstruction.py`: Table 4, fund gate, gap bootstrap. Writes `reconstruction.csv`, `gate.csv` (fund, corr, pass), and the gap rows of `bootstrap.csv`. Review evidence: Table 4 in full and the gate rows.

### Section 4 — Brinson and linking
- 4.1 `attrib/brinson.py`. Tests: identity to 1e-10 on 1000 random synthetic cases (seed from config) and on every real fund quarter; a hand-worked 3-sector example written in the test docstring; empty-bucket rules.
- 4.2 `attrib/linking.py`. Tests: Carino and Menchero sums equal D to 1e-12 on synthetic data and 1e-10 on real data; a period with r_P,t = r_B,t exactly uses the limit; single-period case gives the effects unchanged.
- 4.3 Per passing fund: `brinson_quarterly.csv`, `linked.csv` (both methods), bootstrap rows for allocation, selection and interaction, Chart 1 `outputs/figures/{fund}_alloc_vs_sel.png` (cumulative Carino-linked allocation and selection through each quarter, 2 lines). Review evidence: Table 1 for both methods, the Carino minus Menchero difference rows, bootstrap rows.

### Section 5 — Factor attribution
- 5.1 `returns_based`, `rolling_betas`, `factor_contrib_by_year`. Tests: recovers known betas from synthetic data to 1e-10 with no noise; HAC standard errors match a direct statsmodels call; yearly contributions plus alpha plus residual sum to the year's excess return to 1e-12. Writes `factor_fit.csv`, `factor_by_year.csv`, `rolling_betas.csv`, Chart 2 `outputs/figures/{fund}_rolling_betas.png` (6 lines).
- 5.2 `stock_betas`, `holdings_exposure`. Tests: min-obs rule; bucket fallback. Writes `holdings_exposures.csv` and `outputs/figures/{fund}_exposures_hb_vs_rb.png` (holdings-based fund exposure at each quarter against the rolling returns-based beta, 1 panel per factor). Review evidence: full-sample fit rows for every series, the IVV book's market beta, Table 2 for each passing fund.

### Section 6 — Risk
- 6.1 `fill_daily`, `active_cov` using project 3's functions. Tests: `pc` imports offline; fill rule on a synthetic panel; output is symmetric and positive definite.
- 6.2 `active_share`, `te_decomposition`. Tests: Euler identity to 1e-12; AS of identical books is 0 and of disjoint books is 1; share classes of one issuer net. Writes `risk_quarterly.csv`, `cte_positions.csv`, `cte_sectors.csv`, realised TE rows, Chart 3 `outputs/figures/{fund}_cte_top15.png` (last holdings date). Review evidence: Table 3 in full, top 15 CTE rows at the last date, sector sums.

### Section 7 — Report and entry point
- 7.1 `attrib/report.py`. Tests: 2 builds of the same inputs are byte-identical; page count ≤ 4.
- 7.2 `attribute()`. Test: a tiny synthetic data directory in `tests/fixtures/mini/` (3 stocks, 2 quarters, its own prices, map and factors) runs end to end offline and writes a PDF; a holdings file with a CUSIP missing from the data directory raises an error listing it and naming the pull command.
- 7.3 `pull_data.py --holdings <path> --benchmark <path>`: maps new CUSIPs and pulls their prices into `data/extra/` (gitignored).
- 7.4 Sample reports for each passing fund in `outputs/reports/{fund}.pdf`, committed. Review evidence: page renders of every page as PNGs in `review/section_7_pages/`.

### Section 8 — Write-up and reproducibility
- 8.1 `scripts/run_all.py`: regenerates every table, figure and report from `data/raw/` and `data/manual/`. Running it twice leaves `git status` clean.
- 8.2 `outputs/tables/answers.csv`: one or more rows per research question and fund, each with its source table and row.
- 8.3 `README.md`: what it is, the one-function interface with a copy-paste example, the answers from `answers.csv`, Tables 1 to 4 generated from the CSVs, the charts with one callout each placed in the prose before the chart, the 13F limits, and that the project 1 link was dropped and why. Test: README tables match the CSVs.
- 8.4 `docs/METHODS.md`: Sections 4 and 5 of this document with the corrections in Section 2.
- 8.5 Final fresh-clone run of `scripts/run_all.py` and the suite with sockets disabled; tidy (no stray files, no TODOs, no unused functions).

Writing rules for README, docs and report text: plain English, conversational but technical; numerals, not words, for numbers; no hyphens joining sentences; none of the words robust, resilient, rigorous, leveraging, grounded; no filler; the vehicle is called "the fund".

---

## 9. What session 0 must produce

This document is already committed as `instructions/00_kickoff.md`, and the source doc as `Project Outline/04_Attribution_Engine.docx`. If either is missing, stop and say so in the status file; do not recreate them.

Write these files, commit as `step 0.0: plan and scaffolding`, then the status file, push, stop. No other files.

1. `WORKFLOW.md`: the workflow text the owner pasted into the session, verbatim.
2. `PLAN.md`: Sections 1 to 8 from Section 8 above. For each step, one paragraph stating what is built, the file it lives in, the signatures from Section 6 it implements, the tests that prove it (file and test name), the output files it writes, and the review evidence to attach. Expand, do not summarise, and add or remove no step. Anything this document leaves unspecified is marked OPEN in `PLAN.md` and listed in `decisions/OPEN.md` and the status file, not decided.
3. `CLAUDE.md`: Sections 0, 4 and 6 of this document verbatim, then an empty `## Amendments` heading.
4. `config.toml`: Section 7 exactly.
5. `review/TEMPLATE.md`, headings in this order: Section; Steps completed (one line each with commit hash); Evidence (one subsection per numeric claim, each with raw rows via `to_string()`); Tests run (exact command and full output); Fresh-clone check (full output); Runtime per step; Deviations from PLAN.md; Not verified; Open questions; Files changed; Reviewer reads (ordered, shortest sufficient set).
6. `decisions/OPEN.md` (empty), and `decisions/funds_and_benchmarks.md`, `decisions/data_sources.md`, `decisions/sectors_ff12.md`, `decisions/pricing_rules.md`, `decisions/dependencies.md`, each restating the decision in 5 lines or fewer.
7. `docs/CONVENTIONS_RESOLVED.md`, numbered: 1 holdings dated by period date; 2 equity rows only; 3 CUSIP aggregation; 4 amendment rule; 5 weights sum to 1 including Unmapped and Unpriced; 6 the 14 buckets; 7 adjusted close and ticker normalisation; 8 position return and delisting rule; 9 neutral return for Unmapped and Unpriced; 10 sector return; 11 empty-bucket rules; 12 monthly book returns; 13 calendar-month periods; 14 NAV return on the institutional class; 15 French percent to decimal and RF; 16 annualisation factors; 17 issuer-level active share; 18 risk weights renormalised; 19 failed-gate handling; 20 13F units switch on filing date 2023-01-03; 21 Carino and Menchero zero limits; 22 project 3 functions and the pinned commit; 23 reportlab with invariant output.
8. `pyproject.toml`: package `attrib`, Python ≥ 3.11; runtime numpy, pandas, scipy, statsmodels, lxml, requests, yfinance, matplotlib, reportlab, pyarrow, and `pc @ git+https://github.com/uty101/Constrained-Portfolio-Optimiser@88e865d8202023cd495dd9866c49e6adbc9f4654`; dev extra pytest, pytest-socket, pypdf (for the page count test).
9. `requirements-lock.txt` produced by `uv pip compile pyproject.toml --extra dev`, committed.
10. `.gitattributes`: `* text=auto eol=lf`, `*.png binary`, `*.pdf binary`, `*.parquet binary`, `*.docx binary`, `data/raw/** -text`, `tests/fixtures/** -text`.
11. `.gitignore`: `data/processed/**`, `data/extra/**`, `.env`, `__pycache__/`, `*.py[cod]`, `.venv/`, `venv/`, `.pytest_cache/`, `*.egg-info/`, `.DS_Store`, `Thumbs.db`, `~$*`, `.vscode/`. `data/raw/` is not ignored.
12. `README.md` with a 5-line description and "results pending"; `attrib/__init__.py`; `tests/test_placeholder.py` that passes; `data/manual/overrides.csv` with the header only; `.gitkeep` in `data/raw`, `data/processed`, `outputs/tables`, `outputs/figures`, `outputs/reports`, `review`, `tests/fixtures`.
13. `instructions/00_kickoff.status.md` per rule 11, including the output of the placeholder test run.

Do not pull data. Do not install packages beyond what is needed to build the lock file and run the placeholder test.
