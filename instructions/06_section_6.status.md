# Session 6 status

## Outcome

Completed. Section 6 is finished, and so is step 6.0, the residual volatility change.

- `python scripts/run_all.py --section 6` passes every check.
- 2 runs give byte-identical CSVs and PNGs.
- All 76 tests pass, both locally and in a fresh clone of GitHub at `318a36a`.
- In that clone, `run_all.py --section 6` regenerated every committed output with `git status` clean.

## Last step reached

Step 6.2 (`318a36a`). Session 6 commits:

- 6.0 (`0ece094`), `resid_vol_ann` = √(SSR / (n − 7)) × √12;
- 6.1 (`5b3f0a0`);
- 6.2 (`318a36a`).

## Stop reason

None. No rule 4 condition was hit:

- no earlier test failed;
- Σ CTE = TE at every fund and date, and the sector sums equal TE, both to 5.6e-17 at worst against the 1e-12 check;
- every window has a return on every day for at least 1 ticker;
- no ticker has 2 FF12 buckets or 2 CIKs.

## Results

All rows are in `review/section_6.md`, E.1 to E.5.

| fund | AS 2026-06-30 | TE ex-ante 2026-06-30 | mean TE ex-ante (28) | TE realised (83 months) | top 15 share of TE | dates ridged |
|---|---|---|---|---|---|---|
| akre | 0.974 | 13.46% | 8.82% | 10.39% | 76.1% | 0 |
| jensen | 0.616 | 5.75% | 5.27% | 5.24% | 36.5% | 0 |
| polen | 0.618 | 8.43% | 6.71% | 6.43% | 76.5% | 10 |

## Questions for the reviewer

1. **`n_names`** (Deviation 1) is the number of tickers in the TE set, which is also the dimension of Σ. Neither the kickoff nor the instructions define it. Is that the intended definition?
2. **Realised TE sample** (Deviation 2). Section C says "the 83 months", so the sample is October 2019 to August 2026. `book_monthly.csv` has 84 months, to September 2026. Over 84 months Akre's realised TE is 11.4%, not 10.4%: its book trails IVV by 13.3% in September 2026. Jensen and Polen change by less than 0.2 points. Keep 83?
3. **Polen's ETF holdings** (E.5). Polen's 13F holds IWF itself at every date, plus VONG, SPY, VOO, VUG, IWM or IVV at some dates. Near-duplicate pairs (VONG/IWF, SPY/VOO, GOOG/GOOGL) push cond(Σ_d) to about 1e7, so Polen is ridged at the 10 dates from 2023-12-31 to 2026-03-31. The ETFs are kept as priced, mapped equity rows. Should they stay?
4. **Format details** (Deviations 3 to 5):
   - `cte_sectors.csv` has 12 FF12 rows per fund and date, 0 where empty;
   - Chart 3 bars are sorted by signed CTE, red for positive and blue for negative, with no legend;
   - issuer keys are `cik:<n>` or `sec_id:<id>`, used internally only.
5. **For the write-up:**
   - Jensen's GOOG and GOOGL both appear in its top 15, with opposite signs. Active share nets them at the CIK, but risk is per ticker.
   - Akre's ex-ante TE averages 8.8% against 10.4% realised, so it understates. Jensen's and Polen's ex-ante averages are within 0.3 points of realised.

## git log origin/main --oneline -3

Captured after the push of the step commits, before this file and the review were committed:

```
318a36a step 6.2: active share, ex-ante TE with its Euler split, realised TE and Chart 3
5b3f0a0 step 6.1: fill rule, risk weights and the conditioned Ledoit-Wolf covariance
0ece094 step 6.0: residual volatility uses n − 7
```
