# Methods

This file states every rule the pipeline runs today, in the order of Sections 4 and 5 of `instructions/00_kickoff.md`. A later instruction file beats the `CLAUDE.md` amendments and `PLAN.md`, which beat the kickoff. An item with no citation is as the kickoff wrote it. An item that a later file set or changed cites that file. Where the code fixes a detail no instruction names, the item cites the review deviation the reviewer accepted.

Throughout, `h` is a holdings date, `t` a return quarter, P the fund side and B the benchmark side. Returns are decimals unless a label says percent.

## 3. Sample and data

### 3.1 Entities

| id | type | 13F filer CIK | NAV class | NAV source | benchmark |
|---|---|---|---|---|---|
| akre | fund | 1112520 | AKRIX (Institutional Class, `C000080287`, series `S000026760`) | `nport`, with ETF successor `AKRE` | ivv |
| jensen | fund | 1106129 | JENIX | `yfinance` | ivv |
| polen | fund | 1034524 | POLIX | `yfinance` | iwf |
| ivv | benchmark | n/a | IVV (ETF) | ETF adjusted close | n/a |
| iwf | benchmark | n/a | IWF (ETF) | ETF adjusted close | n/a |

`nav_source` and `etf_successor` are config keys (`instructions/02b_section_2_completion.md`, step 2.1b). `nav_ticker = "AKRIX"` stays as the class identity even though Yahoo no longer carries it.

- Each benchmark's N-PORT series is resolved from its ticker through `company_tickers_mf.json` and written to `data/raw/sec/series_resolved.csv` (entity, ticker, cik, series_id, class_id) (`instructions/01_section_1.md`, D 1.5).
- Each fund's series and NAV class are resolved the same way by `--stage navret` and written to `data/raw/edgar/nport_returns/series_resolved.csv` (`instructions/02b_section_2_completion.md`, step 2.1b; `instructions/02c_section_2_completion.md`, Section B).
- A 13F belongs to the manager, not to the fund. Polen's 13F carries over 200 names, ETFs among them (IWF itself, plus VONG, SPY, VOO, VUG, IWM or IVV at some dates). They stay in the book as priced, mapped equity rows (`instructions/07_section_7.md`, Section A, answer 3). Jensen's 13F holds its own ETF, JGRW, which has no CIK and so sits in Other.

### 3.2 Sources

| need | source | committed as |
|---|---|---|
| 13F filing list | submissions JSON `https://data.sec.gov/submissions/CIK{cik:010d}.json` plus every `filings.files` page; forms `13F-HR` and `13F-HR/A` only; `period_date` = `reportDate`, `filing_date` = `filingDate`; `amendment_type` from the `amendmentType` element of the filing's `primary_doc.xml`, blank for originals (`instructions/01_section_1.md`, D 1.3) | `data/raw/edgar/13f/filings_{id}.csv` |
| 13F information table | the 1 XML file in the filing's `index.json` other than `primary_doc.xml`; 0 or more than 1 such file raises. Pulled for every filing with `period_date` in H plus every `/A` for those periods (`instructions/01_section_1.md`, D 1.3 and D 1.5) | `data/raw/edgar/13f/{id}/{period}_{accession}.xml` |
| N-PORT filing list | the series atom feed, paged with `&start=` in steps of 100 until a page is empty; forms `NPORT-P` and `NPORT-P/A`, filed 2019-04-01 to 2026-09-30 (`instructions/01_section_1.md`, D 1.4 and D 1.5; `instructions/01b_section_1_completion.md`, Section B) | `data/raw/edgar/nport/filings_{id}.csv` |
| N-PORT holdings | `primary_doc.xml` of each filing, parsed (5.1). The XML is not committed; its sha256 is in `MANIFEST.json` under `uncommitted_sha256` | `data/raw/edgar/nport/holdings_{id}.csv` |
| Fund monthly NAV returns | Form N-PORT Part B Item B.5 `monthlyTotReturns` of each fund's series, every `NPORT-P` and `NPORT-P/A` filed 2019-11-01 to 2026-12-31 (`instructions/02b_section_2_completion.md`, step 2.1b) | `data/raw/edgar/nport_returns/{fund}_monthly.csv` |
| tickers | `company_tickers.json` and `company_tickers_mf.json`, as downloaded | `data/raw/sec/` |
| SIC | submissions JSON `name`, `sic` and `sicDescription` for every CIK reachable by ticker → CIK or by a `cik` override | `data/raw/sec/sic.csv` (cik, name, sic, sic_description) |
| sec_id → ticker, pass 1 | OpenFIGI `https://api.openfigi.com/v3/mapping` (5.2) | `data/raw/openfigi/mapping.csv` |
| sec_id → ticker, passes 2 to 4 | OpenFIGI and `yfinance.Search` (5.2) (`instructions/02b_section_2_completion.md`, step 2.1c) | `data/raw/openfigi/fallback.csv` |
| reviewer overrides | hand-written rows (5.2) (`instructions/03_section_3.md`, Section B) | `data/manual/overrides.csv` |
| stock prices | yfinance `download` with `auto_adjust=True`, `actions=False`, `threads=False`, `progress=False`, daily, 2015-12-01 to 2026-09-30 (`end="2026-10-01"`), in batches of 50 tickers in sorted order. A batch that raises is retried once, then the pull stops. A ticker that returns no rows is listed in `missing.csv` (yf_ticker, sec_ids) (`instructions/02_section_2.md`, Section B) | `data/raw/prices/adjclose.parquet`, `data/raw/prices/missing.csv` |
| NAV and ETF prices | the same call for JENIX, POLIX, IVV, IWF and AKRE. AKRIX is not requested (`instructions/02b_section_2_completion.md`, step 2.3b) | `data/raw/prices/nav_adjclose.csv` (date, JENIX, POLIX, IVV, IWF, AKRE) |
| factors | Ken French `F-F_Research_Data_5_Factors_2x3_CSV.zip` and `F-F_Momentum_Factor_CSV.zip`, monthly block only, kept as filed | `data/raw/french/ff5_monthly.csv`, `data/raw/french/mom_monthly.csv` |
| FF12 map | Ken French `Siccodes12.zip` | `data/raw/french/Siccodes12.txt` |

The price panel has index `date` (sorted, unique), 1 float64 column per `yf_ticker` in sorted order, written with pyarrow. Its dates are the union of every ticker's trading dates, with no forward fill (`instructions/02_section_2.md`, Section B). Tickers added after the first pull are merged in as new columns, and existing columns are never re-pulled, because a re-pull would restate adjusted closes as of a new date (`instructions/03_section_3.md`, step 3.0).

### 3.3 Sample

- **Holdings dates H.** The 28 calendar quarter ends from 2019-09-30 to 2026-06-30. iShares Trust filed no public NPORT-P before November 2019, so the benchmarks have no book before 2019-09-30 (`instructions/01b_section_1_completion.md`, Section B; amendment 7).
- Every entity must have a book at every date in H, else the run stops and lists the gaps. An N-PORT filing whose reporting period is not a date in H is ignored; a date in H with no N-PORT filing stops the run.
- **Quarter end trading day.** q(h) is the last date on or before h in the IVV price index (the IVV column of `nav_adjclose.csv`). `attribute()` takes q(h) from its own price panel's index, since a user's data directory need not hold IVV; on the committed data the 2 indexes are equal (`review/section_7.md`, Deviation 5, accepted in `instructions/08_section_8.md`, Section A, answer 6).
- **Return quarters.** QUARTERS has 28 rows, `t` from 1 to 28. Quarter t runs from `q_start = q(h_t)` to `q_end = q(next calendar quarter end)`, so the last runs from q(2026-06-30) to q(2026-09-30) (`instructions/02_section_2.md`, C 2.4; `instructions/01_section_1.md`, Section B, D-14).
- **Monthly series.** Book and NAV returns are calendar months from October 2019 to September 2026, 84 months. Factor regressions run from October 2019 to the earlier of September 2026 and the last month in the French files. That is August 2026 today, so 83 months (`instructions/05_section_5.md`, Section C).
- Holdings are dated by period date, not filing date. That is correct for ex-post attribution and is not look-ahead.

## 4. Conventions

**4.1 Holdings date.** A 13F or N-PORT book is the book at its period date. The filing lag is reported only as a data fact: `lag_days` in `coverage.csv` is the filing date of the filing the book starts from minus the period date (`review/section_1.md`, Deviations, accepted in `instructions/01b_section_1_completion.md`, Section B).

**4.2 Equity rows only.** 13F: keep rows with `sshPrnamtType` = SH and no `putCall`. N-PORT: keep `invstOrSec` rows with `assetCat` = EC and `units` = NS. Everything else is dropped. The parser keeps every row and the filter runs only when books are resolved (`instructions/01_section_1.md`, D 1.3). `dropped_value_usd` in `coverage.csv` is the value of all information-table rows before filtering minus the value of the book (`instructions/01_section_1.md`, Section B, D-09).

**4.3 Security identifier and aggregation.** Every book row carries a `sec_id`:
- the CUSIP, upper-cased and trimmed, when it is 9 alphanumeric characters;
- else the ISIN, when it is a valid ISO 6166 ISIN (2 letters, 9 alphanumeric characters, a Luhn check digit) (`instructions/02_section_2.md`, Section A, answer 1);
- else the row is dropped and its value counted in `dropped_value_usd`.

13F rows have `isin` blank and `sec_id` = `cusip`. Rows with the same `sec_id` in 1 book are summed (value and shares). In HOLDINGS, `cusip` is blank where it is not a valid CUSIP, so an N-PORT row filed with `N/A` or no `cusip` element becomes an ISIN-only row. These are mostly the non-US-domiciled members of the S&P 500 and Russell 1000 Growth, such as Accenture, Linde and Medtronic. `coverage.csv` reports their weight as `isin_only_weight` (`instructions/01b_section_1_completion.md`, step 1.4b; amendment 8).

HOLDINGS, the canonical book schema and the input schema of `attribute()`: entity, period_date, cusip, isin, sec_id, name, value_usd, shares.

**4.4 Amendments.** For each 13F period: start from the latest original 13F-HR; if a 13F-HR/A with `amendmentType` RESTATEMENT exists, the latest of them replaces the book entirely; each 13F-HR/A with `amendmentType` NEW HOLDINGS filed after the book in use is appended. For N-PORT, `NPORT-P` and `NPORT-P/A` are both read, and for each period the latest filing by filing date wins, original or amendment (`instructions/01b_section_1_completion.md`, Section B; amendment 9). `amendments_used` in `coverage.csv` holds the semicolon-joined accessions of the 13F-HR/A filings applied, or for N-PORT the accession of the filing used (`instructions/01_section_1.md`, Section B, D-08).

**4.5 Weights.** w_i = value_i / Σ value over all kept equity rows in that book, by `sec_id`, including rows that later land in Unmapped or Unpriced. Weights in every book sum to 1 (`instructions/02_section_2.md`, C 2.5).

**4.6 Buckets.** 14 buckets: the 12 FF12 industries in French's order (NoDur, Durbl, Manuf, Enrgy, Chems, BusEq, Telcm, Utils, Shops, Hlth, Money, Other), then Unmapped, then Unpriced.
- **Unmapped:** `map_status` = `no_match`, so no ticker from any pass or override.
- **Unpriced:** a ticker, but no adjusted close on the exact `q_start` date of the book's return quarter (`instructions/02_section_2.md`, Section B).
- A priced ticker with no CIK (`no_cik`) or a CIK with no SIC (`no_sic`) goes to Other, and its weight is reported as `other_nosic_weight` in `coverage.csv`. A SIC in no FF12 range goes to Other, as in French's own convention.
- `unpriced_weight` and `other_nosic_weight` may overlap, since a `no_cik` ticker can also lack a price. Each column answers its own question (`instructions/02b_section_2_completion.md`, Section B, OPEN-32).
- Sectors are FF12, built from SIC, applied identically to both sides. FF12 puts payment networks and ratings agencies (SIC 7389 and 7320: Mastercard, Visa, Moody's) in Other. ETFs held in a 13F book are mostly `no_cik` and so also land in Other (`instructions/02b_section_2_completion.md`, Section B).

**4.7 Prices.** Adjusted close only. `yf_ticker` = the ticker with `/` replaced by `-` (BRK/B → BRK-B). Because a position is priced only by a close on its exact `q_start`, a reused ticker whose price column starts after that date never prices it (`instructions/04_section_4.md`, Section A, answer 8). Delisted names that yfinance no longer carries land in Unpriced; that is a limit of free price data and is reported, not fixed (`instructions/04_section_4.md`, Section A, answer 7).

**4.8 Position return over a quarter.** r_i = P_i(end) / P_i(q_start) − 1, with P_i(end) the last close on or before `q_end`. If that close is before `q_end`, the position is held as cash at 0 return after it and `delisted_in_quarter` is true (`review/section_3.md`, Deviation 8, accepted in `instructions/04_section_4.md`, Section A, answer 4). No price on `q_start` sends the position to Unpriced. A `quarter_return` override (5.2) replaces r_i for the position it names.

**4.9 Book return.** The priced, mapped part of a book is held buy-and-hold through the quarter. Unmapped and Unpriced each earn that book's priced, mapped return, so the book return equals the priced, mapped return and r = Σ_s w_s r_s holds exactly over the 14 buckets. A `quarter_return` override recomputes the neutral return of the book it changes (`review/section_3.md`, Deviation 6, accepted in `instructions/04_section_4.md`, Section A, answer 4).

**4.10 Sector return.** r_s = Σ_{i∈s} w_i r_i / Σ_{i∈s} w_i for each bucket with positive weight. `buckets.csv` carries all 14 rows for every entity and quarter, with `r` blank where the weight is 0 (`review/section_3.md`, Deviation 7, accepted in `instructions/04_section_4.md`, Section A, answer 4).

**4.11 Empty buckets.** r_B = Σ_s w_s^B r_s^B over the buckets the benchmark holds. If the benchmark has 0 weight in a bucket, r_s^B := r_B. If the fund has 0 weight, r_s^P := r_s^B (after that fill), so selection is 0 there. If both are 0 the bucket contributes nothing. The rules are applied inside `brinson_fachler` to the blank `r` values of `buckets.csv` (`instructions/04_section_4.md`, Section B). `brinson_quarterly.csv` shows the filled `rP` and `rB`, with a boolean `filled` column after `rB` that is true where this rule supplied a value (`instructions/05_section_5.md`, Section A, answer 3).

**4.12 Monthly book returns.** Within each quarter the buy-and-hold value path is V_d = Σ_i w_i P_i(d) / P_i(q_start) over priced, mapped positions, divided by their weight sum, with P_i(d) the last close on or before d, so a delisted name is flat after its last close. The month-end dates are the last date of the price panel's index in each calendar month after `q_start`; the last of them must be `q_end`, else the run raises (`review/section_3.md`, Deviation 9, accepted in `instructions/04_section_4.md`, Section A, answer 4). The monthly return is the change in V between month-end dates, with `q_start` standing in for the first month's start. The 3 monthly returns of a quarter compound to its book return to 1e-12. Output: `outputs/tables/book_monthly.csv` (entity, month, ret), 84 months per entity (`instructions/03_section_3.md`, step 3.2).

**4.13 Monthly stock returns.** The month-end close is the last available adjusted close in each calendar month, per ticker; never `DateOffset` arithmetic. The first month of a ticker's series has no return, and neither has a month that follows a month with no close (`instructions/02_section_2.md`, C 2.4). Daily returns are simple returns, each from that ticker's previous available close, so a gap in a series does not erase the move across it (`review/section_2.md`, Deviations, accepted in `instructions/03_section_3.md`, Section A, point 4).

**4.14 NAV return.** Monthly NAV returns per fund are in `outputs/tables/nav_monthly.csv` (entity, month, ret, source), October 2019 to September 2026, with no row for a missing month (`instructions/02b_section_2_completion.md`, step 2.1b; `instructions/02c_section_2_completion.md`, Section C):
- **Jensen and Polen:** month-end adjusted close returns of JENIX and POLIX from yfinance, source `yfinance`.
- **Akre:** chosen month by month, first match wins:
  1. `nport_b5`: the B.5 monthly total return of AKRIX's class, net of fees, percent ÷ 100;
  2. the B.5 return of an ETF class in the same series, meaning a class whose symbol is `etf_successor`. AKRE is its own series, so this never fires;
  3. `yfinance_etf`: AKRE's month-end return from yfinance, for months that start after AKRE's first trading day (2025-10-27), so from November 2025 on;
  4. else missing.

  2025-08, 2025-09 and 2025-10 are missing, and that gap is accepted: Akre Focus Fund converted into the AKRE ETF in October 2025, its last NPORT-P covers July 2025, and Yahoo dropped the mutual fund's history (`instructions/02c_section_2_completion.md`, Section B, OPEN-33). `run_all.py` stops if any other Akre month is missing.
- **Benchmarks:** month-end returns of the IVV and IWF adjusted close.

A quarterly NAV return is the compound of the 3 calendar-month returns after h_t, and only when all 3 are present; otherwise it is blank. The same rule serves funds and benchmarks (amendment 11; `instructions/02c_section_2_completion.md`, Section B; `review/section_3.md`, Deviation 10, accepted in `instructions/04_section_4.md`, Section A, answer 4). On the benchmarks it differs from the direct ratio of adjusted closes at q(h_{t+1}) and q(h_t) by at most 4.9e-16. Akre's quarters t = 24 and t = 25 are blank.

**4.15 Factors and rf.** French data is in percent and is divided by 100. `load_french` returns columns mkt, smb, hml, rmw, cma, umd (French's `Mom`) and rf, indexed by calendar month, on the months both files share (`instructions/02_section_2.md`, C 2.3). Excess return = return − RF for the same calendar month.

**4.16 Annualisation.** Monthly volatility × √12. Monthly covariance × 12 for annual tracking error. Daily covariance × 21 for monthly. A quarterly standard deviation × 2 for the annual tracking error of the gap. A compounded return R over T quarters annualises as (1 + R)^(4/T) − 1 (`review/section_7.md`, Deviation 7, accepted in `instructions/08_section_8.md`, Section A, answer 6).

**4.17 Active share level.** Active share is computed by issuer, and the issuer is the SEC CIK from SECURITY_MAP. A row with no CIK is its own issuer, keyed by its `sec_id`. A CIK nets share classes (GOOG and GOOGL) and also nets an ISIN-only benchmark row against the fund's CUSIP row for the same company (`instructions/01b_section_1_completion.md`, Section B; amendment 10; `instructions/06_section_6.md`, Section C).

**4.18 Risk weights.** Risk uses the priced, mapped positions of each book. Weights of `sec_id`s that share a `yf_ticker` within a book are summed, then each side is renormalised to 1 (`instructions/06_section_6.md`, Section C). The excluded weight (Unmapped plus Unpriced) is reported next to every tracking-error figure as `excluded_weight_fund` and `excluded_weight_bench`.

**4.19 Failed gate.** A fund that fails the NAV gate (5.4) keeps its rows in `reconstruction.csv`, `gate.csv` and the gap row of `bootstrap.csv`, and its `factor_fit.csv` rows. It is left out of Tables 1 to 3, Charts 1 to 3, the exposures, the report and `answers.csv`, with a printed line saying why. All 3 funds pass, so nothing is excluded today (`review/section_5.md`, Deviation 14).

## 5. Methods

### 5.1 13F and N-PORT parsing (`attrib/edgar.py`)

- XML is parsed with lxml, namespace-agnostic (match on local names). Pre-2013 text filings are out of scope; they get a blank `infotable_name` and `amendment_type`, and none falls in H (`instructions/01b_section_1_completion.md`, Section B).
- 13F fields per row: nameOfIssuer, titleOfClass, cusip, value, sshPrnamt, sshPrnamtType, putCall (blank when absent). `value_raw` is the integer as filed; `shares` is `sshPrnamt` as a float (`instructions/01_section_1.md`, D 1.3).
- **Units.** `value_usd = value × 1000` if the filing date is before 2023-01-03, else `value_usd = value`.
- **Units check, 13F books.** Implied price p_i = value_usd / shares over kept rows with shares > 0. The median must lie in [1, 5000], else the run stops and prints the filing.
- **Check, N-PORT books.** The kept `pctVal` must sum to a value in [95, 101] in every period, else the run stops (`instructions/01_section_1.md`, D 1.6).
- N-PORT fields per row: name, title, cusip, isin, balance, units, valUSD, pctVal, assetCat, issuerCat, invCountry, and `other_id`, the `other` identifier whose `otherDesc` is "Inhouse Asset ID" (`instructions/02b_section_2_completion.md`, step 2.1c). A `cusip` that is absent or `000000000` is blank; `N/A` is kept as filed in the raw CSV and fails the CUSIP test in 4.3 (`instructions/02_section_2.md`, Section A, answer 2). The header gives `seriesId` and `repPdDate`.
- **B.5 monthly returns.** `parse_nport(xml)` returns `(header, HOLDINGS_RAW_NPORT, monthly returns)`. Each `monthlyTotReturn` element gives `classId` and `rtn1`, `rtn2`, `rtn3` in percent; `rtn3` is the month of `repPdDate`, `rtn2` the month before, `rtn1` the month before that. When 2 filings report the same class and month, the latest by filing date wins (`instructions/02b_section_2_completion.md`, step 2.1b).
- **Client.** `EdgarClient(user_agent, min_interval, retries, backoff, timeout, session=None)`. A `requests.Session` sends `User-Agent: $SEC_USER_AGENT` with every GET.
  - At most 5 requests a second: a request counts towards the 0.2 s minimum interval when it is sent.
  - Each GET has a 30 s timeout.
  - HTTP 429, HTTP 500 to 599, `requests.Timeout` and `requests.ConnectionError` are retried up to 3 times, with waits of 2, 4 and 8 s, then the call fails. Any other non-200 status raises at once with the status and URL.

  (`instructions/01_section_1.md`, D 1.2; `instructions/01b_section_1_completion.md`, Section B; amendment 5.)

### 5.2 Mapping (`attrib/mapping.py`)

The chain is sec_id → ticker (OpenFIGI, its fallbacks, then overrides) → CIK (`company_tickers.json`) → SIC (EDGAR submissions) → FF12 (`Siccodes12.txt`). Fund and benchmark rows are matched by `sec_id`. Where 1 company carries an ISIN in the benchmark and a CUSIP in the fund, the 2 keys meet at the ticker (risk and exposures) and at the CIK (active share) (`instructions/02_section_2.md`, Section A, answer 3).

**SECURITY_MAP** (`data/processed/security_map.csv`), 1 row per `sec_id`: sec_id, id_type (`cusip` or `isin`), ticker, yf_ticker, figi, figi_name, cik, sic, ff12, map_status, source (`instructions/02_section_2.md`, Section B). The universe is every distinct `sec_id` in the 140 books in H.

**Pass 1, OpenFIGI.** 1 job per `sec_id`: `{"idType": "ID_CUSIP" or "ID_ISIN", "idValue": sec_id, "exchCode": "US"}` (`exchCode` kept on ISIN jobs: `instructions/02b_section_2_completion.md`, Section B).
- Batches of 10 jobs every 2.4 s without a key, or 100 every 0.24 s with `OPENFIGI_API_KEY`. The key goes in the `X-OPENFIGI-APIKEY` header only when it is set.
- Timeout, retries and backoff as the EDGAR client. A non-200 after the last retry stops the pull.
- Every result is stored, ranked, in `mapping.csv` (sec_id, id_type, status, result_rank, figi, composite_figi, ticker, name, exch_code, market_sector, security_type).
- The mapping takes the first result whose `marketSector` is Equity. `figi` is its `compositeFIGI` when present, else its `figi` (`instructions/02_section_2.md`, Section B and C 2.1).

**Passes 2 to 4** (`--stage figi2`) run on every `sec_id` with no pass 1 equity result, in order, stopping at the first accepted result (`instructions/02b_section_2_completion.md`, step 2.1c):
- **Pass 2, ISIN crosswalk.** The candidate ISINs are (i) the ISIN of any IVV or IWF N-PORT row, in any period, whose `cusip` or `other_id` equals the `sec_id`; else (ii), for a CUSIP whose first character is a digit, the US ISIN `"US" + cusip + Luhn check digit`. An ISIN `sec_id` is its own candidate. Several candidates are queried in sorted order. Each query is OpenFIGI `ID_ISIN` with `exchCode: "US"`, accepting the first Equity result (`review/section_2.md`, Deviations, accepted in `instructions/03_section_3.md`, Section A, point 4).
- **Pass 3, no exchange filter.** OpenFIGI with the `sec_id`'s own type and no `exchCode`. Accept the first Equity result whose `exchCode` is in {US, UN, UW, UQ, UA, UR, UP, UF, UV, UD}.
- **Pass 4, Yahoo search.** `yfinance.Search(isin, max_results=8)` for each pass 2 candidate. Accept the first quote whose `quoteType` is EQUITY or ETF and whose `exchange` is in {NYQ, NMS, NGM, NCM, ASE, PCX, BTS}. The result name is `longname`, else `shortname`.
- **Name check, passes 2 to 4.** A name is normalised by upper-casing, replacing every non-alphanumeric character with a space, splitting, and dropping a leading `THE`. A result is accepted only if its first token equals the first token of the holding's name, taken from the book row with the largest weight. Rejections are logged with the reason. `fallback.csv` (sec_id, pass, query_type, query_value, rank, ticker, name, exch_code, market_sector, security_type, accepted, reject_reason) holds every result seen, accepted or not, and 1 row with a blank `rank` for a query with no result.
- A fallback mapping has a blank `figi`; `figi_name` is the result's name.

**Overrides** (`data/manual/overrides.csv`, columns kind, sec_id, period_date, value, source_note) (`instructions/02_section_2.md`, Section B; `instructions/03_section_3.md`, Section B):
- **`ticker`** replaces the ticker from any pass for that `sec_id`, in every period (`period_date` blank). Ticker precedence is: override, then pass 1, 2, 3, 4.
- **`cik`** sets the CIK. It applies only to a row that has a ticker (`instructions/02b_section_2_completion.md`, Section B), and it always beats the ticker → CIK lookup, because delisted tickers are reused by later companies. Every `cik` row is verified first: the first token of the CIK's submissions `name` (the `name` column of `sic.csv`) must equal the first token of `source_note`, under the pass 2 to 4 normalisation. A row that fails is not applied and is listed. The check is written to `data/raw/sec/cik_override_check.csv` (sec_id, cik, submissions_name, note_name, match).
- **`quarter_return`** sets r on the POSITION_RETURNS rows with that `sec_id` in the return quarter whose holdings date is `period_date`, in every entity. It is applied by `apply_return_overrides(pos, overrides)` after `book_quarter` and before `bucket_table` (`instructions/01_section_1.md`, Section B, D-16), and a `period_date` that is not a holdings date raises (`review/section_3.md`, Deviation 5, accepted in `instructions/04_section_4.md`, Section A, answer 4). An override that names an Unmapped or Unpriced row raises. The file holds no `quarter_return` rows: Yahoo's adjusted closes already absorb spin-offs such as United Technologies in April 2020 (`instructions/04_section_4.md`, Section A, point 3).
- The file holds 62 `ticker` rows and 29 `cik` rows. Old IAC (`44891N109`) and CBS (`124857202`) are left unmapped on purpose, because today's ticker for each is a different security (`instructions/03_section_3.md`, Section B).

**ticker → CIK.** Exact match on the `company_tickers.json` ticker after `-` and `/` are both normalised to `-`. A ticker that matches more than 1 CIK raises.

**CIK → SIC → FF12.** The SIC is the submissions `sic`. `parse_siccodes12` reads French's layout: an industry header line (number, short name, long name), then `NNNN-NNNN` range lines; industry 12 (Other) has no ranges. No SIC from 0100 to 9999 may fall in 2 ranges (`instructions/02_section_2.md`, C 2.2).

**`map_status`:** `no_match` (no ticker), `no_cik` (ticker, no CIK), `no_sic` (CIK, no SIC), else `mapped` (`instructions/01_section_1.md`, Section B, D-12). `ff12` is blank for `no_match` and Other for `no_cik` and `no_sic`.

**`source`:** `openfigi`, `figi_isin`, `figi_noexch` or `yahoo_isin` for the pass that gave the ticker (`openfigi` when none did), with `;override_ticker` and `;override_cik` appended when an override applied (`instructions/02b_section_2_completion.md`, step 2.1c).

### 5.3 Book returns (`attrib/returns.py`)

Conventions 4.5 to 4.14, for all 5 entities and 28 quarters. Outputs (`instructions/03_section_3.md`, step 3.2):
- `data/processed/position_returns.csv`, POSITION_RETURNS: entity, t, cusip, sec_id, issuer6, ticker, bucket, weight, r, delisted_in_quarter, last_price_date. `sec_id` sits after `cusip` because ISIN-only rows have a blank `cusip`; `issuer6` is unused for active share (`instructions/04_section_4.md`, Section A, answer 2).
- `outputs/tables/buckets.csv`, BUCKETS: entity, t, bucket, weight, r.
- `outputs/tables/book_quarterly.csv`: entity, t, book_return, unmapped_weight, unpriced_weight, delisted_weight.
- `outputs/tables/book_monthly.csv`: entity, month, ret.

Checks: Σ_s w_s r_s equals the book return to 1e-12 on every real book, and the 3 monthly returns compound to the quarterly return to 1e-12.

### 5.4 Reconstruction error and gates (`attrib/reconstruction.py`)

- **Gap.** gap_t = book return_t − NAV return_t, per entity and quarter, blank where the NAV return is blank (4.14). `outputs/tables/reconstruction.csv` (TABLE4: entity, t, q_start, q_end, book_return, nav_return, gap) holds all 5 entities, 140 rows (`review/section_3.md`, Deviation 11, accepted in `instructions/04_section_4.md`, Section A, answer 4).
- **Benchmark check.** For ivv and iwf, the gap against the ETF's own compounded monthly return. If any quarter's |gap| exceeds `gates.benchmark_gap_stop` (0.03), the run stops: a gap that size points at a parsing or mapping bug. Quarters whose |gap| exceeds `gates.benchmark_gap_max` (0.01) are listed with that book's unmapped, unpriced and delisted weights, and the run carries on. About 3% to 4% of IVV earns the neutral return, and buy-and-hold from a quarter-start book cannot follow index changes made inside the quarter, so a 1% gap in a violent quarter is possible without a bug (`instructions/03_section_3.md`, step 3.3; `instructions/04_section_4.md`, Section A, point 4).
- **Fund gate.** The Pearson correlation of quarterly book return with NAV return, per fund, over the quarters that have a NAV return. Pass if it is at least `gates.fund_nav_corr_min` (0.90). Blank quarters are left out of the correlation, the gap statistics and the gap bootstrap (amendment 11; `instructions/02c_section_2_completion.md`, Section B).
- **`gate.csv`:** fund, corr, pass, n_quarters (the quarters used: 26 for Akre, 28 for Jensen and Polen), mean_gap, std_gap, mean_abs_gap, te_gap_ann (`instructions/03_section_3.md`, step 3.4). `std_gap` uses ddof 1, since the gap is not a regression residual (`instructions/04_section_4.md`, Section A, answer 3; `instructions/06_section_6.md`, Section A, answer 3). `te_gap_ann` = 2 × `std_gap`.
- **Gap bootstrap.** A 90% stationary bootstrap interval for the mean gap (5.9), over the non-blank quarters concatenated in `t` order. For Akre the blocks therefore run across the gap at t = 24 and t = 25 (`review/section_3.md`, Deviation 13, accepted in `instructions/04_section_4.md`, Section A, answer 4).

### 5.5 Brinson-Fachler single period (`attrib/brinson.py`)

Over the 14 buckets s, with r_B the benchmark book return:

- Allocation_s = (w_s^P − w_s^B)(r_s^B − r_B)
- Selection_s = w_s^B (r_s^P − r_s^B)
- Interaction_s = (w_s^P − w_s^B)(r_s^P − r_s^B)
- Σ_s (Allocation_s + Selection_s + Interaction_s) = r_P − r_B, checked to 1e-10 on every real fund quarter.

Inputs are `buckets.csv` for the fund and its benchmark and `book_quarterly.csv` for r_P and r_B; nothing is recomputed from positions. Unmapped and Unpriced enter like any bucket, with their book's neutral return, which keeps the identity exact. Empty buckets follow 4.11 (`instructions/04_section_4.md`, Section B).

`outputs/tables/brinson_quarterly.csv`: fund, t, bucket, wP, wB, rP, rB, filled, allocation, selection, interaction, ordered by fund (config order), t, then bucket in 4.6 order (`instructions/04_section_4.md`, C 4.3; `instructions/05_section_5.md`, Section A, answer 3).

### 5.6 Multi-period linking (`attrib/linking.py`)

d_t = r_P,t − r_B,t. R_P = Π(1 + r_P,t) − 1, R_B likewise, D = R_P − R_B, T the number of quarters (28).

**Carino.** k_t = [ln(1 + r_P,t) − ln(1 + r_B,t)] / d_t, and k_t = 1/(1 + r_P,t) when |d_t| < 1e-12. k = [ln(1 + R_P) − ln(1 + R_B)] / D, and k = 1/(1 + R_P) when |D| < 1e-12. Linked effect = Σ_t (k_t / k) effect_t.

**Menchero.** M = (D / T) / [(1 + R_P)^(1/T) − (1 + R_B)^(1/T)], and M = (1 + R_P)^((T − 1)/T) when |D| < 1e-12. α_t = [(D − M Σ_t d_t) / Σ_t d_t²] × d_t, and α_t = 0 when Σ_t d_t² < 1e-24. Linked effect = Σ_t (M + α_t) effect_t.

The 1e-12 tolerance is `linking.zero_tol`; the 1e-24 limit is a module constant citing kickoff 5.6. Both linked sets sum to D, checked to 1e-12 on synthetic data and 1e-10 on real data. The Carino minus Menchero difference per bucket and effect is reported, not tested.

`outputs/tables/linked.csv` (Table 1): fund, method, bucket, allocation, selection, interaction, total. Per fund and method (`carino`, `menchero`), 14 bucket rows plus a `Total` row of column sums; `total` = allocation + selection + interaction (`instructions/04_section_4.md`, Section B). The report and the README show Carino only (`instructions/01_section_1.md`, Section B, D-27).

**Chart 1** (`outputs/figures/{fund}_alloc_vs_sel.png`). For each k from 1 to 28, quarters 1 to k are linked with Carino, so every point is a proper linked effect, not a running sum. 3 lines against `q_end` of quarter k, in percentage points, with a zero line:
- Total allocation;
- Total selection;
- the cumulative excess D_k = R_P,k − R_B,k, black and dashed, labelled "Total excess (D)".

Title "{Fund} vs {benchmark}: cumulative allocation and selection (Carino)"; subtitle "Interaction is excluded from the chart and shown in Table 1."; y label "Percentage points of cumulative return"; 8 × 4.5 inches (`instructions/04_section_4.md`, Section B; `instructions/05_section_5.md`, step 5.0). {Fund} is the capitalised fund id and {benchmark} the ETF ticker.

### 5.7 Returns-based factor attribution (`attrib/factors.py`)

- **Model.** r_t − RF_t = α + β_M MktRF_t + β_S SMB_t + β_V HML_t + β_R RMW_t + β_C CMA_t + β_U UMD_t + ε_t, OLS, on monthly data.
- **Series** (`instructions/01_section_1.md`, Section B, D-22): `{fund}_book` and `{fund}_nav` for the 3 funds, and `ivv_book` and `iwf_book` as a sanity check. Months with a missing return are dropped before the fit, so `akre_nav` uses 80 months and the others 83; `n_months` records the count (`instructions/05_section_5.md`, Section C).
- **Full sample.** Exactly `statsmodels.api.OLS(y, sm.add_constant(X)).fit(cov_type="HAC", cov_kwds={"maxlags": 3})`, every other argument at its default, factors in the order mkt, smb, hml, rmw, cma, umd (`instructions/05_section_5.md`, Section C). The constant is named `alpha` in every output.
- **Residual volatility.** `resid_vol_ann` is the regression standard error, √(Σ ε̂_t² / (n − 7)) × √12, with n the months used and 7 the parameters (6 factors and the constant) (`instructions/06_section_6.md`, Section A, answer 3; `docs/CONVENTIONS_RESOLVED.md`, item 24).
- **`outputs/tables/factor_fit.csv`:** series_id, series_kind (book, nav), coef, value, se_hac, t_hac, r2, resid_vol_ann, n_months.
- **Rolling betas.** Book series only (`instructions/01_section_1.md`, Section B, D-23). Plain OLS with a constant on every window of 36 consecutive calendar months with no missing month, dated by its last month (`YYYY-MM`). That gives 48 windows per series, 2022-09 to 2026-08 (`instructions/05_section_5.md`, Section C). Written to `outputs/tables/rolling_betas.csv` (series_id, month_end, mkt, smb, hml, rmw, cma, umd).
- **Table 2 by calendar year, full-sample betas.** Over the months the fit used: contribution_j,y = Σ_{t∈y} β̂_j f_j,t; alpha_y = α̂ × n_months in year y; residual_y = Σ_{t∈y} ε̂_t; plus the year's summed excess return and the full-sample R². Rolling 36-month betas feed Chart 2 only, since 6 betas cannot be estimated from 12 points. Years run from 2019 (3 months) to 2026 (8 months), and `n_months` follows `year` so partial years are visible. The 6 contributions, alpha and residual sum to the year's excess return to 1e-12. `outputs/tables/factor_by_year.csv` (series_id, year, n_months, excess_return, mkt, smb, hml, rmw, cma, umd, alpha, residual, r2_full) carries all 8 series; the report and README print the fund book rows (`instructions/05_section_5.md`, Section C; `instructions/06_section_6.md`, Section A, answer 4).
- **Chart 2** (`outputs/figures/{fund}_rolling_betas.png`). 6 lines of rolling book betas against window end, legend Mkt-RF, SMB, HML, RMW, CMA, UMD, with a zero line. Title "{Fund}: rolling 36-month factor betas (book)", y label "Beta", 8 × 4.5 inches (`instructions/05_section_5.md`, Section C).

### 5.8 Holdings-based exposures (`attrib/factors.py`)

Project 1's characteristic scores are not used; exposures come from each stock's own factor betas.

- **Stock universe at h.** Every priced, mapped ticker of every fund and benchmark in scope at h (`instructions/05_section_5.md`, Section C).
- **Stock betas.** OLS with a constant of the stock's monthly excess returns (4.13 and 4.15) on the 6 factors, over the 36 calendar months ending at h's month, if at least 24 months are present.
- **Fallback.** A stock with fewer than 24 months takes the mean beta of the stocks in its FF12 bucket on the same side (fund or benchmark) that have valid betas at h (`instructions/05_section_5.md`, Section C).
- **Exposure.** β_P,j = Σ_i w_i β_i,j over the priced, mapped positions of 1 side, summed by ticker, that have a beta (own or fallback), with their weights renormalised to 1. Same for the benchmark; active = fund − benchmark.
- **`outputs/tables/holdings_exposures.csv`:** fund, holdings_date, side (fund, benchmark, active), mkt, smb, hml, rmw, cma, umd, excluded_weight. `excluded_weight` is 1 minus the weight that entered the exposure (unmapped, unpriced, and any position with no beta), blank on active rows (`instructions/06_section_6.md`, Section A, answer 1).
- **Exposures chart** (`outputs/figures/{fund}_exposures_hb_vs_rb.png`). 2 × 3 panels, 1 per factor: the holdings-based fund exposure at each h as markers, and the rolling returns-based book beta whose window ends at h's month as a line where it exists (`instructions/05_section_5.md`, Section C).
- Both measures use the same trailing 36 months: the first regresses each stock, the second the weighted sum of those stocks. Their agreement is therefore a consistency check, not independent confirmation (`instructions/06_section_6.md`, Section A, point 3).

### 5.9 Bootstrap (`attrib/bootstrap.py`)

`pc.stats.stationary_bootstrap_indices(n, mean_block, reps, seed)` with mean_block = 4 quarters, reps = 10000 and seed `run.bootstrap_seed` (20261002), the same seed for every fund. `bootstrap_mean(x, mean_block, reps, seed, lo, hi, idx=None)` returns the sample mean of x and the 5th and 95th percentiles of the resampled means, taken with `numpy.quantile` (linear) (`instructions/01_section_1.md`, Section B, D-20; `review/section_3.md`, Deviation 13, accepted in `instructions/04_section_4.md`, Section A, answer 4).

- **Effects.** 1 call to `stationary_bootstrap_indices(n=28, ...)` per fund; the same draws resample that fund's quarterly total allocation, selection and interaction (each the sum over buckets for the quarter, unlinked) (`instructions/04_section_4.md`, Section B; `instructions/05_section_5.md`, Section A, answer 1).
- **Gap.** The fund's non-blank gap series (5.4).
- `outputs/tables/bootstrap.csv`: fund, series (allocation, selection, interaction, gap), mean, p05, p95, ordered by fund then series.
- No selection skill is claimed for a fund whose interval contains 0.

### 5.10 Active share and tracking error (`attrib/risk.py`)

- **Active share.** AS = ½ Σ_k |w_k^P − w_k^B| over the union of issuers k (4.17), on the 4.5 book weights of all positions, unmapped included, each unmapped row its own issuer. Unmapped names cannot match across books and so push AS up; `unmapped_weight_fund` and `unmapped_weight_bench` sit beside it (`instructions/06_section_6.md`, Section C).
- **Ticker set.** The union of both books' risk-weight tickers (4.18). `n_names` is its size, which is also the dimension of Σ (`instructions/07_section_7.md`, Section A, answer 1).
- **Window.** Daily simple returns (4.13) from `adjclose.parquet`, over the rows `pc.cov.window_daily(returns_d, q_start(h), 36)` returns, restricted to the ticker set.
- **Fill.** A missing daily return of ticker i is filled with the equal-weight mean that day of the other tickers in i's FF12 bucket (from SECURITY_MAP) that have a return that day; if there are none, the equal-weight mean of every ticker with a return that day. A ticker's fill share is its filled days over the window's rows, and `max_fill_share` is the largest at h. A day on which no ticker has a return stops the run.
- **Covariance.** Σ_d = `pc.cov.cov_lw_cc(X, ddof=0)`, whose shrinkage intensity is `delta_lw`. Then `pc.cov.condition_cov(Σ_d, max_cond)` with `max_cond` = 1e6; `ridged` is true when the ridge it adds is above 0. Then Σ_m = 21 Σ_d (`instructions/06_section_6.md`, Section C).
- **TE and its Euler split.** a = w^P − w^B on the ticker set.
  - TE = √(12 a′ Σ_m a)
  - MCTE_i = 12 (Σ_m a)_i / TE
  - CTE_i = a_i MCTE_i, in annualised TE units, so Σ_i CTE_i = TE, checked to 1e-12.
  - Sector CTE = Σ of CTE_i within each FF12 bucket; all 12 rows are written per fund and date, 0 where empty.
- **Constants.** 21 and 12 are literals in `attrib/risk.py` citing kickoff 5.10, because `active_cov` and `te_decomposition` have fixed signatures; `run_all.py` stops if `risk.daily_to_monthly` or `risk.months_per_year` differs from them.
- **Outputs** (`instructions/06_section_6.md`, Section C):
  - `outputs/tables/risk_quarterly.csv` (Table 3): fund, holdings_date, active_share, unmapped_weight_fund, unmapped_weight_bench, te_exante, excluded_weight_fund, excluded_weight_bench, n_names, max_fill_share, delta_lw, ridged.
  - `outputs/tables/cte_positions.csv`: fund, holdings_date, ticker, bucket, a, mcte, cte.
  - `outputs/tables/cte_sectors.csv`: fund, holdings_date, bucket, cte.
- **Realised TE.** The standard deviation (ddof 1) of the monthly book active return (fund book minus its benchmark's book) × √12, over all 84 book months, October 2019 to September 2026. Realised TE needs no factor data, so the French end date does not cut it (`instructions/07_section_7.md`, Section A, answer 2). `outputs/tables/te_realised.csv`: fund, te_realised, te_exante_mean (the mean of the 28 ex-ante TEs), n_months = 84 (`instructions/01_section_1.md`, Section B, D-25).
- **Chart 3** (`outputs/figures/{fund}_cte_top15.png`). Horizontal bars of the 15 positions with the largest |CTE| at h = 2026-06-30, labelled by ticker, in percentage points of annualised TE. Sorted by signed CTE, largest at the top, positive bars red and negative bars blue, with a vertical zero line. Title "{Fund} vs {benchmark}: top 15 contributions to ex-ante tracking error, 2026-06-30"; subtitle giving TE and the share of TE the 15 explain; 8 × 6 inches (`instructions/06_section_6.md`, Section C).

### 5.11 Report (`attrib/report.py`) and the entry point

The layout is that of `instructions/07_section_7.md`, Section C.1, which supersedes the kickoff's outline. reportlab, A4 portrait, 2 cm margins, Helvetica 9 pt body and 8 pt tables, `invariant=1`, each page started fresh. Numbers are percent with 2 decimals unless stated; correlation, HAC t and R² are plain numbers with 2 decimals. Charts are 17 cm wide, matplotlib PNGs at 150 dpi saved with `metadata={"Software": None}` and embedded from memory; the report embeds the same PNG bytes as `outputs/figures/` (`instructions/07_section_7.md`, Section C.2). Figures shown in a table or chart are not restated in prose on the page.

**Page 1.**
- Title "{Fund} vs {benchmark}: performance and risk attribution".
- The window: holdings 2019-09-30 to 2026-06-30, returns 2019-09-30 to 2026-09-30.
- The annualised book returns of the fund and the benchmark (4.16) and the cumulative D.
- A data line: the mean unmapped and mean unpriced weight of the fund book over the 28 quarters, from `book_quarterly.csv`.
- Table 1: the Carino rows of `linked.csv`, 14 buckets plus Total, columns allocation, selection, interaction and total, in percentage points.
- The bootstrap 90% intervals of mean quarterly allocation and selection.
- Chart 1.

**Page 2.**
- Table 2: the fund's book rows of `factor_by_year.csv`, columns year, n_months, excess return, the 6 factors, alpha and residual.
- The full-sample alpha a month, its HAC t and R².
- Chart 2.
- **Short-window rule.** When the fund book has fewer than `report.min_factor_months` (24) monthly returns inside the factor window (3.3: from the month after the first holdings date to the earlier of the last return month and the last French month), page 2 shows only the line "Fewer than 24 monthly returns, so the factor fit is skipped.", with no Table 2 and no Chart 2, and the factor fit is not run (`instructions/08_section_8.md`, Section A, answer 2).

**Page 3.**
- Table 3: the rows of `risk_quarterly.csv` at each 31 December from 2019 to 2025 and at 2026-06-30 (8 rows), columns date, active share, ex-ante TE, n_names and ridged.
- Realised TE (84 months) and the mean ex-ante TE.
- Chart 3.

**Page 4.**
- Table 4: the fund's `gate.csv` row (correlation, n_quarters, mean gap, std of gap, TE of the gap) and the gap bootstrap interval.
- The 13F limits paragraph, verbatim from `instructions/07_section_7.md`, Section C.1.
- With no NAV series (a user's report), the line "No NAV series was supplied, so the reconstruction check is skipped." replaces Table 4 (`instructions/01_section_1.md`, Section B, D-28; `instructions/07_section_7.md`, Section C.3).

**Mechanics.** `build_report(fund_id, results, out_path)` renders what it is given and filters nothing. `results` maps the table stems `linked`, `factor_by_year`, `factor_fit`, `risk_quarterly`, `te_realised`, `gate`, `bootstrap`, `book_quarterly` and `coverage`, already cut to the fund, plus `fund_name`, `benchmark_name`, `chart1` to `chart3` and `min_factor_months` (`instructions/07_section_7.md`, Section C.2). Each of the 3 sample reports in `outputs/reports/{fund}.pdf` has exactly 4 pages; a user's report has at most 4.

**Entry point.** `attribute(holdings_path, benchmark_path, start, end, data_dir="data", out_dir="outputs/reports", fund_name=None) -> Path` reads local data only (`instructions/07_section_7.md`, Section C.3):
- Both inputs are HOLDINGS CSVs. `entity`, `isin` and `sec_id` may be absent. A non-blank `sec_id` is used as given; a blank or absent `sec_id` follows 4.3.
- `start` and `end` are holdings dates, and every calendar quarter end between them must be in both files, else it raises and lists the missing dates.
- It reads `data_dir/raw` and `data_dir/manual`, then merges `data_dir/extra/security_map_extra.csv` and `data_dir/extra/adjclose_extra.parquet` when present; the extra rows win on a duplicate `sec_id` or ticker.
- Any `sec_id` absent from the merged map raises an error listing every such `sec_id` and naming `python scripts/pull_data.py --holdings <path> --benchmark <path>`.
- It runs Sections 3 to 6 for the pair, with no NAV, so no gate and nothing excluded. It writes `{out_dir}/{fund_name or holdings file stem}.pdf` and returns the path.

**Pulling for new holdings.** `scripts/pull_data.py --holdings <path> --benchmark <path>` maps every `sec_id` of the 2 files that is not in the data directory: OpenFIGI pass 1, ticker → CIK on the committed `company_tickers.json`, CIK → SIC from EDGAR for CIKs `sic.csv` lacks, then `build_security_map`. It writes `data/extra/security_map_extra.csv`, and pulls prices for every needed `yf_ticker` with no price column into `data/extra/adjclose_extra.parquet` (`instructions/07_section_7.md`, Section C.3). Tickers already listed in `data/raw/prices/missing.csv` are skipped by default; `--retry-missing` asks for them again (`instructions/08_section_8.md`, Section A, answer 4). `data/extra/` is gitignored, and `data/raw/` is not touched.

**`answers.csv`.** Rows for every fund that passed the gate, figure by figure in the order of `instructions/08_section_8.md`, Section C. Values are decimals, each traced to a source table and row. The alpha interval is alpha ± 1.645 × HAC se; the effect and gap intervals are the bootstrap p05 and p95. After those come 7 rows for Akre only (`instructions/09_closeout.md`, Section B): the Carino BusEq selection and interaction (`linked`), the min and max of the Other bucket weight over the 28 quarters (`buckets`), FICO's weight at 2026-06-30 (POSITION_RETURNS), FICO's 2026-09 return from month-end adjusted closes (`adjclose.parquet`), and the book's 2026-09 monthly return minus IVV's (`book_monthly`).

## Configuration

Every parameter lives in `config.toml` and is loaded by `attrib/config.py` into frozen dataclasses. No numeric parameter is hard-coded in `attrib/` except constants written inside a formula, which cite their section.

| table | keys |
|---|---|
| `[run]` | `bootstrap_seed = 20261002` |
| `[sample]` | `first_holdings_date = "2019-09-30"`, `last_holdings_date = "2026-06-30"`, `last_return_date = "2026-09-30"`, `price_start = "2015-12-01"`, `price_end_exclusive = "2026-10-01"` |
| `[entities.*]` | `type`; funds: `cik`, `nav_ticker`, `benchmark`, `nav_source`, and for Akre `etf_successor`; benchmarks: `etf_ticker` |
| `[edgar]` | `min_interval_s = 0.2`, `retries = 3`, `backoff_s = [2, 4, 8]`, `units_switch_date = "2023-01-03"`, `implied_price_lo = 1.0`, `implied_price_hi = 5000.0`, `timeout_s = 30` |
| `[openfigi]` | `batch_no_key = 10`, `batch_with_key = 100`, `min_interval_no_key_s = 2.4`, `min_interval_with_key_s = 0.24` |
| `[gates]` | `fund_nav_corr_min = 0.90`, `benchmark_gap_max = 0.01`, `benchmark_gap_stop = 0.03` |
| `[linking]` | `zero_tol = 1e-12` |
| `[factors]` | `names = ["mkt", "smb", "hml", "rmw", "cma", "umd"]`, `hac_maxlags = 3`, `rolling_window = 36`, `stock_beta_window = 36`, `stock_beta_min_obs = 24` |
| `[risk]` | `cov_months = 36`, `daily_to_monthly = 21`, `months_per_year = 12`, `max_cond = 1e6`, `top_n_positions = 15` |
| `[bootstrap]` | `mean_block = 4`, `reps = 10000`, `lo = 0.05`, `hi = 0.95` |
| `[report]` | `dpi = 150`, `max_pages = 4`, `min_factor_months = 24` |

`timeout_s` is from `instructions/01b_section_1_completion.md`, step 1.2b; `nav_source` and `etf_successor` from `instructions/02b_section_2_completion.md`, step 2.1b; `benchmark_gap_stop` from `instructions/03_section_3.md`, step 3.3; `min_factor_months` from `instructions/08_section_8.md`, Section A, answer 2.

**Secrets.** `SEC_USER_AGENT` (format `Utkarsh Malhotra <email>`) and the optional `OPENFIGI_API_KEY` are read from the environment only. Only `scripts/pull_data.py` touches the network.

**Output format and determinism.** Every CSV is written with `float_format="%.17g"`, LF line endings, UTF-8 and no index column (amendment 6; `instructions/01b_section_1_completion.md`, Section B). Every random draw uses the config seed. On 1 platform, 2 runs give byte-identical CSVs, PNGs and PDFs. Across platforms, numeric outputs agree to 1e-10 relative: `%.17g` prints every bit, so BLAS and libm last-bit differences show, and font rasterisation changes PNG and PDF bytes (`docs/CONVENTIONS_RESOLVED.md`, item 25; `instructions/07_section_7.md`, Section A, point 4).

**Dependencies.** Python 3.12. `pc.cov.cov_lw_cc`, `pc.cov.condition_cov`, `pc.cov.window_daily` and `pc.stats.stationary_bootstrap_indices` come from project 3, a git dependency pinned to commit `88e865d8202023cd495dd9866c49e6adbc9f4654`; `pc.cov.estimate_cov` is not used (amendment 1).
