# instructions/05_section_5.md — Session 5: Section 5, Factor attribution

Pull `main` first. Precedence (rule 13): this file beats `CLAUDE.md` amendments and `PLAN.md`, which beat the kickoff.

---

## A. Section 4: approved

What the reviewer checked independently, from a clone of `2d788b3`, on Linux with Python 3.12:

1. **Brinson and Carino from scratch.** The reviewer's own code started from `buckets.csv` and `book_quarterly.csv`. It applied the Convention 4.11 fills, checked the identity in every fund-quarter, and linked with its own Carino. The Totals match `linked.csv` to the 2nd decimal of a percentage point for all 3 funds:

   | fund | allocation | selection | interaction |
   |---|---|---|---|
   | Akre | −55.06 | −130.44 | +60.59 |
   | Jensen | +2.39 | −67.99 | −18.60 |
   | Polen | −23.17 | −135.59 | +17.28 |

2. **The headline numbers are plausible.** The cumulative book returns over the 28 quarters are:

   | book | cumulative | annualised |
   |---|---|---|
   | Akre | +62.4% | 7.2% |
   | Jensen | +103.1% | 10.7% |
   | Polen | +92.5% | 9.8% |
   | IVV | +187.3% | 16.3% |
   | IWF | +234.0% | 18.8% |

   All 3 funds lagged badly, which matches their public record over 2021 to 2026. D of −125 pp for Akre is cumulative returns compounding apart, not a bug.
3. **Akre's large interaction (+60.6 pp)** comes from holding 39% to 56% in FF12 Other (Mastercard, Moody's, Visa, FICO and CoStar) against a small Other weight in IVV. With 12 coarse buckets, a fund this concentrated in one bucket pushes a lot into interaction. The write-up must say so; nothing to fix.

Answers to the session 4 questions:

1. **The `idx` keyword on `bootstrap_mean`.** Accepted.
2. **The `zero_tol` keyword and the 1e-24 module constant.** Accepted.
3. **`rP` and `rB` in `brinson_quarterly.csv`.** Keep them filled, because those are the values that entered the formula. Add a boolean column `filled` (true where Convention 4.11 supplied the value), placed after `rB`.
4. **Chart 1.** Accepted, with the fix in step 5.0.
5. **The step 4.0 commit.** Accepted.
6. **Keeping `test_equal_period_uses_limit`.** Accepted, and correctly reasoned.
7. **The Other bucket and JGRW.** Noted for the write-up.

---

## B. Step 5.0: Chart 1 fix (new)

Commit `step 5.0: chart 1 shows total excess and labels units`.

1. Add a 3rd line: the cumulative excess return D_k = R_P,k − R_B,k, where R_P,k and R_B,k compound quarters 1 to k. Draw it in black, dashed, labelled "Total excess (D)". Without it, a reader sees selection at −130 and cannot tell it is measured against a D of −125.
2. Y label: "Percentage points of cumulative return".
3. Add the `filled` column to `brinson_quarterly.csv` (Section A, answer 3).
4. Rerun `run_all.py --section 4`. Every check must still pass.

---

## C. Decisions for Section 5

| item | decision | reason |
|---|---|---|
| Monthly sample | October 2019 to August 2026, the last French month: 83 months | Kickoff 3.3 |
| Series | `{fund}_book` and `{fund}_nav` for the 3 funds; `ivv_book` and `iwf_book` | D-22 |
| Missing months | Rows with a missing return are dropped before the regression. Akre's NAV series loses 2025-08 to 2025-10, so 80 months. `n_months` records the count. | D-33 |
| OLS call | `statsmodels.api.OLS(y, sm.add_constant(X)).fit(cov_type="HAC", cov_kwds={"maxlags": 3})`, every other argument at its default. Factor order: mkt, smb, hml, rmw, cma, umd. | One exact call, so the HAC test is meaningful |
| Rolling betas | Book series only (D-23), on windows of 36 consecutive months with no missing month, plain OLS. A window is dated by its last month. 48 windows per series, from 2022-09 to 2026-08. | |
| Table 2 by year | Calendar years 2019 (3 months) to 2026 (8 months). Add a column `n_months` after `year`, so partial years are visible. | Without it, 2019 and 2026 look like full years |
| Stock betas | For each holdings date h, the window is the 36 calendar months ending at h's month. Use the stock's monthly excess returns (month-end adjusted close, minus RF). At least 24 non-missing months, else the FF12 bucket mean of stocks with valid betas at h on the same side. | Kickoff 5.8 |
| Stock universe at h | Every priced, mapped position in the fund and its benchmark at h | |
| Holdings exposures | Weights renormalised over priced, mapped positions with a beta (own or bucket fallback). Unpriced and unmapped weight is reported beside each row in a column `excluded_weight`. | |
| Chart 2 | Per fund, 6 lines of rolling book betas against window end, with a zero line. Title "{Fund}: rolling 36-month factor betas (book)". Y label "Beta". Size 8 × 4.5 inches. | |
| Exposures chart | 2 × 3 panels, 1 per factor. Holdings-based fund exposure at each h (markers), and the rolling returns-based beta whose window ends at h's month (line, where it exists). | |

---

## D. Amendments to Section 5 steps

### 5.1
- `test_recovers_known_betas`. 120 synthetic months: factors drawn from `default_rng(run.bootstrap_seed)` standard normal × 0.04; y = 0.002 + X·(1.0, 0.3, −0.2, 0.1, 0.05, −0.15) with no noise. The coefficients are recovered to 1e-10.
- `test_hac_matches_statsmodels`: the same synthetic data plus noise drawn from the same generator (×0.01), drawn after the factors. Standard errors equal a direct call made with the Section C OLS call, to 1e-12.
- `test_year_rows_sum`: for each year, the sum of the 6 contributions, alpha and residual equals the year's summed excess return to 1e-12.

### 5.2
- `test_min_obs_rule`: a synthetic stock with 23 months gets the bucket mean; one with 24 gets its own beta.
- `test_bucket_fallback`: the fallback beta equals the mean of the same-bucket valid betas, on the same side.
- **Sanity check (report, not a test):** the holdings-based market beta of `ivv_book` at every h, and the full-sample returns-based `ivv_book` market beta. Both should be close to 1. Print both.

---

## E. Review evidence

1. `factor_fit.csv` in full.
2. Per series: R², annualised residual volatility, alpha per month with its HAC t-stat, and n_months.
3. Table 2 (`factor_by_year.csv`) for each fund's book series.
4. For each fund at h = 2019-09-30, 2022-12-31 and 2026-06-30: the holdings-based fund, benchmark and active exposures, with `excluded_weight`.
5. The IVV sanity check in Section D, 5.2.
6. Chart 1 (fixed), Chart 2 and the exposures chart for every fund, as embedded PNGs.
7. Full test output, then the fresh-clone check against GitHub.

---

## F. End of session

Status file: `instructions/05_section_5.status.md`, per rule 11. Push the step commits, run the fresh-clone check against GitHub, then commit and push the review and status files.
