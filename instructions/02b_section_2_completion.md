# instructions/02b_section_2_completion.md — Session 2b: fixes to finish Section 2

Pull `main` first. This file finishes Section 2. `instructions/02_section_2.md` stays binding wherever this file does not change it. It holds fixes and the decisions that unblock the stop, then steps 2.4 and 2.5 as already specified.

---

## A. Review of steps 2.1 to 2.3 (`764b38b`)

The stop was correct, and so was reporting the `no_match` problem rather than stopping on it.

The reviewer measured the `no_match` problem on the Section 1 books with its own code: the value-weighted share of `no_match` `sec_id`s per book, mean and maximum across the 28 dates.

| entity | mean | max |
|---|---|---|
| akre | 2.6% | 7.0% |
| jensen | 5.5% | 11.7% |
| polen | 5.9% | 8.5% |
| ivv | 4.2% | 8.7% |
| iwf | 3.1% | 6.3% |

That is too much to leave to the neutral-return rule: it would bias every selection effect. 354 of the 1,622 `sec_id`s failed. 114 of those start with a letter (CINS numbers for foreign issuers, such as Accenture `G1151C101`). The rest include live US names (Exxon, Honeywell), where OpenFIGI's CUSIP coverage simply has gaps. Ticker overrides alone cannot close a gap that wide by hand, so this file adds 3 mechanical fallback passes, each with a name check. The reviewer's overrides then cover only what remains.

AKRIX: Akre Focus Fund converted into the AKRE ETF in October 2025, and Yahoo dropped the mutual fund's history. The fund's own N-PORT filings report monthly total returns for every share class (Form N-PORT Part B Item B.5, `returnInfo`/`monthlyTotReturns`). That is an official source, net of fees, from the same EDGAR stack this repo already parses. It replaces yfinance for Akre.

---

## B. Decisions

| item | decision | reason |
|---|---|---|
| OPEN-31, AKRIX | **New option (c)**: Akre's NAV return comes from the fund's own N-PORT `monthlyTotReturns`. See step 2.1b. | Official and fee-net, so no splicing of 2 market-data vendors |
| Open question 1, `no_match` | **(b) extended**: 3 fallback passes in step 2.1c, then reviewer `ticker` overrides for whatever remains (instruction 03). | Measured gap of 3% to 6% of value |
| OPEN-32 | **(a)**. Report both weights as defined; they may overlap. Each column answers its own question. | No information lost |
| Deviation: OpenFIGI client in `scripts/pull_data.py` | Accepted | It is network code |
| Deviation: `exchCode: "US"` on ISIN jobs | Accepted for pass 1 | Pass 3 covers what it misses |
| Deviation: `ff12` blank for `no_match` | Accepted | Those rows sit in the Unmapped bucket |
| Deviation: `cik` override only on a row with a ticker | Accepted | A CIK without a ticker cannot be priced anyway |
| Deviation: French blocks kept as filed; French pull sends its own User-Agent | Accepted | |
| ETFs in 13F books in Other | Accepted (Convention 4.6) | Reported, not judged |
| Long pulls | Run each network stage in the foreground, or split it so that no single call exceeds the session's 30-minute background limit. A stage that is cut off writes nothing and is rerun. | The first OpenFIGI run was lost this way |

---

## C. Steps

### 2.1b Fund NAV returns from N-PORT
Commit `step 2.1b: fund monthly NAV returns from N-PORT`.
- `parse_nport` also returns the header's class list and the `monthlyTotReturns` block. Each `monthlyTotReturn` element has attributes `classId`, `rtn1`, `rtn2` and `rtn3` (percent). `rtn3` is the month of `repPdDate`, `rtn2` the month before, and `rtn1` the month before that. New signature: `parse_nport(xml) -> tuple[dict, pd.DataFrame, pd.DataFrame]`, the 3rd frame having columns class_id, month (`YYYY-MM`), rtn_pct. Update the existing callers and tests; the 1st and 2nd outputs are unchanged.
- Series resolution, new stage `--stage navret`:
  - For each fund, resolve the series and the class ID of its NAV ticker from `company_tickers_mf.json`.
  - If AKRIX is absent there (expected after the conversion), find the series with EDGAR full-text search for NPORT-P filings by "Akre Focus Fund", as session 1 did for iShares. Take the class whose name contains "Institutional".
  - Print the resolution in the review: fund, series_id, class_id, class name, and how it was found.
- The stage lists every NPORT-P and NPORT-P/A of each fund's series filed from 2019-11-01 to 2026-12-31, using the same feed code as the benchmarks, then parses each one.
  - Output `data/raw/edgar/nport_returns/{fund}_monthly.csv`: entity, series_id, class_id, accession, filing_date, period_date, month, rtn_pct.
  - When 2 filings report the same class and month, keep the latest by filing date.
  - XML is not committed; hashes go in the manifest.
- **Akre monthly NAV series** for months October 2019 to September 2026, chosen month by month:
  1. the B.5 return of AKRIX's class;
  2. else the B.5 return of an ETF class in the same series;
  3. else the month return of AKRE from yfinance adjusted month-end closes, for months fully after 2025-10-27;
  4. else missing.
  Write `outputs/tables/nav_monthly.csv` (entity, month, ret, source) for all 3 funds. Jensen and Polen use yfinance month-end returns, with source `yfinance`.
- **Cross-check.** Run the same N-PORT pull for JENIX and POLIX. Report per fund the maximum and mean absolute difference between the B.5 monthly return and the yfinance month return over the months both have. This validates the B.5 source against a vendor on the 2 funds that have both. Report only; no test threshold. The reviewer sets one after seeing the figures.
- Config:
  - Add `nav_source = "nport"` and `etf_successor = "AKRE"` to `[entities.akre]`, and `nav_source = "yfinance"` to `[entities.jensen]` and `[entities.polen]`.
  - Keep `nav_ticker = "AKRIX"` as the class identity.
  - Update `tests/test_config.py`'s key list.
- Tests:
  - `test_parse_monthly_returns` (synthetic `returnInfo` with 2 classes: rtn1 to rtn3 map to the right months);
  - `test_latest_filing_wins_for_month` (synthetic);
  - `test_akre_month_source_order` (synthetic: order 1 to 4 above).
- **Stop condition.** If the Akre series has more than 1 missing month from October 2019 to the last month any source reaches, stop under rule 4 and list the months.

### 2.1c OpenFIGI fallback passes
Commit `step 2.1c: OpenFIGI fallback passes with name check`.
- `parse_nport` keeps the `other` identifier whose `otherDesc` is "Inhouse Asset ID" as a new column `other_id` in HOLDINGS_RAW_NPORT. Rerun `--stage edgar`; 13F XML must come back byte-identical, as in 1.5b.
- New stage `--stage figi2`, run on every `sec_id` with no accepted pass-1 result. In order, stopping at the first accepted result:
  - **Pass 2, ISIN crosswalk.** Find an ISIN for the `sec_id`:
    - (i) from any N-PORT row (IVV or IWF, any period) whose `cusip` or `other_id` equals it;
    - (ii) else, for a CUSIP whose first character is a digit, the US ISIN `"US" + cusip + Luhn check digit`.
    Query OpenFIGI `ID_ISIN` with `exchCode: "US"`.
  - **Pass 3, no exchange filter.** Query OpenFIGI with the `sec_id`'s own type and no `exchCode`. Accept the first `Equity` result whose `exchCode` is in {US, UN, UW, UQ, UA, UR, UP, UF, UV, UD}.
  - **Pass 4, Yahoo search.** For each ISIN found in pass 2, call `yfinance.Search(isin, max_results=8)`. Accept the first quote whose `quoteType` is EQUITY or ETF and whose `exchange` is in {NYQ, NMS, NGM, NCM, ASE, PCX, BTS}.
- **Name check on passes 2 to 4.** Normalise a name by upper-casing, replacing every non-alphanumeric character with a space, splitting, and dropping a leading `THE`. A result is accepted only if its first token equals the first token of the holding's name, taken from the book row with the largest weight. Rejected results are logged with the reason.
- Output `data/raw/openfigi/fallback.csv`: sec_id, pass, query_type, query_value, rank, ticker, name, exch_code, market_sector, security_type, accepted, reject_reason. It holds every result seen, accepted or not.
- `build_security_map` gains a parameter: `build_security_map(figi, fallback, overrides, tickers, sic, ff12)`. Precedence: override ticker, then pass 1, 2, 3, 4. `source` is `openfigi`, `figi_isin`, `figi_noexch` or `yahoo_isin`, with `;override_ticker` / `;override_cik` appended when an override applied.
- Tests in `tests/test_mapping.py`:
  - `test_fallback_precedence` (synthetic: pass 1 beats 2 beats 3 beats 4; an override beats all);
  - `test_name_check_rejects` (synthetic: a pass 4 result for a different company is rejected and logged);
  - `test_us_isin_from_cusip` (`30231G102` gives `US30231G1022`; `037833100` gives `US0378331005`).
- Rerun `--stage sec` for any new CIKs.

### 2.3b Prices
Commit `step 2.3b: prices for the extended map and NAV`.
- Rerun `--stage prices` on the full extended map. `nav_adjclose.csv` columns: date, JENIX, POLIX, IVV, IWF, AKRE. AKRIX is not requested from yfinance.
- Section D of instruction 02 applies to JENIX, POLIX, IVV, IWF and AKRE.

### 2.4 and 2.5
As in instruction 02, Section C, unchanged, with these additions to 2.5:
- `outputs/tables/unmapped_top.csv` lists the **60** largest remaining `no_match` `sec_id`s, not 20, with name, max weight and every period held. The reviewer writes ticker overrides from it in instruction 03.
- Report every book whose remaining `unmapped_weight` exceeds 2%.

---

## D. Review evidence for `review/section_2.md`, rewritten for all of Section 2

Everything listed in instruction 02, plus:

1. The fund series resolution (2.1b), and for Akre the count of months by source, and every month that is missing.
2. The Jensen and Polen B.5 against yfinance cross-check, as 2 rows of figures and the 5 months with the largest absolute difference per fund.
3. Per pass, the number of `sec_id`s accepted and rejected. The 20 largest accepted fallback mappings by maximum weight, printed with the holding name next to the result name, so the reviewer can check them.
4. The mean and maximum `unmapped_weight` per entity after the fallbacks, in the same layout as the table in Section A above.

---

## E. End of session

Status file: `instructions/02b_section_2_completion.status.md`, per rule 11. Push the step commits, run the fresh-clone check against GitHub, then commit and push the review and status files.
