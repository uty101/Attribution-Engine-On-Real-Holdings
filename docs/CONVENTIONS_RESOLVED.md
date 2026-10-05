# Conventions resolved

Each item is fixed by `instructions/00_kickoff.md` (Sections 2, 4 and 5). This file only lists them in one place.

1. **Holdings dated by period date.** A 13F or N-PORT book is the book at its period date. The 45-day filing lag is reported as a data fact and does not affect ex-post attribution.
2. **Equity rows only.** 13F: `sshPrnamtType` = SH and no `putCall`. N-PORT: `assetCat` = EC and `units` = NS. Everything else is dropped and its value reported.
3. **CUSIP aggregation.** CUSIPs are upper-cased; rows with the same 9-character CUSIP in one book are summed (value and shares); a CUSIP that is not 9 alphanumeric characters is reported and dropped.
4. **Amendment rule.** Start from the latest original 13F-HR; the latest 13F-HR/A RESTATEMENT replaces the book; each NEW HOLDINGS amendment filed after the book in use is appended. N-PORT: the latest NPORT-P by filing date for the period.
5. **Weights sum to 1 including Unmapped and Unpriced.** w_i = value_i / Σ value over all kept equity rows in the book.
6. **The 14 buckets.** The 12 FF12 industries in French's order (NoDur, Durbl, Manuf, Enrgy, Chems, BusEq, Telcm, Utils, Shops, Hlth, Money, Other), then Unmapped, then Unpriced.
7. **Adjusted close and ticker normalisation.** Adjusted close only; yfinance ticker = OpenFIGI ticker with `/` replaced by `-`.
8. **Position return and delisting rule.** r_i = P_i(end) / P_i(q_start) − 1; if prices end before the quarter end, the last close is used and the position is held as cash at 0 return; no price on q_start sends it to Unpriced.
9. **Neutral return for Unmapped and Unpriced.** Both earn the book's priced, mapped return, so the book return equals that return and r = Σ_s w_s r_s holds exactly.
10. **Sector return.** r_s = Σ_{i∈s} w_i r_i / Σ_{i∈s} w_i for each FF12 bucket with positive weight.
11. **Empty-bucket rules.** Fund weight 0: r_s^P := r_s^B. Benchmark weight 0: r_s^B := r_B. Both 0: the bucket contributes nothing.
12. **Monthly book returns.** Buy-and-hold value path from quarter start over priced, mapped positions, renormalised, delisted names flat after their last close; the 3 monthly returns compound to the quarterly book return to 1e-12.
13. **Calendar-month periods.** Monthly returns come from month-end adjusted closes on calendar periods, never `DateOffset` arithmetic.
14. **NAV return on the institutional class.** Quarterly and monthly NAV returns from yfinance adjusted close on AKRIX, JENIX and POLIX, net of fees.
15. **French percent to decimal and RF.** French data is divided by 100; rf is French's RF; excess return is return − RF for the same calendar month.
16. **Annualisation factors.** Monthly volatility × √12; monthly covariance × 12 for annual tracking error; daily covariance × 21 for monthly.
17. **Issuer-level active share.** Issuer = first 6 characters of the CUSIP, so share classes of one issuer net against each other.
18. **Risk weights renormalised.** Risk uses the priced, mapped positions of each book renormalised to 1 on each side; the excluded weight is reported next to every tracking error figure.
19. **Failed-gate handling.** A fund below 0.90 correlation keeps its Table 4 row and is excluded from Tables 1 to 3, Charts 1 to 3 and `answers.csv`, with a line saying why.
20. **13F units switch on filing date 2023-01-03.** `value_usd = value × 1000` for filings dated before 2023-01-03, else `value`; every book's median implied price must lie in [1, 5000].
21. **Carino and Menchero zero limits.** Carino: k_t = 1/(1 + r_P,t) when |d_t| < 1e-12, k = 1/(1 + R_P) when |D| < 1e-12. Menchero: M = (1 + R_P)^((T − 1)/T) when |D| < 1e-12; α_t = 0 when Σ d_t² < 1e-24.
22. **Project 3 functions and the pinned commit.** `pc.cov.cov_lw_cc`, `pc.cov.condition_cov`, `pc.cov.window_daily` and `pc.stats.stationary_bootstrap_indices` from commit 88e865d8202023cd495dd9866c49e6adbc9f4654; `pc.cov.estimate_cov` is not used.
23. **reportlab with invariant output.** Reports are built with reportlab and `invariant=1`; charts are PNGs with `metadata={"Software": None}`, so 2 builds are byte-identical.
24. **Annualised residual volatility.** `resid_vol_ann` in `factor_fit.csv` is the regression standard error, √(Σ ε̂_t² / (n − 7)) × √12, with n the months used and 7 the parameters (6 factors and the constant). `std_gap` in `gate.csv` stays at ddof 1, because the gap is not a regression residual (`instructions/06_section_6.md`, Section A, answer 3).
25. **Cross-platform determinism.** Byte-identical on one platform; across platforms, numeric outputs agree to 1e-10 relative. CSVs print every bit (`%.17g`), so BLAS and libm last-bit differences show up between operating systems; PNGs and PDFs differ at the byte level through font rasterisation (`instructions/07_section_7.md`, Section A, point 4, which names this item 24; 24 was already taken by step 6.0).
