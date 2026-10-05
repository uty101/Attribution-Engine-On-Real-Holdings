# Session 5 status

## Outcome

Completed. Section 5 is finished, and so is step 5.0, the Chart 1 fix.

- `python scripts/run_all.py --section 5` passes every check. 2 runs give byte-identical CSVs and PNGs.
- `run_all.py --section 4` still passes after step 5.0.
- All 67 tests pass, both locally and in a fresh clone of GitHub at `dbd4e89`.
- In that clone, `run_all.py --section 5` regenerated every committed output with `git status` clean.

## Last step reached

Step 5.2 (`dbd4e89`). Session 5 commits:

- 5.0 (`6771aea`), Chart 1 with the total excess line, and the `filled` column;
- 5.1 (`8640da6`);
- 5.2 (`dbd4e89`).

## Stop reason

None. No rule 4 condition was hit:

- no earlier test failed;
- every Table 2 year row sums to the year's excess return within 1e-12;
- no ticker sits in 2 buckets within a book.

## Results

Full-sample fits, monthly, with HAC (maxlags 3) t-stats. All rows are in `review/section_5.md`, E.1 and E.2.

| series | n_months | R² | resid vol (ann.) | alpha / month | t | β mkt |
|---|---|---|---|---|---|---|
| akre_book | 83 | 0.764 | 9.7% | −0.46% | −1.39 | 0.955 |
| akre_nav | 80 | 0.770 | 9.2% | −0.30% | −0.94 | 0.904 |
| jensen_book | 83 | 0.923 | 4.3% | −0.32% | −2.23 | 0.884 |
| jensen_nav | 83 | 0.915 | 4.5% | −0.36% | −2.42 | 0.861 |
| polen_book | 83 | 0.929 | 5.4% | −0.40% | −2.06 | 1.040 |
| polen_nav | 83 | 0.923 | 5.6% | −0.52% | −2.59 | 1.026 |
| ivv_book | 83 | 0.997 | 1.0% | +0.002% | 0.06 | 0.988 |
| iwf_book | 83 | 0.973 | 3.2% | +0.11% | 1.02 | 1.104 |

The IVV sanity check:

- the returns-based market beta of `ivv_book` is 0.988;
- the holdings-based beta lies between 0.962 and 1.107 over the 28 dates, with a mean of 1.018.

## Questions for the reviewer

1. **`excluded_weight` in `holdings_exposures.csv`** (Deviation 7). It is 1 minus the weight that entered the exposure, so it includes any priced, mapped position with no beta, own or fallback. Section C names only unmapped and unpriced weight. The only such position is YETI in Polen at 3 dates in 2020, at most 0.0099%: it is Polen's only NoDur name and has fewer than 24 months. The column is blank on the active rows. Is that acceptable?
2. **The constant is named `alpha`** in `factor_fit.csv` and in the D-24 dict (Deviation 1).
3. **`resid_vol_ann` uses ddof 1** (Deviation 2), matching `std_gap` in `gate.csv`. Should it be ddof 0, or n − 7?
4. **`factor_by_year.csv` carries all 8 series**, NAV and benchmark included (Deviation 3). Should it carry the fund book series only?
5. **Chart and format details** (Deviations 4, 11, 12 and 13):
   - `month_end` is `YYYY-MM`;
   - the exposures chart is 10 × 6 inches, with the returns-based line sampled at the holdings dates;
   - Chart 1 keeps its title.
6. **For the write-up:**
   - Jensen and Polen have a negative alpha below −2 HAC standard errors on both the book and the NAV series. Akre's alpha is not distinguishable from 0, and its book R² is low at 0.76.
   - The holdings-based IVV beta drifts from about 0.96 in 2019 to 1.04 to 1.11 from 2024 on. This was not investigated.

## git log origin/main --oneline -3

Captured after the push of the step commits, before this file and the review were committed:

```
dbd4e89 step 5.2: stock betas, holdings-based exposures and the exposures chart
8640da6 step 5.1: returns-based factor fits, Table 2, rolling betas and Chart 2
6771aea step 5.0: chart 1 shows total excess and labels units
```
