# Review — Section 9

## Section

Session 9, close-out (`instructions/09_closeout.md`). Wording and sourcing fixes to the README, 7 Akre-only `answers.csv` rows, and a `num3` format. No method changes. This is the last session of project 4.

Session 9b (`instructions/09b_closeout_fixes.md`) then fixed 3 rendering issues the session 9 questions raised: absolute-value formats for the FICO sentence, a stray comma, and `num4` for correlations.

## Steps completed

- 9.0 `answers.csv` rows of Section B, `test_answers_trace_to_source` extended to them, `num3`, template fixes C.1 to C.5, README re-rendered — `362ebb7`
- 9.1 `run_all.py` twice with `git status` clean, `docs/METHODS.md` row definition for `answers.csv`, fresh clone — `8c923c8`
- 9b.0 `abspct`, `abspp` and `num4` in `scripts/build_readme.py`, `num3` removed; template fixes B.1 to B.3; README re-rendered — `7c393a9`

## Evidence

### E.1 The new `answers.csv` rows, and the source rows behind them

Printed with `float_format="%.17g"`, each CSV read with `float_precision="round_trip"`, so the digits are those in the files.

#### The 7 new `answers.csv` rows

```
    question  fund                  figure                value  interval_lo  interval_hi      source_table                            source_row
75         1  akre         selection_BusEq   -1.245879928202422          NaN          NaN            linked  fund=akre,method=carino,bucket=BusEq
76         1  akre       interaction_BusEq  0.78167253604031184          NaN          NaN            linked  fund=akre,method=carino,bucket=BusEq
77         1  akre        other_weight_min  0.34021406991612529          NaN          NaN           buckets      entity=akre,bucket=Other,t=1..28
78         1  akre        other_weight_max    0.562230625474051          NaN          NaN           buckets      entity=akre,bucket=Other,t=1..28
79         3  akre  fico_weight_2026_06_30 0.084651154606920562          NaN          NaN  position_returns          entity=akre,t=28,ticker=FICO
80         3  akre     fico_return_2026_09 -0.48355576496305996          NaN          NaN          adjclose             ticker=FICO,month=2026-09
81         3  akre   active_return_2026_09 -0.13277795584864938          NaN          NaN      book_monthly         entity=akre|ivv,month=2026-09
```

#### `linked.csv`, Akre BusEq

```
    fund    method bucket           allocation           selection         interaction                total
5   akre    carino  BusEq -0.29367380017177058  -1.245879928202422 0.78167253604031184 -0.75788119233388085
20  akre  menchero  BusEq -0.31621473329467309 -1.2979714187831335 0.80974248566784657  -0.8044436664099599
```

#### `buckets.csv`, Akre Other, 28 quarters

```
    entity   t bucket              weight                      r
11    akre   1  Other 0.34021406991612535    0.11972776724175499
25    akre   2  Other 0.36746462342981323   -0.14456490173039552
39    akre   3  Other 0.38297206157280089    0.22665696035893074
53    akre   4  Other 0.39387958825408764    0.10774008520550277
67    akre   5  Other 0.40736557129226875   0.068928723162837838
81    akre   6  Other 0.41730030205143176 -0.0039566890830929988
95    akre   7  Other 0.41842954136818622   0.090815328786850308
109   akre   8  Other 0.38278807153335559  -0.026075689680772198
123   akre   9  Other 0.37206329145888029   0.029034866656239562
137   akre  10  Other 0.36032195161917557  -0.063797036548526989
151   akre  11  Other 0.40212656484519982   -0.13732311059100033
165   akre  12  Other 0.38972186215918947  -0.077141959506407759
179   akre  13  Other  0.3964101052852449    0.17771486034098805
193   akre  14  Other 0.47059843425639869   0.054919528232036517
207   akre  15  Other 0.48257540451903469    0.11438642344114891
221   akre  16  Other 0.49569907612775643  -0.044531641393969194
235   akre  17  Other 0.51311393825672114    0.14140778552143665
249   akre  18  Other 0.46885926667198297   0.077702097891707705
263   akre  19  Other 0.47330575971796307  -0.048737340527536685
277   akre  20  Other 0.45835214307979255   0.091474242544433912
291   akre  21  Other 0.45277959019214448   0.044867965370972297
305   akre  22  Other  0.4719874736326396   0.039565568319553455
319   akre  23  Other 0.49605639865444351   0.039486691447963143
333   akre  24  Other 0.52496645882310644  -0.014221207646608209
347   akre  25  Other 0.54004748355628929   0.010074471409062744
361   akre  26  Other   0.562230625474051   -0.18175592099622231
375   akre  27  Other 0.52999831548927456   0.024730345209785096
389   akre  28  Other 0.56005959315620824  -0.038260386339903051
```

#### POSITION_RETURNS, Akre t=28 (holdings 2026-06-30), FICO

```
    entity   t      cusip     sec_id issuer6 ticker bucket               weight                    r  delisted_in_quarter last_price_date
584   akre  28  303250104  303250104  303250   FICO  Other 0.084651154606920562 -0.50411794960132361                False      2026-09-30
```

#### FICO month-end adjusted closes, `adjclose.parquet`

```
                     FICO
date                     
2026-07 1122.969970703125
2026-08   1147.2099609375
2026-09  592.469970703125
```

#### `book_monthly.csv`, 2026-09

```
     entity    month                    ret
83     akre  2026-09   -0.13673949146210107
167  jensen  2026-09  -0.027735380491708095
251   polen  2026-09  -0.025068731161790425
335     ivv  2026-09 -0.0039615356134516944
419     iwf  2026-09    0.02149068821233624
```

#### `gate.csv` correlations, printed with num3 in the README

```
     fund                corr
0    akre 0.99002831574664885
1  jensen 0.99960561212591381
2   polen 0.99818433624530201
```


Checks against the rows above:

- `selection_BusEq` and `interaction_BusEq` are the `selection` and `interaction` cells of the Carino BusEq row.
- `other_weight_min` is t=1 (0.3402…), `other_weight_max` is t=26 (0.5622…). The min differs from t=1's cell in the 17th digit (…529 against …535): `answers()` reads `buckets.csv` with `pd.read_csv`'s default float parser, as it reads every other source table for the 75 session 8 rows. The difference is 1 ulp, under the test's 1e-15. See Deviations, item 6.
- `fico_weight_2026_06_30` is the FICO row's `weight` at t=28, the quarter that starts from the 2026-06-30 book.
- `fico_return_2026_09` = 592.469970703125 / 1147.2099609375 − 1 = −0.48355576496305996.
- `active_return_2026_09` = −0.13673949146210107 − (−0.0039615356134516944) = −0.13277795584864938.

### E.2 `README.md` against `8c546bc`, in full

```diff
diff --git a/README.md b/README.md
index f00d4fd..60d2ba4 100644
--- a/README.md
+++ b/README.md
@@ -10,11 +10,11 @@ Everything is built from free public data: SEC EDGAR filings, the OpenFIGI mappi
 
 **Allocation, selection and interaction.** Every fund trailed its benchmark over the 28 quarters to September 2026. Akre's book returned 7.2% a year against 16.3% for IVV, a cumulative excess return D of −124.9 pp. Jensen's returned 10.7% against the same 16.3% (D of −84.2 pp), and Polen's 9.8% against 18.8% for IWF (D of −141.5 pp). Selection, not allocation, carried most of it for Akre and Polen. Linked with Carino, Akre's selection is −130.4 pp against allocation of −55.1 pp, and Polen's is −135.6 pp against −23.2 pp. Jensen's loss is also selection, −68.0 pp, with allocation of 2.4 pp. The mean quarterly selection effect is −2.25% for Akre and −1.88% for Polen, and both bootstrap intervals are entirely negative (−3.74% to −0.95%, and −2.74% to −0.97%). Jensen's mean quarterly selection of −1.10% has an interval of −2.32% to 0.11%, which reaches into positive values, so this sample cannot distinguish Jensen's selection from no effect. Only Akre's allocation interval is entirely negative (−1.63% to −0.15%).
 
-**Factors.** Jensen's alpha is −0.32% a month on the book, with a HAC t of −2.23, and −0.36% on the NAV, with a t of −2.42. Polen's is −0.40% on the book (t of −2.06) and −0.52% on the NAV (t of −2.59). Akre's alpha of −0.46% a month on the book (t of −1.39, interval −0.99% to 0.08%) cannot be told apart from no alpha. Its R² of 0.76, against 0.92 for Jensen and 0.93 for Polen, says most of Akre's active risk is stock-specific: its residual volatility is 10.0% a year. Market betas on the book are 0.96 for Akre, 0.88 for Jensen and 1.04 for Polen. Akre's exposures drifted the most: from 2025 its value loading climbed and its investment loading fell away, in both its returns and its holdings (Akre's rolling beta and exposure charts below).
+**Factors.** Jensen's alpha is −0.32% a month on the book, with a HAC t of −2.23, and −0.36% on the NAV, with a t of −2.42. Polen's is −0.40% on the book (t of −2.06) and −0.52% on the NAV (t of −2.59). Akre's alpha of −0.46% a month on the book (t of −1.39, interval −0.99% to 0.08%) cannot be told apart from no alpha. Its R² of 0.76, against 0.92 for Jensen and 0.93 for Polen, says most of Akre's active risk is stock-specific: its residual volatility is 10.0% a year. Market betas on the book are 0.96 for Akre, 0.88 for Jensen and 1.04 for Polen. Akre's exposures drifted the most: from 2025 its value loading climbed and its investment loading fell away, (Akre's rolling beta chart below).
 
-**Active risk.** At 2026-06-30 Akre's active share against IVV was 97.4% and its ex-ante tracking error 13.5%. Jensen's were 61.6% and 5.8%, and Polen's against IWF 61.8% and 8.4%. A few positions carry most of that risk for Akre and Polen: the top positions in each tracking error chart below explain 76.1% of Akre's ex-ante tracking error and 76.5% of Polen's, against 36.5% of Jensen's. Akre's largest single contribution is a position it holds, MA at 1.5 pp. Polen's and Jensen's are names they do not own: NVDA at 1.7 pp and MU at 0.7 pp. Realised tracking error over 84 months is 11.4% for Akre, above its ex-ante mean of 8.8%. The reason is September 2026, the largest active month in the sample: FICO, one of Akre's largest positions, collapsed after the FHFA's September order letting every GSE lender use VantageScore, and the book fell far more than IVV that month. Jensen's and Polen's realised figures, 5.3% and 6.6%, sit close to their ex-ante means of 5.3% and 6.7%.
+**Active risk.** At 2026-06-30 Akre's active share against IVV was 97.4% and its ex-ante tracking error 13.5%. Jensen's were 61.6% and 5.8%, and Polen's against IWF 61.8% and 8.4%. A few positions carry most of that risk for Akre and Polen: the top positions in each tracking error chart below explain 76.1% of Akre's ex-ante tracking error and 76.5% of Polen's, against 36.5% of Jensen's. Akre's largest single contribution is a position it holds, MA at 1.5 pp. Polen's and Jensen's are names they do not own: NVDA at 1.7 pp and MU at 0.7 pp. Realised tracking error over 84 months is 11.4% for Akre, above its ex-ante mean of 8.8%. The reason is September 2026, the largest active month in the sample: FICO, 8.5% of Akre's book at 2026-06-30, fell −48.4% in the month after the FHFA's September 2026 order letting every GSE lender use VantageScore, and the book trailed IVV by −13.3 pp that month. Jensen's and Polen's realised figures, 5.3% and 6.6%, sit close to their ex-ante means of 5.3% and 6.7%.
 
-**The book against the NAV.** The quarter-start book tracks the fund's NAV closely for all of them: the correlation of quarterly book and NAV returns is 0.99 for Akre, 1.00 for Jensen and 1.00 for Polen. Polen's filing mixes strategies, ETFs included, and its book still tracks the fund's NAV at 1.00. Every mean gap is positive: the book beat the NAV by 0.16% a quarter for Akre, 0.21% for Jensen and 0.39% for Polen. That is the sign fees and cash predict, since the NAV pays fees and holds cash that the book does not. Jensen's and Polen's bootstrap intervals are entirely positive; Akre's runs from −0.07% to 0.39%. The gap's annualised tracking error is 0.59% for Jensen, 1.31% for Polen and 2.79% for Akre.
+**The book against the NAV.** The quarter-start book tracks the fund's NAV closely for all of them: the correlation of quarterly book and NAV returns is 0.990 for Akre, 1.000 for Jensen and 0.998 for Polen. Polen's filing mixes strategies, ETFs included, and its book still tracks the fund's NAV at 0.998. Every mean gap is positive: the book beat the NAV by 0.16% a quarter for Akre, 0.21% for Jensen and 0.39% for Polen. That is the sign fees and cash predict, since the NAV pays fees and holds cash that the book does not. Jensen's and Polen's bootstrap intervals are entirely positive; Akre's runs from −0.07% to 0.39%. The gap's annualised tracking error is 0.59% for Jensen, 1.31% for Polen and 2.79% for Akre.
 
 ## Results
 
@@ -28,7 +28,7 @@ Table 1 gives the linked totals over the 28 quarters in percentage points. Alloc
 | Jensen | 2.4 pp | −68.0 pp | −18.6 pp | −84.2 pp | −84.2 pp |
 | Polen | −23.2 pp | −135.6 pp | 17.3 pp | −141.5 pp | −141.5 pp |
 
-Akre's selection loss sits almost entirely in BusEq. Its BusEq names (Roper, Danaher, CCC and Verisk) did far worse than IVV's BusEq, which is mega-cap technology. Its large positive interaction comes from its weight in FF12 Other (Mastercard, Visa and Moody's), which is weight it does not hold in BusEq: an underweight in a bucket where selection lost gives a positive interaction. Every bucket of every fund is in `outputs/tables/linked.csv`, with the Menchero linking beside Carino.
+Akre's selection loss sits almost entirely in BusEq. Its BusEq names (Roper, Danaher, CCC and Verisk) did far worse than IVV's BusEq, which is mega-cap technology. Its large positive interaction sits in BusEq too: Akre held far less BusEq than IVV, and an underweight in a bucket where the fund's own picks lost gives a positive interaction (78.2 pp, against −124.6 pp of selection). Its weight in FF12 Other, 34.0% to 56.2% of the book, is Mastercard, Visa, Moody's, FICO and CoStar. Every bucket of every fund is in `outputs/tables/linked.csv`, with the Menchero linking beside Carino.
 
 Akre's selection slides from 2024 and allocation follows it down, with selection ending at −130.4 pp.
 
@@ -56,7 +56,7 @@ Akre's rolling betas show the drift: its value (HML) loading climbs through 2025
 
 ![Akre: rolling factor betas](outputs/figures/akre_rolling_betas.png)
 
-The holdings-based exposures, built from each stock's own 36-month betas, follow the returns-based line, so the drift comes from what Akre holds.
+The holdings-based exposures, built from each stock's own 36-month betas, follow the returns-based line, which is what you would expect, since both use the same 36 months of returns (see Data and method limits).
 
 ![Akre: holdings-based against returns-based exposures](outputs/figures/akre_exposures_hb_vs_rb.png)
 
@@ -88,9 +88,9 @@ Table 4 gives the gate for each fund: the correlation of quarterly book and NAV
 
 | Fund | Correlation | Passes | Quarters | Mean gap | Std of gap | Mean abs gap | TE of gap | Mean gap, bootstrap interval |
 | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
-| Akre | 0.99 | Yes | 26 | 0.16% | 1.39% | 1.07% | 2.79% | −0.07% to 0.39% |
-| Jensen | 1.00 | Yes | 28 | 0.21% | 0.29% | 0.27% | 0.59% | 0.14% to 0.29% |
-| Polen | 1.00 | Yes | 28 | 0.39% | 0.66% | 0.53% | 1.31% | 0.27% to 0.52% |
+| Akre | 0.990 | Yes | 26 | 0.16% | 1.39% | 1.07% | 2.79% | −0.07% to 0.39% |
+| Jensen | 1.000 | Yes | 28 | 0.21% | 0.29% | 0.27% | 0.59% | 0.14% to 0.29% |
+| Polen | 0.998 | Yes | 28 | 0.39% | 0.66% | 0.53% | 1.31% | 0.27% to 0.52% |
 
 ## Use it on your own holdings
 
```

### E.3 `run_all.py` twice, step 9.1

Both runs, at `362ebb7` plus the uncommitted `docs/METHODS.md` edit, printed `section 1` to `section 8: all checks passed` and exited 0. `git status --short` after each:

```
run 1 exit 0
git status after run 1:
 M docs/METHODS.md
run 2 exit 0
git status after run 2:
 M docs/METHODS.md
```

The only change is the hand edit to `docs/METHODS.md`, which `run_all.py` does not write. Every regenerated table, PNG, PDF and the README were byte-identical to the commit.

### E.4 Session 9b: `README.md` against `45d02d0`, in full

```diff
diff --git a/README.md b/README.md
index 60d2ba4..f03fb5f 100644
--- a/README.md
+++ b/README.md
@@ -10,11 +10,11 @@ Everything is built from free public data: SEC EDGAR filings, the OpenFIGI mappi
 
 **Allocation, selection and interaction.** Every fund trailed its benchmark over the 28 quarters to September 2026. Akre's book returned 7.2% a year against 16.3% for IVV, a cumulative excess return D of −124.9 pp. Jensen's returned 10.7% against the same 16.3% (D of −84.2 pp), and Polen's 9.8% against 18.8% for IWF (D of −141.5 pp). Selection, not allocation, carried most of it for Akre and Polen. Linked with Carino, Akre's selection is −130.4 pp against allocation of −55.1 pp, and Polen's is −135.6 pp against −23.2 pp. Jensen's loss is also selection, −68.0 pp, with allocation of 2.4 pp. The mean quarterly selection effect is −2.25% for Akre and −1.88% for Polen, and both bootstrap intervals are entirely negative (−3.74% to −0.95%, and −2.74% to −0.97%). Jensen's mean quarterly selection of −1.10% has an interval of −2.32% to 0.11%, which reaches into positive values, so this sample cannot distinguish Jensen's selection from no effect. Only Akre's allocation interval is entirely negative (−1.63% to −0.15%).
 
-**Factors.** Jensen's alpha is −0.32% a month on the book, with a HAC t of −2.23, and −0.36% on the NAV, with a t of −2.42. Polen's is −0.40% on the book (t of −2.06) and −0.52% on the NAV (t of −2.59). Akre's alpha of −0.46% a month on the book (t of −1.39, interval −0.99% to 0.08%) cannot be told apart from no alpha. Its R² of 0.76, against 0.92 for Jensen and 0.93 for Polen, says most of Akre's active risk is stock-specific: its residual volatility is 10.0% a year. Market betas on the book are 0.96 for Akre, 0.88 for Jensen and 1.04 for Polen. Akre's exposures drifted the most: from 2025 its value loading climbed and its investment loading fell away, (Akre's rolling beta chart below).
+**Factors.** Jensen's alpha is −0.32% a month on the book, with a HAC t of −2.23, and −0.36% on the NAV, with a t of −2.42. Polen's is −0.40% on the book (t of −2.06) and −0.52% on the NAV (t of −2.59). Akre's alpha of −0.46% a month on the book (t of −1.39, interval −0.99% to 0.08%) cannot be told apart from no alpha. Its R² of 0.76, against 0.92 for Jensen and 0.93 for Polen, says most of Akre's active risk is stock-specific: its residual volatility is 10.0% a year. Market betas on the book are 0.96 for Akre, 0.88 for Jensen and 1.04 for Polen. Akre's exposures drifted the most: from 2025 its value loading climbed and its investment loading fell away (Akre's rolling beta chart below).
 
-**Active risk.** At 2026-06-30 Akre's active share against IVV was 97.4% and its ex-ante tracking error 13.5%. Jensen's were 61.6% and 5.8%, and Polen's against IWF 61.8% and 8.4%. A few positions carry most of that risk for Akre and Polen: the top positions in each tracking error chart below explain 76.1% of Akre's ex-ante tracking error and 76.5% of Polen's, against 36.5% of Jensen's. Akre's largest single contribution is a position it holds, MA at 1.5 pp. Polen's and Jensen's are names they do not own: NVDA at 1.7 pp and MU at 0.7 pp. Realised tracking error over 84 months is 11.4% for Akre, above its ex-ante mean of 8.8%. The reason is September 2026, the largest active month in the sample: FICO, 8.5% of Akre's book at 2026-06-30, fell −48.4% in the month after the FHFA's September 2026 order letting every GSE lender use VantageScore, and the book trailed IVV by −13.3 pp that month. Jensen's and Polen's realised figures, 5.3% and 6.6%, sit close to their ex-ante means of 5.3% and 6.7%.
+**Active risk.** At 2026-06-30 Akre's active share against IVV was 97.4% and its ex-ante tracking error 13.5%. Jensen's were 61.6% and 5.8%, and Polen's against IWF 61.8% and 8.4%. A few positions carry most of that risk for Akre and Polen: the top positions in each tracking error chart below explain 76.1% of Akre's ex-ante tracking error and 76.5% of Polen's, against 36.5% of Jensen's. Akre's largest single contribution is a position it holds, MA at 1.5 pp. Polen's and Jensen's are names they do not own: NVDA at 1.7 pp and MU at 0.7 pp. Realised tracking error over 84 months is 11.4% for Akre, above its ex-ante mean of 8.8%. The reason is September 2026, the largest active month in the sample: FICO, 8.5% of Akre's book at 2026-06-30, fell 48.4% in the month after the FHFA's September 2026 order letting every GSE lender use VantageScore, and the book trailed IVV by 13.3 pp that month. Jensen's and Polen's realised figures, 5.3% and 6.6%, sit close to their ex-ante means of 5.3% and 6.7%.
 
-**The book against the NAV.** The quarter-start book tracks the fund's NAV closely for all of them: the correlation of quarterly book and NAV returns is 0.990 for Akre, 1.000 for Jensen and 0.998 for Polen. Polen's filing mixes strategies, ETFs included, and its book still tracks the fund's NAV at 0.998. Every mean gap is positive: the book beat the NAV by 0.16% a quarter for Akre, 0.21% for Jensen and 0.39% for Polen. That is the sign fees and cash predict, since the NAV pays fees and holds cash that the book does not. Jensen's and Polen's bootstrap intervals are entirely positive; Akre's runs from −0.07% to 0.39%. The gap's annualised tracking error is 0.59% for Jensen, 1.31% for Polen and 2.79% for Akre.
+**The book against the NAV.** The quarter-start book tracks the fund's NAV closely for all of them: the correlation of quarterly book and NAV returns is 0.9900 for Akre, 0.9996 for Jensen and 0.9982 for Polen. Polen's filing mixes strategies, ETFs included, and its book still tracks the fund's NAV at 0.9982. Every mean gap is positive: the book beat the NAV by 0.16% a quarter for Akre, 0.21% for Jensen and 0.39% for Polen. That is the sign fees and cash predict, since the NAV pays fees and holds cash that the book does not. Jensen's and Polen's bootstrap intervals are entirely positive; Akre's runs from −0.07% to 0.39%. The gap's annualised tracking error is 0.59% for Jensen, 1.31% for Polen and 2.79% for Akre.
 
 ## Results
 
@@ -88,9 +88,9 @@ Table 4 gives the gate for each fund: the correlation of quarterly book and NAV
 
 | Fund | Correlation | Passes | Quarters | Mean gap | Std of gap | Mean abs gap | TE of gap | Mean gap, bootstrap interval |
 | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
-| Akre | 0.990 | Yes | 26 | 0.16% | 1.39% | 1.07% | 2.79% | −0.07% to 0.39% |
-| Jensen | 1.000 | Yes | 28 | 0.21% | 0.29% | 0.27% | 0.59% | 0.14% to 0.29% |
-| Polen | 0.998 | Yes | 28 | 0.39% | 0.66% | 0.53% | 1.31% | 0.27% to 0.52% |
+| Akre | 0.9900 | Yes | 26 | 0.16% | 1.39% | 1.07% | 2.79% | −0.07% to 0.39% |
+| Jensen | 0.9996 | Yes | 28 | 0.21% | 0.29% | 0.27% | 0.59% | 0.14% to 0.29% |
+| Polen | 0.9982 | Yes | 28 | 0.39% | 0.66% | 0.53% | 1.31% | 0.27% to 0.52% |
 
 ## Use it on your own holdings
 
```

### E.5 Session 9b: `run_all.py` after step 9b.0

Before the commit, 1 run of `run_all.py` printed `section 1` to `section 8: all checks passed`, and `git status --short` listed only the 3 hand-edited files (`README.md`, `docs/README_template.md`, `scripts/build_readme.py`). After committing `7c393a9`, a 2nd run also passed all 8 sections, and `git status --short` printed nothing:

```
run_all exit 0
git status --short:
(end)
```

## Tests run

```
$ .venv/Scripts/python -m pytest -p socket --disable-socket -q     # at 8c923c8
........................................................................ [ 85%]
............                                                             [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\Utkarsh\10. Quant Projects\6) Attribution Engine On Real Holdings\repo-clone\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
84 passed, 1 warning in 45.97s
```

Session 9b, at `7c393a9`'s tree before the commit (the same 3 files):

```
$ .venv/Scripts/python -m pytest -p socket --disable-socket -q
........................................................................ [ 85%]
............                                                             [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\Utkarsh\10. Quant Projects\6) Attribution Engine On Real Holdings\repo-clone\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
84 passed, 1 warning in 61.90s (0:01:01)
```

## Fresh-clone check

```
$ git clone https://github.com/uty101/Attribution-Engine-On-Real-Holdings.git /c/fc9
$ cd /c/fc9 && git log --oneline -1
8c923c8 step 9.1: final run and fresh clone
$ uv venv --python 3.12
$ uv pip install -r requirements-lock.txt
$ uv pip install -e . --no-deps
$ .venv/Scripts/python -m pytest -p socket --disable-socket -q
........................................................................ [ 85%]
............                                                             [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\fc9\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
84 passed, 1 warning in 105.33s (0:01:45)
```

The clone has no `data/processed/` (gitignored), so the `fico_weight_2026_06_30` check rebuilt the 2026-06-30 Akre book from `data/raw/` through `real_risk_inputs`, as rule 7 requires.

## Runtime per step

- 9.0: `run_all.py` 78 s; test suite 52 s.
- 9.1: `run_all.py` about 75 s per run, 2 runs; local suite 47 s; fresh-clone suite 105 s, plus install.

## Deviations from PLAN.md

1. **7 rows, not 6.** E.1 asks for "the 6 new `answers.csv` rows", but Section B's table has 6 lines, one of which (`other_weight_min`, `other_weight_max`) is 2 figures, and Section A answer 2 says "the 2 `answers.csv` rows". `answers.csv` now has 75 + 7 = 82 rows, and the test asserts `25 × 3 + 7`.
2. **Where the rows go.** Section B does not say. They follow the 75 per-fund rows, in Section B's order, so the session 8 rows keep their positions. The test also asserts the last 7 rows are Akre's.
3. **Source names that are not `outputs/tables/` files.** `source_table` is `position_returns` (rebuilt into `data/processed/`) and `adjclose` (`data/raw/prices/adjclose.parquet`), the names Section B gives. The test leaves both out of the tables it reads from `outputs/tables/` and recomputes them: FICO's weight from `real_risk_inputs("akre", "2026-06-30")["posP"]`, FICO's return from `monthly_returns(load_prices(...))`. `posP` comes from `book_quarter` without the `quarter_return` overrides, which change `r` and never `weight`.
4. **`source_row` key shapes.** `t=28` for FICO's weight, since POSITION_RETURNS has `t` and no holdings date. `t=1..28` for the Other range, like the existing `book_quarterly` rows. `entity=akre|ivv,month=2026-09` for the active return, like `cum_excess_D`.
5. **The BusEq figures are Carino-linked**, as Section B says: −124.6 pp selection and +78.2 pp interaction. Section A's −0.603 and +0.376 are summed quarterly effects, which is a different measure, so the README numbers do not match those.
6. **1-ulp parsing.** See E.1. The new rows read their source CSVs the same way the session 8 rows do, and all agree to within 1e-15.
7. **`docs/METHODS.md`.** The `answers.csv` paragraph said "rows for every fund that passed the gate". That row definition has changed, so 1 sentence now lists the 7 Akre-only rows and their sources. No format is stated there, so nothing about `num3` was needed.

8. **Session 9b: `num3` removed.** After B.3, nothing used `num3`, so it was taken out of `fmt` as B.3 says. `num2` stays, since Table 2 and the Factors paragraph use it for R² and betas.
9. **Session 9b: the review file.** Instruction 09b asks for evidence but names no review file. As the 01b, 02b and 02c sessions did, it goes into this section's file, `review/section_9.md` (E.4, E.5 and the 9b test output).

## Not verified

- `ruff` is not installed in the project venv, so no lint was run. The suite and `run_all.py` both import the changed modules.
- The README was read as Markdown here, not on GitHub's renderer.

## Open questions

Section C was applied word for word. When rendered, 3 of the replacements read badly. None was changed, because changing them would be a wording choice:

1. **C.4 double negatives.** The README now says "fell −48.4%" and "trailed IVV by −13.3 pp". Should these be "fell 48.4%" and "by 13.3 pp", using absolute-value formats or reworded placeholders, or kept as they are?
2. **C.3 stray comma.** C.3 replaces only the text after "fell away, ", so the sentence now ends "…its investment loading fell away, (Akre's rolling beta chart below)." Should the comma be dropped?
3. **Jensen's correlation prints as 1.000.** It is 0.99961, and `num3` rounds it to 1.000, the same issue that question 4 raised for Polen under `num2`. Keep it as is?

Session 9b: none. Instruction 09b answered all 5 session 9 questions, and its fixes are applied as written.

## Files changed

```
 README.md                  | 16 ++++++++--------
 docs/METHODS.md            |  2 +-
 docs/README_template.md    | 10 +++++-----
 outputs/tables/answers.csv |  7 +++++++
 scripts/build_readme.py    |  8 +++++---
 scripts/run_all.py         | 35 +++++++++++++++++++++++++++++++++++
 tests/test_answers.py      | 37 +++++++++++++++++++++++++++++++++----
```

Plus this file and `instructions/09_closeout.status.md`.

Session 9b (`7c393a9`):

```
 README.md               | 12 ++++++------
 docs/README_template.md |  6 +++---
 scripts/build_readme.py | 15 ++++++++++-----
```

Plus this file and `instructions/09b_closeout_fixes.status.md`.

## Reviewer reads

Session 9b: E.4, the README diff, then E.5.

Session 9:

1. E.2, the README diff.
2. Open questions 1 to 3.
3. E.1, the 7 rows and their source rows.
4. `scripts/run_all.py`, `akre_rows`.
5. `tests/test_answers.py`, the new branches.
