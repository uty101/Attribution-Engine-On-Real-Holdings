# Session 3 status

## Outcome

Completed. Section 3 is finished. `python scripts/run_all.py --section 3` passes every check and gives byte-identical outputs on 2 runs. All 50 tests pass, both locally and in a fresh clone of GitHub at `2596b35`. In that clone, `run_all.py --section 3` regenerated every committed output with `git status` clean.

## Last step reached

Step 3.4 (`2596b35`). Session 3 commits:

- 3.0 (`86df1a2`);
- 3.1 (`92f1eb1`);
- 3.2 (`3f1bbfe`);
- 3.3 (`ac2c391`);
- 3.4 (`2596b35`).

## Stop reason

None. No rule 4 condition was hit:

- every pull succeeded (`--stage sec --overrides-only`, `--stage prices --new-only`);
- all 29 `cik` overrides passed the name check;
- every Section 1 and 2 check passed after the overrides;
- no benchmark |gap| exceeds `benchmark_gap_stop` (0.03). The largest is 1.16%.

## Results

| fund | corr | pass | quarters | mean gap | gap bootstrap 5% to 95% |
|---|---|---|---|---|---|
| Akre | 0.990 | yes | 26 | +0.16% | −0.07% to +0.39% |
| Jensen | 0.9996 | yes | 28 | +0.21% | +0.14% to +0.29% |
| Polen | 0.998 | yes | 28 | +0.39% | +0.27% to +0.52% |

The unmapped weight now has a maximum of 0.03% for Akre, 0.10% for Jensen, 0.29% for Polen, and 1.48% for both IVV and IWF. The full tables are in `review/section_3.md`, D.3.

## Questions for the reviewer

1. **An existing test's input changed** (Deviation 1). `test_cik_override` from Section 2 used `source_note = "reviewer"`. Section B's new name check rejects that note against the synthetic name "GONE CO", so the test failed.
   - The input is now `"Gone Co"`.
   - No assertion changed.
   - This follows the 02c precedent of updating a test to a format the instructions changed.

   Is that acceptable, or should it have been a rule 4 stop?
2. **The POSITION_RETURNS key** (Deviation 2). The kickoff schema is kept, and `sec_id` is added after `cusip`, because 745 ISIN-only IVV rows have a blank `cusip`. Should `sec_id` replace `cusip` instead?
3. **The gap standard deviation** (Deviation 12) uses ddof 1. Both versions are printed. Should it be ddof 0?
4. **Other choices where the spec was silent**, listed as Deviations 3 to 11, 13 and 14 for confirmation. The main ones:
   - `--overrides-only` and `--new-only` flags, so the two pulls touch only what step 3.0 names;
   - the `cik` name check reads `sic.csv`'s submissions `name`;
   - `period_date` of a `quarter_return` row is h_t;
   - an override recomputes its book's neutral return (Convention 4.9);
   - blank `r` for empty buckets;
   - benchmark NAV from compounded months. It differs from the Convention 4.14 ratio by at most 4.9e-16.
5. **IWF t = 27** (Q2 2026) is the only benchmark quarter above `benchmark_gap_max`, with a gap of −1.16%. Its unmapped weight is 0.09% and its unpriced weight 0%.
6. **`quarter_return` candidates.** D.4 of the review lists:
   - 10 fund position-quarters with a daily |return| above 25% and weight above 0.5%;
   - 4 IVV and IWF position-quarters with weight above 1%.

   Nothing was adjusted.
7. **Delisted names are all Unpriced; none is "delisted in quarter".** yfinance keeps no history for delisted tickers: every one of the 1314 price columns runs to 2026-09-30, so `delisted_weight` is 0 in every book. 22 of the override tickers are new entries in `missing.csv`, every one with a reviewer `cik` override, as Section B expected. Their weight earns the neutral return.
8. **Reused tickers.** The new price columns `INFO` and `STI` belong to later companies; they start in 2024 and 2022. Neither prices any position: all 18 positions on them are Unpriced.

## git log origin/main --oneline -3

Captured after the push of the step commits, before this file and the review were committed:

```
2596b35 step 3.4: reconstruction table, fund gate and gap bootstrap
ac2c391 step 3.3: benchmark check against IVV and IWF
3f1bbfe step 3.2: book returns, buckets and monthly book returns
```
