# instructions/02_section_2.md — Session 2: Section 2, Mapping, sectors, prices and factors

Pull `main` first. This file is the session prompt for Section 2. Precedence (rule 13): this file beats `CLAUDE.md` amendments and `PLAN.md`, which beat the kickoff. Where `PLAN.md` says 30 dates or quarters, read 28 (amendment 7).

---

## A. Section 1: approved

What the reviewer checked independently, on Linux with Python 3.12, from a fresh clone of `770d9e9`:

1. Lock install, `pytest -p socket --disable-socket -q`: 26 passed.
2. `python scripts/run_all.py --section 1`: all checks pass, exit 0, and `git status` is clean afterwards. The outputs regenerate byte-identically on Linux.
3. **13F totals, exact.** The reviewer summed the `value` elements of the raw XML with its own code for every original 13F-HR book in H that uses no amendment, applying the units switch. All 79 match `total_value_usd` in `coverage.csv` to the dollar, so the `%.17g` fix works.
4. **ISIN-only rows.** `coverage.csv` has 140 rows. `isin_only_weight` runs from 2.68% to 3.99% for IVV and from 0 to 2.19% for IWF, and is 0 for every 13F book. The IVV 2023-06-30 book has 503 rows, 25 of them ISIN-only, with 3.16% of its value.

Answers to the session 1b questions:

1. **ISIN validity.** ISO 6166 with the Luhn check digit is the right reading. Accepted.
2. **`N/A` and missing `cusip` elements.** Covered by "valid CUSIP, else valid ISIN". Accepted, with the raw CSVs keeping `N/A` as filed.
3. **One issuer, two keys.** **(a).** SECURITY_MAP is keyed by `sec_id`. OpenFIGI is queried with `ID_CUSIP` for CUSIP `sec_id`s and `ID_ISIN` for ISIN `sec_id`s. Option (b) relies on an iShares-internal field that is not a filing standard. The 2 keys of 1 issuer (IVV's ISIN and the funds' CUSIP for Accenture) meet at the ticker and the CIK, which is all Sections 3 to 6 need.
4. **IVV's `NPORT-P/A` for 2025-09-30.** Noted. It carries the same values as the original.
5. **Fresh clone of local `main`.** Accepted. From this section on, push the step commits first, then run the fresh-clone check against GitHub, then commit and push the review and status files. That is 2 pushes, matching `WORKFLOW.md` Part 2 step 5.

---

## B. Decisions for Section 2

| item | decision | reason |
|---|---|---|
| SECURITY_MAP key | `sec_id`. Schema: sec_id, id_type (`cusip` or `isin`), ticker, yf_ticker, figi, figi_name, cik, sic, ff12, map_status, source. Supersedes kickoff 6.2. `build_security_map` keeps its signature. | Answer 3 |
| OpenFIGI universe | Every distinct `sec_id` in any of the 140 books in H. Nothing outside H. | The 2019-03-31 and 2019-06-30 13F books are unused |
| OpenFIGI HTTP | `requests.Session`, `timeout = edgar.timeout_s`, retries and backoff from `[edgar]`, rate from `[openfigi]`. API key header `X-OPENFIGI-APIKEY` only when `OPENFIGI_API_KEY` is set. A non-200 after the last retry stops under rule 4. | Same failure rules as EDGAR |
| OpenFIGI selection | Within a job's results, the first with `marketSector` = `Equity`. `figi` is that result's `compositeFIGI` when present, else `figi`. | Composite FIGI is the US-level line, stable across venues |
| Overrides file | Columns become: kind, sec_id, period_date, value, source_note. `kind` ∈ {`ticker`, `cik`, `quarter_return`}. `ticker` replaces the OpenFIGI ticker. `cik` sets the CIK when ticker → CIK fails. `quarter_return` is for Section 3. Header only for now. | Delisted names lose their CIK in today's `company_tickers.json`, so the reviewer needs a way to set it |
| `map_status` | `mapped`, `no_match` (no OpenFIGI equity result), `no_cik` (ticker but no CIK), `no_sic` (CIK but no SIC). | D-12, unchanged |
| `source` column | `openfigi`, `override_ticker`, `override_cik`, or both override values joined with `;` | Each row's provenance visible |
| Price pull | yfinance `download`, batches of 50 tickers in sorted order, `auto_adjust=True`, `actions=False`, `threads=False`, `progress=False`. A ticker that returns no rows is listed in `data/raw/prices/missing.csv` (yf_ticker, sec_ids). A batch that raises is retried once, then stops under rule 4. | Deterministic order; missing names visible rather than silently absent |
| Price panel format | `adjclose.parquet`: index `date` (datetime64, sorted, unique), columns `yf_ticker` sorted, float64, written with pyarrow, `index=True`. Dates are the union of all tickers' trading dates; no forward fill. | One panel; gaps stay gaps |
| Unpriced | Ticker mapped but no adjusted close on the exact `q_start` date of the book's return quarter. | Convention 4.8 |
| No-CIK review list | New file `outputs/tables/nocik_top.csv`, the 40 largest `no_cik` sec_ids by maximum weight across books. | Feeds the `cik` overrides in instruction 03 |

---

## C. Amendments to Section 2 steps

### 2.1 SEC and OpenFIGI pulls
- `--stage figi` before `--stage sec`, as `PLAN.md` says.
- `data/raw/openfigi/mapping.csv`, columns: sec_id, id_type, status, result_rank, figi, composite_figi, ticker, name, exch_code, market_sector, security_type. Status `ok` or the API's `warning` / `error` text. One row per result; jobs with no result get 1 row with `result_rank` blank.
- `--stage sec`: `company_tickers.json` as downloaded. `sic.csv` covers every CIK reachable by ticker → CIK.
- Review evidence: per entity, the count of `sec_id`s mapped and `no_match`, split by `id_type`; the count of CIKs with and without SIC.

### 2.2 Mapping module
- D-11 A stands: `--stage french` runs here, and its 3 files are committed in this step.
- `parse_siccodes12` reads French's layout: an industry header line (`number`, short name, long name), then lines of `NNNN-NNNN` ranges. Industry 12 (Other) has no ranges.
- `test_ff12_ranges_land_in_one_industry`: no SIC from 0100 to 9999 falls in 2 ranges. If the file has overlapping ranges, stop under rule 4 and print them; do not choose.
- New test `test_isin_sec_id_maps`: a synthetic OpenFIGI frame with an ISIN `sec_id` gives the same ticker, CIK and FF12 as a CUSIP `sec_id` for the same company.
- New test `test_cik_override`: an override row of kind `cik` sets `cik`, then `sic` and `ff12` from `sic.csv`, and `map_status` becomes `mapped`.
- `build_security_map` writes `data/processed/security_map.csv` when run by `run_all.py --section 2`.

### 2.3 Prices and French data
- French loaders. In `ff5_monthly.csv` and `mom_monthly.csv`, columns are kept as French names them. `load_french(data_dir)` returns a frame indexed by `pd.Period(freq="M")` with columns `mkt, smb, hml, rmw, cma, umd, rf`, all ÷ 100, on the months both files share. The momentum column is French's `Mom` (strip whitespace from headers).
- `test_french_loader_decimals`: print March 2020 from the raw file (percent) and from the loader (decimal), and assert decimal × 100 equals percent to 1e-12.
- `nav_adjclose.csv`: columns date, AKRIX, JENIX, POLIX, IVV, IWF.
- Review evidence: panel shape and first/last date, `missing.csv` in full, NAV first/last dates, and the last French month available.

### 2.4 Calendar and stock returns
- `quarter_calendar`: 28 rows, `t` from 1 to 28, `holdings_date` 2019-09-30 to 2026-06-30, `q_start` = q(holdings_date), `q_end` = q(next calendar quarter end), so the last `q_end` is q(2026-09-30).
- `test_quarters_has_28_rows` replaces `test_quarters_has_30_rows`. Name the change in Deviations; this is an amendment, not a loosened test.
- `monthly_returns`: month-end close is the last available adjusted close in each calendar month (`groupby(index.to_period("M")).last()` over non-missing values per column). The first month of each ticker's series has no return.
- `test_month_end_uses_calendar_periods`: a synthetic series whose last trading day of a month is the 28th returns that day's close, not a value from the next month.

### 2.5 Coverage mapping columns and review lists
- Weights are those of Convention 4.5 on each book, by `sec_id`.
- `unmapped_weight`: map_status `no_match`. `other_nosic_weight`: `no_cik` or `no_sic`. `unpriced_weight`: mapped, but no price on the exact `q_start` of the return quarter starting at that holdings date.
- Column lists. `unmapped_top.csv`: sec_id, id_type, name, max_weight, entity_of_max, periods (semicolon-joined). `unpriced_top.csv`: sec_id, yf_ticker, name, max_weight, entity_of_max, periods. `nocik_top.csv`: sec_id, ticker, name, max_weight, entity_of_max, periods. `large_moves.csv`: entity, t, sec_id, yf_ticker, date, daily_return, weight; sorted by entity, t, date.
- `run_all.py --section 2` produces all of them.
- Review evidence: the 4 lists in full; per entity per period, the unmapped, unpriced and other-no-SIC weights; the largest of each across all books. Then the fresh-clone check, against GitHub per A answer 5.

---

## D. Stop conditions specific to this section

- OpenFIGI returns `no_match` on more than 5% of the value of any single book: complete the section, then report it as the first open question with the 10 largest offenders. Do not stop.
- yfinance returns no data for IVV, IWF or any NAV ticker: stop under rule 4.
- The French files end before 2026-06: report it, do not stop. The monthly sample end follows the data (kickoff 3.3).

---

## E. End of session

Status file: `instructions/02_section_2.status.md`, per rule 11.
