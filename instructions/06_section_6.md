# instructions/06_section_6.md — Session 6: Section 6, Risk

Pull `main` first. Precedence (rule 13): this file beats `CLAUDE.md` amendments and `PLAN.md`, which beat the kickoff.

---

## A. Section 5: approved

What the reviewer checked independently, from a clone of `7eea637`, on Linux with Python 3.12:

1. **All 8 factor fits.** The reviewer's own regressions started from `book_monthly.csv`, `nav_monthly.csv` and the French loader, with its own sample filter (2019-10 to 2026-08, missing months dropped). The alpha, its HAC t-stat, the market beta and R² match `factor_fit.csv` to every printed digit for all 8 series. For example, `jensen_book` has alpha −0.319% a month with t = −2.231, and `akre_nav` uses 80 months.
2. **Charts.** Chart 1 now shows D, and selection visibly tracks it for Polen. Chart 2 and the exposures chart read cleanly.
3. **A point the write-up must make.** Holdings-based and returns-based exposures agree closely in the exposures chart, partly by construction. Both use the same trailing 36 months: one regresses each stock, the other regresses the weighted sum of those same stocks. Agreement is therefore a consistency check, not independent confirmation. Where they part (Akre's RMW in 2026, its SMB in 2024 to 2025), turnover inside the window is the likely cause.
4. **IVV's holdings-based beta drifting from 0.96 to about 1.1** is consistent with the index's growing weight in high-beta mega-cap technology over 2023 to 2026. Noted for the write-up; it is not a defect.

Answers to the session 5 questions:

1. **`excluded_weight` including YETI** (at most 0.0099%). Accepted as defined; blank on active rows is fine.
2. **The constant named `alpha`.** Accepted.
3. **`resid_vol_ann`.** Change it to the regression standard error, which divides by n − 7 (n months, 7 parameters including the constant), × √12. Rename nothing. Document it in `docs/CONVENTIONS_RESOLVED.md`. `std_gap` in `gate.csv` stays at ddof 1, because it is not a regression residual.
4. **All 8 series in `factor_by_year.csv`.** Accepted. The README prints only the fund book rows.
5. **Chart and format details.** All accepted.
6. **Alphas.** Noted for the write-up. Jensen and Polen have alpha below −2 HAC standard errors on both book and NAV. Akre's alpha is indistinguishable from 0, with a low R² of 0.76: its active risk is mostly idiosyncratic.

---

## B. Step 6.0 (new)

Commit `step 6.0: residual volatility uses n − 7`. Apply answer 3, rerun `run_all.py --section 5`, and print the 8 old and new `resid_vol_ann` values in the review.

---

## C. Decisions for Section 6

| item | decision | reason |
|---|---|---|
| Issuer key for active share | SEC CIK from `security_map.csv`. A position with no CIK is its own issuer, keyed by `sec_id`. This is amendment 10, which supersedes `PLAN.md` 6.2's CUSIP-6. | ISIN rows have no CUSIP-6 |
| Active share weights | Convention 4.5 book weights, all positions, unmapped included (each its own issuer). Report `unmapped_weight_fund` and `unmapped_weight_bench` beside each row as 2 new columns after `active_share`. | Unmapped names cannot match across books, so they push AS up; the reader needs to see by how much |
| Risk weights | Priced, mapped positions only. Sum weights across `sec_id`s that share a `yf_ticker` within a book, then renormalise each side to 1 (Convention 4.18). | Prices are per ticker |
| Daily returns | Simple returns from `adjclose.parquet`, over the rows `pc.cov.window_daily(returns_d, q_start(h), 36)` returns, restricted to the union of the 2 books' tickers | Kickoff 5.10 |
| Fill | Kickoff 5.10 rule, using the FF12 bucket from `security_map.csv`. `max_fill_share` is the largest per-ticker fill share at h. | |
| Shrinkage and conditioning | `pc.cov.cov_lw_cc(X, ddof=0)`, then `pc.cov.condition_cov(S, risk.max_cond)`. `delta_lw` is the returned delta. `ridged` is true when the log's ridge > 0. | |
| TE and the Euler split | Kickoff 5.10. CTE is reported in annualised TE units, so that Σ CTE = TE. | |
| Realised TE | `outputs/tables/te_realised.csv` (D-25): per fund, std (ddof 1) of monthly book active returns (fund book minus its benchmark book) × √12 over the 83 months, the mean of the 28 ex-ante TEs, and n_months. | |
| Chart 3 | Horizontal bars: the 15 largest CTE positions by absolute value at h = 2026-06-30, labelled by ticker, in percentage points of annualised TE. Positive bars in 1 colour and negative in another, sorted, with a vertical zero line. Title "{Fund} vs {benchmark}: top 15 contributions to ex-ante tracking error, 2026-06-30"; subtitle giving TE and the share of TE the 15 explain. Size 8 × 6 inches. | |

---

## D. Amendments to Section 6 steps

### 6.1
- `test_cov_symmetric_positive_definite` runs on the real covariance for Akre at h = 2026-06-30, built from the committed raw data: symmetric to 1e-15 and smallest eigenvalue > 0.
- New `test_fill_share_bounds`: every fill share lies in [0, 1], and tickers with a full history in the window have share 0.

### 6.2
- `test_share_classes_net`: GOOG and GOOGL (same CIK) in different proportions across 2 books net to the issuer-level difference.
- New `test_te_matches_direct_quadratic`: TE from `te_decomposition` equals `sqrt(12 * a @ S @ a)` computed directly, to 1e-12, on the real Akre 2026-06-30 inputs.

---

## E. Review evidence

1. `risk_quarterly.csv` (Table 3) in full, with the 2 new columns.
2. `te_realised.csv` in full.
3. Per fund at h = 2026-06-30: the top 15 CTE rows (ticker, bucket, a, mcte, cte), and the share of TE they explain.
4. Per fund at h = 2026-06-30: the sector CTE sums, which must sum to TE.
5. Per fund: `delta_lw` range, count of ridged dates, and `max_fill_share` range over the 28 dates.
6. Chart 3 for each fund, as an embedded PNG.
7. The step 6.0 before-and-after values.
8. Full test output, then the fresh-clone check against GitHub.

---

## F. End of session

Status file: `instructions/06_section_6.status.md`, per rule 11. Push the step commits, run the fresh-clone check against GitHub, then commit and push the review and status files.
