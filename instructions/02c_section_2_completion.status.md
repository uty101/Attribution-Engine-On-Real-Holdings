# Session 2c status

## Outcome

Completed. Section 2 is finished. `python scripts/run_all.py --section 2` passes every check and gives byte-identical outputs on 2 runs. All 43 tests pass, locally and in a fresh clone of GitHub at `8f996a0`, where `run_all.py --section 2` reproduced every output hash.

## Last step reached

Step 2.5 (`8f996a0`). Session 2c commits, in the order 02c C item 2 sets:

- 2.0c (`035da83`);
- 2.1c (`e21e4c1`);
- 2.3b (`6d637e2`);
- 2.1b-2 (`da938d2`);
- 2.4 (`3853eff`);
- 2.5 (`8f996a0`).

## Stop reason

None. No rule 4 condition was hit:

- the Akre NAV series misses only 2025-08 to 2025-10, the gap 02c accepted;
- JENIX, POLIX, IVV, IWF and AKRE all returned data;
- every pull succeeded.

## Blockers and questions for the reviewer

1. **Unmatched weight after the fallbacks.** The fallback passes matched 100 of the 354 `sec_id`s OpenFIGI's first pass had missed, so 254 remain.

   Mean and max `unmapped_weight` before and after:

   | entity | before, mean | before, max | after, mean | after, max |
   |---|---|---|---|---|
   | akre | 2.64% | 7.00% | 2.47% | 7.00% |
   | jensen | 5.49% | 11.67% | 0.89% | 6.99% |
   | polen | 5.89% | 8.52% | 0.43% | 0.80% |
   | ivv | 4.18% | 8.73% | 3.52% | 6.94% |
   | iwf | 3.10% | 6.26% | 1.87% | 4.25% |

   52 books stay above 2%: Akre 13, IVV 21, IWF 14 and Jensen 4. The main names are:
   - Brookfield `112585104` for Akre;
   - Alphabet's old CUSIP `38259P508` and United Technologies `913017109` for Jensen;
   - Exxon, Ansys and the long tail of delisted names for IVV and IWF.

   `outputs/tables/unmapped_top.csv` lists the 60 largest, for instruction 03.
2. **Name-check rejections that look like the right company:** Exxon (XOM), GE, NOV, QuidelOrtho (QDEL), and Liberty Formula One (FWONK, FWONA). The first-token rule rejects renamed or reworded companies. These are candidates for `ticker` overrides; whether to accept them is the reviewer's call.
3. **Fallback tickers yfinance cannot price.** 33 tickers are in `missing.csv`, mostly acquired or delisted names such as CELG, ALXN, MXIM, HES, WBA and DBRG. Their weight now counts as Unpriced rather than Unmapped. Under OPEN-32 (a), 317 book rows count in both `unpriced_weight` and `other_nosic_weight`; the largest is Celgene in IWF at 2019-09-30, at 0.50%.
4. **Choices made where the spec was silent**, listed under Deviations in the review, for confirmation:
   - the 2.0c commit;
   - commit contents follow the 02c step order;
   - 2 changed `source` expectations in existing tests, as 02b's format requires;
   - pass 2 for ISIN `sec_id`s, and its Equity rule;
   - logging of empty queries;
   - blank `figi` for fallback mappings;
   - `--stage sec` rebuilding all of `sic.csv`;
   - no rows for missing months in `nav_monthly.csv`;
   - the cross-check kept as evidence only.
5. **B.5 against yfinance.** The mean absolute monthly difference is 1.1 bp for Jensen (78 months; its B.5 lacks 2024-12 to 2025-02) and 2.1 bp for Polen (84 months). The largest single months are 29 bp and 35 bp. The threshold is the reviewer's to set.
6. `CLAUDE.md` amendment 11 is committed in `035da83`. The safety check did not refuse the edit.

## git log origin/main --oneline -3

Captured after the push of the step commits, before this file and the review were committed:

```
8f996a0 step 2.5: coverage mapping columns and review lists
3853eff step 2.4: quarter calendar and stock returns
da938d2 step 2.1b-2: NAV monthly table and B.5 cross-check
```
