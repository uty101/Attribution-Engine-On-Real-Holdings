# Session 2 status

## Outcome

Stopped under rule 4 at step 2.3.

## Last step reached

Step 2.3 (`c233354`), committed without `nav_adjclose.csv`. Steps 2.1 (`0b64589`) and 2.2 (`097028f`) are complete. Steps 2.4 and 2.5 were not started. All 34 tests pass, locally and in a fresh clone of GitHub at `c233354`.

## Stop reason

Instruction 02, Section D: "yfinance returns no data for IVV, IWF or any NAV ticker: stop under rule 4." `--stage prices` wrote the stock panel (2723 dates × 1265 tickers; CMA and CTRA missing). The NAV call then returned 0 rows for AKRIX. A repeat call also returns 0 rows for AKRIX, AKREX and AKRSX, while JENIX, POLIX, IVV and IWF return 2723 rows each. AKRE is an ETF on yfinance from 2025-10-27, with `fundInceptionDate` 2009-08-31. That suggests the Akre Focus Fund converted to an ETF and Yahoo dropped the mutual fund's history; this is not verified. Evidence is in `review/section_2.md`, under "The stop".

## Blockers and questions for the reviewer

1. **OpenFIGI `no_match` above 5% of book value** (Section D, reported, not a stop). 59 of 140 books are above 5% (Akre 8, Jensen 14, Polen 27, IVV 8, IWF 2); the highest is Jensen 2021-06-30 at 11.67%. Of the 10 largest offenders, Accenture `G1151C101` and Aon `G0403H108` get nothing from OpenFIGI. Exxon `30231G102` gets lines only on non-US exchanges. Jensen filed Google's pre-2015 CUSIP `38259P508`. Options: (a) reviewer `ticker` overrides; (b) a second OpenFIGI pass without `exchCode` for `no_match` IDs, restricted to US venues the reviewer lists. The table and probe output are in the review, under Open questions 1.
2. **AKRIX (the stop), OPEN-31 in `decisions/OPEN.md`.** Options: (a) a non-yfinance AKRIX NAV source, spliced onto AKRE after the conversion date; (b) Akre reported as failed for having no NAV data (Convention 4.19).
3. **OPEN-32:** `unpriced_weight` and `other_nosic_weight` overlap for a `no_cik` ticker with no price, for example CMA and CTRA. Options: (a) report both as defined; (b) count only priced rows in `other_nosic_weight`.
4. **Choices made where the spec was silent**, listed under Deviations in the review, for confirmation:
   - the OpenFIGI client lives in `scripts/pull_data.py`;
   - `exchCode: "US"` is kept on ISIN jobs;
   - `ff12` is blank for `no_match` rows;
   - a `cik` override applies only to a row with a ticker;
   - French blocks are kept as filed;
   - the French pull sends its own User-Agent.
5. 29 of the 34 `no_cik` rows are ETFs held in the 13F books, mostly Polen's. They go to Other under Convention 4.6.
6. The first OpenFIGI run was stopped at 1410 of 1622 by the session's 30-minute limit on background tasks, before it wrote anything. The rerun took 7 min 48 s with 0 retries.
7. `CLAUDE.md` and `PLAN.md` were not touched; instruction 02 asks for no amendment.

## git log origin/main --oneline -3

Captured after the push of the 3 step commits, before this file and the review were committed:

```
c233354 step 2.3: prices and French loaders (stopped: yfinance has no AKRIX data)
097028f step 2.2: mapping module, French pull, security map
0b64589 step 2.1: SEC and OpenFIGI pulls
```
