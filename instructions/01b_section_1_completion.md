# instructions/01b_section_1_completion.md — Session 1b: fixes to finish Section 1

Pull `main` first. This file finishes Section 1. `instructions/01_section_1.md` stays binding wherever this file does not change it. It holds fixes only, plus the decisions that unblock the stop. No Section 2 work.

---

## A. Review of steps 1.0 to 1.6 (`e5dba91`)

What the reviewer checked independently, on Linux with Python 3.12:

1. Fresh clone, lock install, `pytest -p socket --disable-socket -q`: all tests pass.
2. **Raw 13F files against an outside source.** The committed Akre 2026-06-30 information table, parsed with the reviewer's own lxml code, gives Mastercard 57636Q104 at $1,022,015,722 and 1,989,906 shares, and Moody's 615369105 at $523,979,978 and 1,156,893 shares. That matches a third-party 13F summary of the same filing to the dollar. `coverage.csv` totals for 2026-06-30 match the same source: Akre $5,122,536,308 (20 rows, 19 kept, the dropped row being call options) and Polen $11,610,786,601 (219 rows).
3. **Book totals from raw XML.** The reviewer re-parsed all 90 original 13F filings in H with its own code and applied the units switch. Every total matches `coverage.csv` except 23 that differ by $1 to $5. Cause: Problem 2 below.
4. **IVV weights.** Apple at 7.70% of IVV at 2023-06-30 is right for the S&P 500 at that date. EC/NS rows number 503 to 505 per period and sum to 99.6% to 99.9% of net assets.
5. **The stop is correct.** The reviewer accepts the full-text search evidence that iShares Trust filed no public NPORT-P before November 2019.

The reviewer found 2 problems the session did not, and both are bugs in the reviewer's own spec.

**Problem 1: about 3% of the S&P 500 is silently dropped.** Every period, 24 to 31 IVV equity rows have no CUSIP, only an ISIN. They are the companies domiciled outside the US: Accenture, Linde, Medtronic, Eaton, Chubb, Aon, NXP, Johnson Controls, TE Connectivity, Trane and others. At 2023-06-30 they are 25 rows and 3.15% of IVV; across periods, between 2.68% and 3.98%. For IWF they are about 2%. Instruction 01, D 1.4 told you to drop blank-CUSIP rows, so you followed the spec. The spec was wrong: these are real benchmark holdings, several of which the funds also own under a CUSIP in their 13F. Fix in step 1.4b.

**Problem 2: `%.10g` loses dollars.** Kickoff rule 9 set the CSV float format to `%.10g`. Values above $10bn keep only 10 significant digits, so 12,003,999,013 is written as 12,003,999,010. Fix: `%.17g`, which round-trips every float64 exactly.

---

## B. Decisions

| item | decision | reason |
|---|---|---|
| Stop: missing 2019 benchmark books | **(a)**. H starts at 2019-09-30. 28 holdings dates, 28 return quarters (Q4 2019 to Q3 2026). `sample.first_holdings_date = "2019-09-30"`. Wherever the kickoff, `PLAN.md` or instruction 01 says 30 holdings dates or 30 quarters, read 28; for example, QUARTERS has 28 rows and `coverage.csv` has 140. Monthly series start in October 2019. | (b) needs an HTML parser for 2 pre-N-PORT filings to buy 2 quarters out of 30; not worth a new failure surface |
| HTTP timeout | **(a), extended.** `[edgar] timeout_s = 30`. `EdgarClient.__init__(self, user_agent, min_interval, retries, backoff, timeout, session=None)` passes `timeout` to every `get`. `requests.Timeout` and `requests.ConnectionError` retry exactly like 5xx. | a pull with no timeout can hang forever on 1 slow response |
| Text-era 13F filings get a blank `infotable_name` | **Accepted.** | none of them is in H |
| `entity` filled by the caller | **Accepted.** | the signatures carry no entity |
| `NPORT-P/A` excluded | **Reversed.** `list_nport_filings` keeps `NPORT-P` and `NPORT-P/A`. For each period, the latest filing by filing date wins, whether original or amendment. | an N-PORT amendment restates the whole report, so the latest one is the correct book |
| `coverage.csv` column definitions | **Accepted as written** in the review's Deviations section. | they are consistent and documented |
| `run_all.py` writes outputs before reporting failed checks | **Accepted.** It still exits 1 when a check fails. | the reviewer needs the table to see the failure |
| ISIN-only equity rows | **Kept.** See step 1.4b. | Problem 1 |
| CSV float format | **`%.17g`** everywhere a CSV is written. Rule 9 in `CLAUDE.md` is amended. | Problem 2 |
| Active share issuer key (Convention 4.17) | **Amended for Section 6:** issuer = SEC CIK from SECURITY_MAP. A row with no CIK is its own issuer, keyed by `sec_id`. | ISIN-only rows have no CUSIP-6; CIK also nets share classes (GOOG and GOOGL share 1 CIK) |

---

## C. Steps

### 1.2b HTTP timeout
Commit `step 1.2b: HTTP timeout and retry on connection errors`.
- `config.toml`: `timeout_s = 30` as the last key of `[edgar]`. `attrib/config.py` loads it, and `tests/test_config.py` adds it to the literal key list.
- `attrib/edgar.py`: the signature in Section B.
- `tests/test_edgar_client.py`:
  - `_client` passes `CFG.edgar.timeout_s`, and the fake session's `get` accepts `timeout=None`;
  - new `test_timeout_passed_to_get`: the recorded `timeout` equals 30;
  - new `test_connection_error_then_200_retries`: `requests.ConnectionError` once, then 200, gives recorded backoff sleeps `[2]`.

### 1.4b N-PORT: ISIN-only rows and amendments
Commit `step 1.4b: keep ISIN-only equity rows, accept NPORT-P/A`.
- HOLDINGS schema becomes: entity, period_date, cusip, isin, sec_id, name, value_usd, shares.
  - `sec_id` = `cusip` when it is a valid 9-character CUSIP, else `isin` when it is a valid 12-character ISIN.
  - For 13F rows `isin` is blank and `sec_id` = `cusip`.
  - A row with neither is dropped and its value counted in `dropped_value_usd`.
  - Aggregation (Convention 4.3) is by `sec_id`.
- `resolve_nport_books` keeps EC/NS rows with a blank CUSIP and a valid ISIN.
- `list_nport_filings` keeps `NPORT-P` and `NPORT-P/A`. Latest filing date per period wins.
- `coverage.csv` gains a column `isin_only_weight` (the weight of rows whose `sec_id` is an ISIN), placed after `amendments_used`. It is 0 for 13F rows.
- Tests in `tests/test_edgar_nport.py`:
  - `test_isin_only_row_kept` (synthetic: an EC/NS row with no CUSIP and ISIN `IE00B4BNMY34` is kept with `sec_id` = that ISIN);
  - `test_row_with_no_ids_dropped` (synthetic);
  - `test_amendment_supersedes_original` (synthetic `NPORT-P` then a later `NPORT-P/A` for the same period: the `/A` wins).
  - `test_ivv_fixture_shape` now also asserts that exactly 25 kept rows have an ISIN `sec_id`, and that their `pctVal` sum is in [3.0, 3.3]. The reviewer measured 25 rows and 3.154 on this fixture.

### 1.5b Re-pull
Commit `step 1.5b: re-pull EDGAR with %.17g and NPORT-P/A`.
- Change both CSV writers (`scripts/pull_data.py`, `scripts/run_all.py`) to `float_format="%.17g"`.
- Rerun `--stage edgar`. `data/raw/edgar/nport/holdings_{id}.csv` are rewritten with full precision, including any `/A` filings.
- Update `MANIFEST.json`. The 13F XML files should come back byte-identical; show the hash comparison in the review.

### 1.6b Holdings and coverage on H = 2019-09-30 to 2026-06-30
Commit `step 1.6b: rerun section 1 on 28 dates`.
- `config.toml`: `first_holdings_date = "2019-09-30"`.
- Update any test that counts dates.
- Rerun `scripts/run_all.py --section 1`. All checks must pass. If any fails, stop under rule 4.
- `CLAUDE.md` `## Amendments`, new lines:
  - (5) the timeout signature, superseding line 3 on the signature;
  - (6) rule 9 float format is `%.17g`;
  - (7) H starts 2019-09-30, 28 dates, read 28 wherever 30 is written;
  - (8) the HOLDINGS schema with `isin` and `sec_id`, aggregation by `sec_id`;
  - (9) `NPORT-P/A` accepted, latest per period wins;
  - (10) Convention 4.17 issuer key = CIK, fallback `sec_id`.
  Each cites this file.

---

## D. Review evidence, rewriting `review/section_1.md` for all of Section 1

Keep every item of instruction 01, Section E (coverage now 140 rows), and add:

1. For IVV and IWF, per period: the count and summed weight of ISIN-only rows (now kept).
2. Every `NPORT-P/A` in either feed, with its period and whether it is the filing used.
3. Precision check: for akre 2023-06-30, polen 2023-06-30 and ivv 2026-06-30, `total_value_usd` from `coverage.csv` printed next to the sum recomputed from the raw file in the review script, and their difference, which must be exactly 0.
4. The `MANIFEST.json` hash comparison for the 13F XML files before and after the re-pull.

---

## E. End of session

Status file: `instructions/01b_section_1_completion.status.md`, per rule 11. Push once at the end, then stop.
