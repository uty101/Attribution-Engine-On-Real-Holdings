# Session 1b status

## Outcome

Completed. Section 1 is finished, and `python scripts/run_all.py --section 1` passes every check on H = 2019-09-30 to 2026-06-30: 28 dates, 140 books.

## Last step reached

Step 1.6b (`fb2eee2`). Steps 1.2b (`62f5b3d`), 1.4b (`d46da92`) and 1.5b (`2ab736d`) are complete. `review/section_1.md` was rewritten for all of Section 1, per 01b Section D.

## Stop reason

None. No rule 4 condition was hit:

- the 1.5b re-pull succeeded;
- all 26 tests pass, both locally and in a fresh clone;
- every Section 1 check passes.

## Blockers and questions for the reviewer

1. **Please confirm what "a valid 12-character ISIN" means** (review, Deviations). It is implemented as ISO 6166 with the Luhn check digit. A plain 12-alphanumeric rule would make the fixed test `test_only_ec_ns_rows_kept` fail: its `US0000000000` row would then be kept. Every ISIN on a real ISIN-only row passes the check digit, and no EC/NS row in any book is dropped.
2. **The "blank CUSIP" rows are mostly not blank.** IVV files 411 of the ISIN-only rows over the 28 books as `<cusip>N/A</cusip>`, and omits the element on 334. IWF omits it on 271. The rule as written ("valid CUSIP, else valid ISIN") covers all 3 forms, and the raw CSVs keep `N/A` as filed.
3. **One issuer, two keys, a Section 2 issue** (review, Open question 1). IVV files non-US issuers with only an ISIN on all 28 dates. IWF does the same until 2022-06-30 and then switches to their CUSIP (e.g. Accenture `G1151C101`). The 13F books always use the CUSIP. SECURITY_MAP is keyed by `cusip`, so the ISIN-only rows (2.7% to 4.0% of IVV) have no OpenFIGI lookup key yet. 2 options are in the review: (a) key SECURITY_MAP by `sec_id` and query OpenFIGI with `ID_ISIN` for ISIN rows; (b) recover the CUSIP from IVV's "Inhouse Asset ID" identifier. Neither was chosen.
4. **The only `NPORT-P/A`** in either feed is IVV `0002071691-26-015790`, filed 2026-07-13 for period 2025-09-30. It is now the filing used for that period. Its 507 rows carry exactly the same `valUSD` values as the original.
5. **Push and fresh-clone check.** 01b Section E says to push once, at the end. So the fresh-clone check cloned the local `main` at `fb2eee2`, which is the same commits as the push, rather than the copy on GitHub. For the same reason, the log below was captured before the push.
6. `CLAUDE.md` amendments 5 to 10 are committed in `fb2eee2`, as 01b step 1.6b directs. The safety check did not refuse the edit. `PLAN.md` was not touched (rule 14), and amendment 7 says to read 28 where it says 30.

## git log origin/main --oneline -3

Captured before the single push at the end of this session. `origin/main` was then still at the instruction commit:

```
883bdb2 instructions: 01b section 1 completion
e5dba91 session 1: review and status (stopped at 1.6, 2019 N-PORT books missing)
15809d3 step 1.6: holdings books and coverage (stopped: 4 N-PORT books missing)
```

The push sends these 4 step commits on top of `883bdb2`, followed by the commit that adds this file and `review/section_1.md`:

```
fb2eee2 step 1.6b: rerun section 1 on 28 dates
2ab736d step 1.5b: re-pull EDGAR with %.17g and NPORT-P/A
d46da92 step 1.4b: keep ISIN-only equity rows, accept NPORT-P/A
62f5b3d step 1.2b: HTTP timeout and retry on connection errors
```
