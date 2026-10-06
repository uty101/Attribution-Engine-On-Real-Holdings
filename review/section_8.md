# Review — Section 8

## Section

Section 8, Write-up and reproducibility, run from `instructions/08_section_8.md`. Precedence (rule 13): that file over the `CLAUDE.md` amendments and `PLAN.md`, which beat the kickoff.

Outcome: **completed.** No rule 4 stop.

- Step 8.0 adds `[report] min_factor_months = 24` and `--retry-missing`. `run_all.py --section 7` afterwards left every committed table, PNG and PDF byte-identical, 4 pages each (E.1).
- `answers.csv` has the 25 figures of instruction 08 Section C for each of the 3 funds, 75 rows. `test_answers_trace_to_source` checks every row against its source to 1e-15 (E.2).
- `README.md` is rendered from `docs/README_template.md` by `scripts/build_readme.py`, which `run_all.py` section 8 calls. Both README tests pass (E.3).
- `docs/METHODS.md` states the method in kickoff Sections 4 and 5 order, each amended item citing its instruction file.
- `run_all.py` with no `--section` runs sections 1 to 8. 2 runs in a row left `git status` clean (E.5). The fresh clone of GitHub at `7ef86d4` ran `run_all.py` and the suite, 84 passed, and `git status` was clean.
- 3 claims in instruction 08 D.3 do not match the data, or cannot be written under D.1. The README makes each claim in the form the data supports, with no unsourced number. See Open questions 1 to 3.

## Steps completed

- 8.0 `[report] min_factor_months = 24` in `config.toml`, `attrib/config.py` and the key-list test; `attribute()` skips the factor fit below it, and report page 2 prints the skip line; `test_short_window_skips_factor_page`; `pull_data.py --holdings` skips `missing.csv` tickers unless `--retry-missing` — `03e48dc`
- 8.1 `run_all.py` with no `--section` runs every section — `f2c2019`
- 8.2 `answers.csv` (`answers()` in `run_all.py`, section 8); `tests/test_answers.py` — `9f6347d`
- 8.3 `scripts/build_readme.py`, `docs/README_template.md`, `README.md`, `examples/akre_holdings.csv`, `examples/ivv_holdings.csv`; `tests/test_readme.py` (2 tests) — `ad10548`
- 8.4 `docs/METHODS.md` — `94de8af`
- 8.5 tidy; `CLAUDE.md` amendment 12 — `7ef86d4`

## Evidence

### E.1 Step 8.0

`run_all.py --section 7` after the change: every section passed, the 3 PDFs kept their sizes and 4 pages, and `git status --short` listed only the 8 source files of the step, no output.

```
outputs/reports/akre.pdf: 263867 bytes, 4 pages
outputs/reports/jensen.pdf: 253318 bytes, 4 pages
outputs/reports/polen.pdf: 249676 bytes, 4 pages
section 7: all checks passed
 M attrib/__init__.py
 M attrib/config.py
 M attrib/report.py
 M config.toml
 M scripts/pull_data.py
 M scripts/run_all.py
 M tests/test_attribute.py
 M tests/test_config.py
```

The mini fixture now takes the short-window path, so the 2 rank-deficient-fit warnings of section 7 are gone. `test_short_window_skips_factor_page` extracts the PDF text with pypdf. It checks that the line "Fewer than 24 monthly returns, so the factor fit is skipped." is present and that "Table 2" appears nowhere.

`--holdings` without `--retry-missing`, on Akre's and IVV's 2026-06-30 books: no new sec_id, so no network call. The 2 IVV tickers known to be missing are skipped. `--retry-missing` without `--holdings` is refused.

```
$ python scripts/pull_data.py --holdings h80_akre.csv --benchmark h80_ivv.csv
508 sec_ids in the 2 files, 0 not in the data directory: []
yf_tickers with no price column: ['AVB', 'EA']
skipped, already in data/raw/prices/missing.csv (pass --retry-missing to retry): ['AVB', 'EA']
$ python scripts/pull_data.py --stage french --retry-missing
pull_data.py: error: --retry-missing goes with --holdings and --benchmark
```

### E.2 `answers.csv` in full

```
   question    fund                       figure                   value              interval_lo              interval_hi    source_table                                       source_row
0         1    akre                 cum_excess_D     -1.2489786517091948                                                    book_quarterly                          entity=akre|ivv,t=1..28
1         1  jensen                 cum_excess_D    -0.84193353381547453                                                    book_quarterly                        entity=jensen|ivv,t=1..28
2         1   polen                 cum_excess_D     -1.4147822119605249                                                    book_quarterly                         entity=polen|iwf,t=1..28
3         1    akre              ann_return_fund    0.071749950819665065                                                    book_quarterly                              entity=akre,t=1..28
4         1  jensen              ann_return_fund     0.10654158126211066                                                    book_quarterly                            entity=jensen,t=1..28
5         1   polen              ann_return_fund    0.098086436155239598                                                    book_quarterly                             entity=polen,t=1..28
6         1    akre             ann_return_bench     0.16273721001799024                                                    book_quarterly                               entity=ivv,t=1..28
7         1  jensen             ann_return_bench     0.16273721001799024                                                    book_quarterly                               entity=ivv,t=1..28
8         1   polen             ann_return_bench     0.18800681797102792                                                    book_quarterly                               entity=iwf,t=1..28
9         1    akre            linked_allocation    -0.55057550332086957                                                            linked             fund=akre,method=carino,bucket=Total
10        1  jensen            linked_allocation    0.023889759395231101                                                            linked           fund=jensen,method=carino,bucket=Total
11        1   polen            linked_allocation     -0.2316893666311482                                                            linked            fund=polen,method=carino,bucket=Total
12        1    akre             linked_selection     -1.3043521101259956                                                            linked             fund=akre,method=carino,bucket=Total
13        1  jensen             linked_selection    -0.67985964230041585                                                            linked           fund=jensen,method=carino,bucket=Total
14        1   polen             linked_selection     -1.3559225240418589                                                            linked            fund=polen,method=carino,bucket=Total
15        1    akre           linked_interaction     0.60594896173766866                                                            linked             fund=akre,method=carino,bucket=Total
16        1  jensen           linked_interaction     -0.1859636509102901                                                            linked           fund=jensen,method=carino,bucket=Total
17        1   polen           linked_interaction     0.17282967871248089                                                            linked            fund=polen,method=carino,bucket=Total
18        1    akre            mean_q_allocation  -0.0085804039490870003    -0.016299738430583102      -0.0015351030670695       bootstrap                      fund=akre,series=allocation
19        1  jensen            mean_q_allocation  0.00028712016696609999   -0.0025830255250060999    0.0031776730854091001       bootstrap                    fund=jensen,series=allocation
20        1   polen            mean_q_allocation  -0.0038760867360744999   -0.0083978796843598002   0.00036673170384700002       bootstrap                     fund=polen,series=allocation
21        1    akre             mean_q_selection   -0.022454857888372499    -0.037373076202892701   -0.0094722859659138996       bootstrap                       fund=akre,series=selection
22        1  jensen             mean_q_selection   -0.011029289591690399    -0.023242233515787299    0.0011140499599447001       bootstrap                     fund=jensen,series=selection
23        1   polen             mean_q_selection     -0.0188254345458553      -0.0274292038857867   -0.0097092435396016006       bootstrap                      fund=polen,series=selection
24        2    akre             alpha_month_book  -0.0045607627941778002   -0.0099494487745507738   0.00082792318619517424      factor_fit                   series_id=akre_book,coef=alpha
25        2  jensen             alpha_month_book  -0.0031886872870087002   -0.0055399292828425782  -0.00083744529117482213      factor_fit                 series_id=jensen_book,coef=alpha
26        2   polen             alpha_month_book  -0.0040271037263314002   -0.0072395949376737601  -0.00081461251498903984      factor_fit                  series_id=polen_book,coef=alpha
27        2    akre              alpha_month_nav  -0.0029738342936190998   -0.0081969473189128436    0.0022492787316746444      factor_fit                    series_id=akre_nav,coef=alpha
28        2  jensen              alpha_month_nav  -0.0035632199443361998   -0.0059845643109021004   -0.0011418755777702987      factor_fit                  series_id=jensen_nav,coef=alpha
29        2   polen              alpha_month_nav  -0.0051854667438056999   -0.0084847727473573494   -0.0018861607402540508      factor_fit                   series_id=polen_nav,coef=alpha
30        2    akre                 alpha_t_book     -1.3922605295146828                                                        factor_fit                   series_id=akre_book,coef=alpha
31        2  jensen                 alpha_t_book     -2.2309020493948788                                                        factor_fit                 series_id=jensen_book,coef=alpha
32        2   polen                 alpha_t_book     -2.0621334640311182                                                        factor_fit                  series_id=polen_book,coef=alpha
33        2    akre                  alpha_t_nav    -0.93659803824144161                                                        factor_fit                    series_id=akre_nav,coef=alpha
34        2  jensen                  alpha_t_nav     -2.4207613296847952                                                        factor_fit                  series_id=jensen_nav,coef=alpha
35        2   polen                  alpha_t_nav      -2.585420323055116                                                        factor_fit                   series_id=polen_nav,coef=alpha
36        2    akre                beta_mkt_book     0.95504797185104484                                                        factor_fit                     series_id=akre_book,coef=mkt
37        2  jensen                beta_mkt_book     0.88394994824954864                                                        factor_fit                   series_id=jensen_book,coef=mkt
38        2   polen                beta_mkt_book      1.0396562769386637                                                        factor_fit                    series_id=polen_book,coef=mkt
39        2    akre                      r2_book     0.76433802222993374                                                        factor_fit                   series_id=akre_book,coef=alpha
40        2  jensen                      r2_book     0.92257068096466155                                                        factor_fit                 series_id=jensen_book,coef=alpha
41        2   polen                      r2_book     0.92862585725554636                                                        factor_fit                  series_id=polen_book,coef=alpha
42        2    akre           resid_vol_ann_book      0.1002866068551294                                                        factor_fit                   series_id=akre_book,coef=alpha
43        2  jensen           resid_vol_ann_book    0.045159783222697501                                                        factor_fit                 series_id=jensen_book,coef=alpha
44        2   polen           resid_vol_ann_book    0.056016537561788197                                                        factor_fit                  series_id=polen_book,coef=alpha
45        3    akre      active_share_2026_06_30     0.97374308497719397                                                    risk_quarterly               fund=akre,holdings_date=2026-06-30
46        3  jensen      active_share_2026_06_30     0.61572126671613514                                                    risk_quarterly             fund=jensen,holdings_date=2026-06-30
47        3   polen      active_share_2026_06_30     0.61778981090676921                                                    risk_quarterly              fund=polen,holdings_date=2026-06-30
48        3    akre         te_exante_2026_06_30      0.1345624243935982                                                    risk_quarterly               fund=akre,holdings_date=2026-06-30
49        3  jensen         te_exante_2026_06_30    0.057537057638539203                                                    risk_quarterly             fund=jensen,holdings_date=2026-06-30
50        3   polen         te_exante_2026_06_30    0.084263380318809394                                                    risk_quarterly              fund=polen,holdings_date=2026-06-30
51        3    akre               te_exante_mean    0.088176716177768802                                                       te_realised                                        fund=akre
52        3  jensen               te_exante_mean    0.052711739913042802                                                       te_realised                                      fund=jensen
53        3   polen               te_exante_mean    0.067049779836412096                                                       te_realised                                       fund=polen
54        3    akre              te_realised_84m       0.114092038568129                                                       te_realised                                        fund=akre
55        3  jensen              te_realised_84m    0.052606680478843502                                                       te_realised                                      fund=jensen
56        3   polen              te_realised_84m    0.065669752372288004                                                       te_realised                                       fund=polen
57        3    akre   top15_cte_share_2026_06_30     0.76074275218368637                                                     cte_positions        fund=akre,holdings_date=2026-06-30,top=15
58        3  jensen   top15_cte_share_2026_06_30     0.36513931336607519                                                     cte_positions      fund=jensen,holdings_date=2026-06-30,top=15
59        3   polen   top15_cte_share_2026_06_30     0.76491511088665998                                                     cte_positions       fund=polen,holdings_date=2026-06-30,top=15
60        3    akre    largest_cte_MA_2026_06_30       0.015380255571707                                                     cte_positions     fund=akre,holdings_date=2026-06-30,ticker=MA
61        3  jensen    largest_cte_MU_2026_06_30   0.0067214991445775996                                                     cte_positions   fund=jensen,holdings_date=2026-06-30,ticker=MU
62        3   polen  largest_cte_NVDA_2026_06_30    0.017411557869154302                                                     cte_positions  fund=polen,holdings_date=2026-06-30,ticker=NVDA
63        4    akre                    gate_corr     0.99002831574664885                                                              gate                                        fund=akre
64        4  jensen                    gate_corr     0.99960561212591381                                                              gate                                      fund=jensen
65        4   polen                    gate_corr     0.99818433624530201                                                              gate                                       fund=polen
66        4    akre              gate_n_quarters                      26                                                              gate                                        fund=akre
67        4  jensen              gate_n_quarters                      28                                                              gate                                      fund=jensen
68        4   polen              gate_n_quarters                      28                                                              gate                                       fund=polen
69        4    akre                   te_gap_ann    0.027870232496955201                                                              gate                                        fund=akre
70        4  jensen                   te_gap_ann      0.0058640837700056                                                              gate                                      fund=jensen
71        4   polen                   te_gap_ann    0.013112466077392399                                                              gate                                       fund=polen
72        4    akre                   mean_q_gap      0.0016167830411646  -0.00068559346469730003       0.0038586997949709       bootstrap                             fund=akre,series=gap
73        4  jensen                   mean_q_gap   0.0021407810171738999    0.0013896996752979999       0.0028637306594818       bootstrap                           fund=jensen,series=gap
74        4   polen                   mean_q_gap   0.0038954262435508999       0.0026802287277179    0.0052203237448247997       bootstrap                            fund=polen,series=gap
```

`cum_excess_D`, the 2 annualised returns and `top15_cte_share_2026_06_30` are recomputed from their source rows. The others are single cells. `largest_cte_<TICKER>` is the largest signed CTE (see Deviation 4).

### E.3 `README.md` in full

The README as committed, rendered from the template and `answers.csv`:

````markdown
# Performance and risk attribution on real 13F holdings

## What this is

This repo takes the quarterly 13F holdings of 3 concentrated quality-growth managers (Akre, Jensen and Polen) and the N-PORT holdings of their ETF benchmarks (IVV for Akre and Jensen, IWF for Polen), and works out where each manager's return against its benchmark came from. Each quarter's book is split into the Fama-French 12 industries (FF12) and attributed with Brinson-Fachler, and the 28 quarters are linked with Carino. Monthly book returns go through a Fama-French 5-factor plus momentum regression with HAC standard errors, and active risk comes from a Ledoit-Wolf covariance of daily returns.

Everything is built from free public data: SEC EDGAR filings, the OpenFIGI mapping API, yfinance prices and Ken French's data library. Each 13F book is checked against the fund's own NAV before it is attributed, and each manager gets a 4-page PDF report in `outputs/reports/`. The method is written out in full in [docs/METHODS.md](docs/METHODS.md).

## Answers

**Allocation, selection and interaction.** Every fund trailed its benchmark over the 28 quarters to September 2026. Akre's book returned 7.2% a year against 16.3% for IVV, a cumulative excess return D of −124.9 pp. Jensen's returned 10.7% against the same 16.3% (D of −84.2 pp), and Polen's 9.8% against 18.8% for IWF (D of −141.5 pp). Selection, not allocation, carried most of it for Akre and Polen. Linked with Carino, Akre's selection is −130.4 pp against allocation of −55.1 pp, and Polen's is −135.6 pp against −23.2 pp. Jensen's loss is also selection, −68.0 pp, with allocation of 2.4 pp. The mean quarterly selection effect is −2.25% for Akre and −1.88% for Polen, and both bootstrap intervals are entirely negative (−3.74% to −0.95%, and −2.74% to −0.97%). Jensen's mean quarterly selection of −1.10% has an interval of −2.32% to 0.11%, which reaches into positive values, so this sample cannot distinguish Jensen's selection from no effect. Only Akre's allocation interval is entirely negative (−1.63% to −0.15%).

**Factors.** Jensen's alpha is −0.32% a month on the book, with a HAC t of −2.23, and −0.36% on the NAV, with a t of −2.42. Polen's is −0.40% on the book (t of −2.06) and −0.52% on the NAV (t of −2.59). Akre's alpha of −0.46% a month on the book (t of −1.39, interval −0.99% to 0.08%) cannot be told apart from no alpha. Its R² of 0.76, against 0.92 for Jensen and 0.93 for Polen, says most of Akre's active risk is stock-specific: its residual volatility is 10.0% a year. Market betas on the book are 0.96 for Akre, 0.88 for Jensen and 1.04 for Polen. Akre's exposures drifted the most: from 2025 its value loading climbed and its investment loading fell away, in both its returns and its holdings (Akre's rolling beta and exposure charts below).

**Active risk.** At 2026-06-30 Akre's active share against IVV was 97.4% and its ex-ante tracking error 13.5%. Jensen's were 61.6% and 5.8%, and Polen's against IWF 61.8% and 8.4%. A few positions carry most of that risk for Akre and Polen: the top positions in each tracking error chart below explain 76.1% of Akre's ex-ante tracking error and 76.5% of Polen's, against 36.5% of Jensen's. Akre's largest single contribution is a position it holds, MA at 1.5 pp. Polen's and Jensen's are names they do not own: NVDA at 1.7 pp and MU at 0.7 pp. Realised tracking error over 84 months is 11.4% for Akre, above its ex-ante mean of 8.8%. The reason is September 2026, the largest active month in the sample: FICO, one of Akre's largest positions, collapsed after the FHFA's September order letting every GSE lender use VantageScore, and the book fell far more than IVV that month. Jensen's and Polen's realised figures, 5.3% and 6.6%, sit close to their ex-ante means of 5.3% and 6.7%.

**The book against the NAV.** The quarter-start book tracks the fund's NAV closely for all of them: the correlation of quarterly book and NAV returns is 0.99 for Akre, 1.00 for Jensen and 1.00 for Polen. Polen's filing mixes strategies, ETFs included, and its book still tracks the fund's NAV at 1.00. Every mean gap is positive: the book beat the NAV by 0.16% a quarter for Akre, 0.21% for Jensen and 0.39% for Polen. That is the sign fees and cash predict, since the NAV pays fees and holds cash that the book does not. Jensen's and Polen's bootstrap intervals are entirely positive; Akre's runs from −0.07% to 0.39%. The gap's annualised tracking error is 0.59% for Jensen, 1.31% for Polen and 2.79% for Akre.

## Results

### Brinson-Fachler, linked with Carino

Table 1 gives the linked totals over the 28 quarters in percentage points. Allocation, selection and interaction sum to the total, which equals the cumulative excess return D.

| Fund | Allocation | Selection | Interaction | Total | D |
| --- | ---: | ---: | ---: | ---: | ---: |
| Akre | −55.1 pp | −130.4 pp | 60.6 pp | −124.9 pp | −124.9 pp |
| Jensen | 2.4 pp | −68.0 pp | −18.6 pp | −84.2 pp | −84.2 pp |
| Polen | −23.2 pp | −135.6 pp | 17.3 pp | −141.5 pp | −141.5 pp |

Akre's selection loss sits almost entirely in BusEq. Its BusEq names (Roper, Danaher, CCC and Verisk) did far worse than IVV's BusEq, which is mega-cap technology. Its large positive interaction comes from its weight in FF12 Other (Mastercard, Visa and Moody's), which is weight it does not hold in BusEq: an underweight in a bucket where selection lost gives a positive interaction. Every bucket of every fund is in `outputs/tables/linked.csv`, with the Menchero linking beside Carino.

Akre's selection slides from 2024 and allocation follows it down, with selection ending at −130.4 pp.

![Akre: cumulative allocation and selection](outputs/figures/akre_alloc_vs_sel.png)

Jensen's selection peaked in early 2023 and then fell to −68.0 pp, while its allocation stayed flat.

![Jensen: cumulative allocation and selection](outputs/figures/jensen_alloc_vs_sel.png)

Polen's shortfall opened in 2022 and is almost all selection, which ends at −135.6 pp.

![Polen: cumulative allocation and selection](outputs/figures/polen_alloc_vs_sel.png)

### Factors

Table 2 gives the full-sample fit of each fund's monthly excess return on the 5 Fama-French factors and momentum, on the book and on the NAV. Jensen's and Polen's alphas lie more than 2 HAC standard errors below 0 on both series; Akre's do not.

| Fund | Alpha a month, book | HAC t, book | Alpha a month, NAV | HAC t, NAV | Market beta, book | R², book |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Akre | −0.46% | −1.39 | −0.30% | −0.94 | 0.96 | 0.76 |
| Jensen | −0.32% | −2.23 | −0.36% | −2.42 | 0.88 | 0.92 |
| Polen | −0.40% | −2.06 | −0.52% | −2.59 | 1.04 | 0.93 |

Akre's rolling betas show the drift: its value (HML) loading climbs through 2025 while its investment (CMA) loading falls away.

![Akre: rolling factor betas](outputs/figures/akre_rolling_betas.png)

The holdings-based exposures, built from each stock's own 36-month betas, follow the returns-based line, so the drift comes from what Akre holds.

![Akre: holdings-based against returns-based exposures](outputs/figures/akre_exposures_hb_vs_rb.png)

### Active risk

Table 3 gives active share and ex-ante tracking error at the last holdings date, the mean ex-ante tracking error over the 28 holdings dates, and the realised tracking error over 84 months.

| Fund | Active share, 2026-06-30 | Ex-ante TE, 2026-06-30 | Mean ex-ante TE | Realised TE, 84 months |
| --- | ---: | ---: | ---: | ---: |
| Akre | 97.4% | 13.46% | 8.82% | 11.41% |
| Jensen | 61.6% | 5.75% | 5.27% | 5.26% |
| Polen | 61.8% | 8.43% | 6.70% | 6.57% |

At 2026-06-30 Akre's largest contribution to tracking error is MA at 1.5 pp, and the positions shown explain 76.1% of its ex-ante tracking error.

![Akre: top contributions to ex-ante tracking error](outputs/figures/akre_cte_top15.png)

Jensen's risk is spread out: the positions shown explain 36.5% of it, and the largest is an underweight in MU.

![Jensen: top contributions to ex-ante tracking error](outputs/figures/jensen_cte_top15.png)

Polen's largest contributions are names it does not own, led by NVDA at 1.7 pp.

![Polen: top contributions to ex-ante tracking error](outputs/figures/polen_cte_top15.png)

### The book against the NAV

Table 4 gives the gate for each fund: the correlation of quarterly book and NAV returns, the number of quarters with a NAV return, the gap statistics and the bootstrap interval of the mean gap. A fund passes at a correlation of 0.90 or more.

| Fund | Correlation | Passes | Quarters | Mean gap | Std of gap | Mean abs gap | TE of gap | Mean gap, bootstrap interval |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Akre | 0.99 | Yes | 26 | 0.16% | 1.39% | 1.07% | 2.79% | −0.07% to 0.39% |
| Jensen | 1.00 | Yes | 28 | 0.21% | 0.29% | 0.27% | 0.59% | 0.14% to 0.29% |
| Polen | 1.00 | Yes | 28 | 0.39% | 0.66% | 0.53% | 1.31% | 0.27% to 0.52% |

## Use it on your own holdings

`attribute()` takes 2 holdings files, the fund's and its benchmark's, and writes the same 4-page report. Each file has the columns `period_date, cusip, name, value_usd, shares`, with `entity`, `isin` and `sec_id` optional, and a row for every calendar quarter end from `start` to `end`. The 2 files in `examples/` are Akre's and IVV's books from 2025-06-30 to 2026-06-30:

```python
from attrib import attribute

pdf = attribute(
    "examples/akre_holdings.csv",
    "examples/ivv_holdings.csv",
    start="2025-06-30",
    end="2026-06-30",
)
print(pdf)  # outputs/reports/akre_holdings.pdf
```

It reads local data only. That window gives 15 monthly returns, fewer than the 24 the factor fit needs, so page 2 of that report says the fit is skipped. No NAV series is supplied, so page 4 skips the reconstruction check.

A file that holds securities not yet in `data/` raises an error listing them. Map them through OpenFIGI and SEC and pull their prices into `data/extra/` with:

```bash
python scripts/pull_data.py --holdings my_fund.csv --benchmark my_benchmark.csv
```

This needs `SEC_USER_AGENT` set in the environment. Tickers already known to have no yfinance prices (`data/raw/prices/missing.csv`) are skipped unless you add `--retry-missing`.

To rebuild every table, figure and report in this repo from `data/raw/` and `data/manual/`:

```bash
python scripts/run_all.py
```

## Data and method limits

**What a 13F book cannot see.** The 13F lists a manager's long US-listed equity positions at each quarter end, filed up to 45 days later. It omits cash, shorts, most non-US shares, bonds and anything bought and sold inside the quarter. This report holds each quarter-end book unchanged for the next 3 months, so trades made during the quarter show up only in the gap between the book and the fund's NAV, together with fees and cash. A 13F belongs to the manager, not to one fund, so where a manager runs several strategies the book blends them. Sectors are Fama-French 12 industries built from SIC codes, which put payment networks such as Visa and Mastercard in Other. Securities that could not be mapped to a ticker, or had no price, earn the book's own return so that they move nothing.

- **Unpriced weight.** A security with a ticker but no price at the start of a quarter goes to the Unpriced bucket. Its mean weight over the 28 quarters is small in every book:

| Book | Mean unpriced weight |
| --- | ---: |
| Akre | 0.78% |
| Jensen | 0.01% |
| Polen | 0.00% |
| IVV | 1.03% |
| IWF | 0.94% |

- **Akre's NAV gap.** Akre's monthly NAV returns come from the fund's N-PORT filings (item B.5) up to July 2025 and from the AKRE ETF's prices from November 2025. The months 2025-08 to 2025-10, when the fund converted to an ETF, have no public return. Their quarters are left out of Akre's gate correlation and gap statistics, so Table 4 counts fewer quarters for Akre.
- **The start date.** The window starts with the 2019-09-30 books because iShares filed its first public N-PORT for that quarter. There are no benchmark holdings on EDGAR before it.
- **FF12, not GICS.** Sectors are the Fama-French 12 industries mapped from SIC codes. They are public and reproducible, but they split companies differently from commercial sector schemes: payment networks, ratings agencies and data providers land in Other.
- **Holdings-based and returns-based exposures share a window.** The stock betas behind the holdings-based exposures and the rolling fund betas both use 36 months of returns ending at the same date, so their agreement is partly built in.
- **Determinism across platforms.** 2 runs on 1 machine give byte-identical CSVs, PNGs and PDFs. Across operating systems the numeric outputs agree to 1e-10 relative, and PNGs and PDFs differ at the byte level through font rendering (`docs/CONVENTIONS_RESOLVED.md`, item 25).
- **The project 1 link was dropped.** The original plan took holdings-based exposures from project 1's characteristic scores. Project 1 produced no characteristic scores, so each stock's exposure comes from its own 36-month factor betas instead.

## Reproduce

Python 3.12 and [uv](https://docs.astral.sh/uv/). The lock file `requirements-lock.txt` pins every dependency, including project 3's covariance and bootstrap code at a fixed commit.

```bash
uv venv --python 3.12
uv pip install -r requirements-lock.txt
uv pip install -e . --no-deps
python scripts/run_all.py
pytest -p socket --disable-socket
```

`run_all.py` is offline and reads only `data/raw/` and `data/manual/`, which are committed. `scripts/pull_data.py` is the only code that touches the network.
````

### E.4 The D.3 claims against the data

**Akre's selection loss sits in BusEq.** Carino rows from `linked.csv`:

```
    fund  method bucket  allocation  selection  interaction     total
5   akre  carino  BusEq   -0.293674  -1.245880     0.781673 -0.757881
11  akre  carino  Other   -0.430719   0.005701    -0.062837 -0.487855
14  akre  carino  Total   -0.550576  -1.304352     0.605949 -1.248979
```

The names behind the BusEq selection: each name's share of the fund's BusEq weight times its return relative to IVV's BusEq, times IVV's BusEq weight, summed over quarters (unlinked). These sum to the unlinked BusEq selection.

```
        quarters  mean_weight  selection_unlinked
ticker                                           
ROP           28     0.061131           -0.360843
DHR           26     0.030591           -0.110134
CCC           10     0.015780           -0.067760
VRSK          25     0.017384           -0.027820
CRM            8     0.036967           -0.025822
ADBE          14     0.044308           -0.015260
ALRM          14     0.007092           -0.004035
TTD            2     0.000020            0.000004
DSGX           6     0.000594            0.000031
SNOW           2     0.013077            0.000925
NOW            2     0.021481            0.002542
SOPH          10     0.001483            0.005131

sum over names np.float64(-0.6030424414497005); unlinked BusEq selection in brinson_quarterly np.float64(-0.6030424414497001)
```

The bucket of each name D.3 mentions, with the number of quarters held. FICO and CoStar (CSGP) sit in FF12 Other, not BusEq: both have SIC 7389 in their submissions, which is in no FF12 range. See Open question 1.

```
  ticker bucket  quarters
0    CCC  BusEq        10
1   CSGP  Other        27
2   FICO  Other         5
3     MA  Other        28
4    MCO  Other        28
5    ROP  BusEq        28
6      V  Other        28
```

**Akre's weight in FF12 Other and BusEq**, from `brinson_quarterly.csv`. Other runs from 34.0% to 56.2%, not 39% to 56%. See Open question 2.

```
    wP_BusEq  wP_Other  wB_BusEq  wB_Other
t                                         
1   0.124811  0.340214  0.237266  0.105791
2   0.115570  0.367465  0.250644  0.107153
3   0.149702  0.382972  0.277662  0.104371
4   0.151104  0.393880  0.298413  0.108000
5   0.158416  0.407366  0.306454  0.111929
6   0.168181  0.417300  0.299967  0.112127
7   0.163630  0.418430  0.295174  0.111909
8   0.209532  0.382788  0.310529  0.109442
9   0.217419  0.372063  0.319355  0.105571
10  0.212886  0.360322  0.335880  0.098829
11  0.219792  0.402127  0.321432  0.095416
12  0.221661  0.389722  0.305120  0.089638
13  0.223480  0.396410  0.296687  0.090749
14  0.146898  0.470598  0.283367  0.093020
15  0.145009  0.482575  0.323453  0.093128
16  0.145901  0.495699  0.348364  0.091171
17  0.110862  0.513114  0.346329  0.090394
18  0.107050  0.468859  0.358051  0.095663
19  0.115664  0.473306  0.368579  0.095388
20  0.124375  0.458352  0.401603  0.086109
21  0.121273  0.452780  0.390498  0.088399
22  0.113588  0.471987  0.400833  0.088968
23  0.129601  0.496056  0.367912  0.093400
24  0.129262  0.524966  0.405814  0.092401
25  0.091547  0.540047  0.430879  0.083928
26  0.079234  0.562231  0.434361  0.080597
27  0.147315  0.529998  0.414867  0.077449
28  0.158577  0.560060  0.462493  0.069774

min and max:
     wP_BusEq  wP_Other  wB_BusEq  wB_Other
min  0.079234  0.340214  0.237266  0.069774
max  0.223480  0.562231  0.462493  0.112127
```

**September 2026 is the largest active month.** The 5 largest |monthly book active returns| over the 3 funds, then September 2026 for every entity, from `book_monthly.csv`:

```
     month  fund  abs_active    active
0  2026-09  akre    0.132778 -0.132778
1  2026-04  akre    0.075027 -0.075027
2  2024-07  akre    0.071630  0.071630
3  2026-02  akre    0.069654 -0.069654
4  2025-09  akre    0.068710 -0.068710

entity       akre       ivv       iwf    jensen     polen
month                                                    
2026-09 -0.136739 -0.003962  0.021491 -0.027735 -0.025069
```

FICO's month-end adjusted closes from `adjclose.parquet`:

```
                FICO       ret
date                          
2026-06  1194.780029       NaN
2026-07  1122.969971 -0.060103
2026-08  1147.209961  0.021586
2026-09   592.469971 -0.483556
```

**Every mean gap is positive**, from `gate.csv`:

```
     fund      corr  pass  n_quarters  mean_gap   std_gap  mean_abs_gap  te_gap_ann
0    akre  0.990028  True          26  0.001617  0.013935      0.010688    0.027870
1  jensen  0.999606  True          28  0.002141  0.002932      0.002749    0.005864
2   polen  0.998184  True          28  0.003895  0.006556      0.005292    0.013112
```

### E.5 `run_all.py` twice in a row, local

```
$ python scripts/run_all.py
section 1: all checks passed
section 2: all checks passed
section 3: all checks passed
section 4: all checks passed
section 5: all checks passed
section 6: all checks passed
outputs/reports/akre.pdf: 263867 bytes, 4 pages
outputs/reports/jensen.pdf: 253318 bytes, 4 pages
outputs/reports/polen.pdf: 249676 bytes, 4 pages
section 7: all checks passed
wrote README.md: 13675 bytes
section 8: all checks passed
(run 1: exit 0, 53 s)
$ git status --short
(end of git status)
$ python scripts/run_all.py
section 1: all checks passed
section 2: all checks passed
section 3: all checks passed
section 4: all checks passed
section 5: all checks passed
section 6: all checks passed
outputs/reports/akre.pdf: 263867 bytes, 4 pages
outputs/reports/jensen.pdf: 253318 bytes, 4 pages
outputs/reports/polen.pdf: 249676 bytes, 4 pages
section 7: all checks passed
wrote README.md: 13675 bytes
section 8: all checks passed
(run 2: exit 0, 55 s)
$ git status --short
(end of git status)
```

### E.6 Tidy

- **TODO grep.** `git grep -l -E "TODO|FIXME|XXX"` still matches, but in no source file:
  - `PLAN.md`, `instructions/00_kickoff.md` and `instructions/08_section_8.md`, which describe the grep itself;
  - `data/raw/sec/company_tickers_mf.json` and `tests/fixtures/nport/ivv_2023-06-30_0001752724-23-191503.xml`, raw data where "XXX" occurs inside identifiers;
  - 14 PNGs, where the bytes happen to match.

  None of these can be edited: they are instruction files, `PLAN.md` (rule 14) and committed raw data. Restricted to whole words, over everything except `data/raw/` and `tests/fixtures/`, only `PLAN.md:107` and `instructions/08_section_8.md:140` match. Both are the instruction text.

  ```
  $ git grep -l -E "TODO|FIXME|XXX"
  PLAN.md
  data/raw/sec/company_tickers_mf.json
  instructions/00_kickoff.md
  instructions/08_section_8.md
  outputs/figures/jensen_exposures_hb_vs_rb.png
  outputs/figures/jensen_rolling_betas.png
  outputs/figures/polen_alloc_vs_sel.png
  outputs/figures/polen_cte_top15.png
  outputs/figures/polen_exposures_hb_vs_rb.png
  outputs/figures/polen_rolling_betas.png
  review/section_7_pages/akre_p1.png
  review/section_7_pages/akre_p2.png
  review/section_7_pages/akre_p3.png
  review/section_7_pages/jensen_p1.png
  review/section_7_pages/jensen_p3.png
  review/section_7_pages/polen_p1.png
  review/section_7_pages/polen_p2.png
  review/section_7_pages/polen_p3.png
  tests/fixtures/nport/ivv_2023-06-30_0001752724-23-191503.xml
  $ git grep -n -w -I -E "TODO|FIXME|XXX" -- . ":!data/raw" ":!tests/fixtures"
  PLAN.md:107:**8.5 Final check and tidy.** A fresh clone runs `scripts/run_all.py` and the suite with sockets disabled; `git status` is clean afterwards. Tidy: no stray files, no TODOs, no unused functions. Review evidence: the full fresh-clone output, a TODO grep and the list of tracked files.
  instructions/08_section_8.md:140:  - `grep -rn "TODO\|FIXME\|XXX"` over tracked files returns nothing;
  ```
- **Unused functions.** None removed, because none were found. Every function in the tracked `.py` files was parsed with `ast`, and the Name, Attribute and import references to it were counted. No function other than tests, dunders and `main` has 0 references. Each function with 1 or 2 references was traced to a real call site by grep. `ruff check --select F401,F811,F841` finds no unused import. Its 1 hit, `bench` in `run_all.report_results`, is a false positive: the variable is used inside a `DataFrame.query` string as `@bench`.
- **`decisions/OPEN.md`** holds only its heading and pointer line, unchanged: "No open items. OPEN-31 and OPEN-32 were decided in instructions/02b_section_2_completion.md, Section B; OPEN-33 in instructions/02c_section_2_completion.md, Section B, recorded in decisions/section_2_review.md." This session's open questions are below and in the status file, not in `OPEN.md`, since Section F asks for the pointer line only.
- **`CLAUDE.md`** `## Amendments` gains line 12, citing instruction 08 for `min_factor_months` and `--retry-missing`.
- **Stray files.** None tracked. Untracked local only: `.venv/`, `attrib.egg-info/`, `__pycache__/`, `.pytest_cache/` and `data/processed/`, all gitignored.

### E.7 Tracked files with sizes

285 tracked files at `7ef86d4`, sizes in bytes. This review and the status file are added in the next commit.

```
                                                              path     bytes
0                                                   .gitattributes       118
1                                                       .gitignore       133
2                                                        CLAUDE.md     18678
3                                                          PLAN.md     25417
4                       Project Outline/04_Attribution_Engine.docx     15494
5                                                        README.md     13675
6                                                      WORKFLOW.md     13703
7                                               attrib/__init__.py     15748
8                                              attrib/bootstrap.py       871
9                                                attrib/brinson.py      1686
10                                                attrib/config.py      3134
11                                                 attrib/edgar.py     17671
12                                               attrib/factors.py      7643
13                                               attrib/linking.py      3218
14                                               attrib/mapping.py     12704
15                                        attrib/reconstruction.py      2558
16                                                attrib/report.py     14779
17                                               attrib/returns.py     12811
18                                                  attrib/risk.py      6152
19                                                     config.toml      1406
20                                       data/manual/overrides.csv      3691
21                                         data/processed/.gitkeep         0
22                                               data/raw/.gitkeep         0
23                                          data/raw/MANIFEST.json     55056
24     data/raw/edgar/13f/akre/2019-03-31_0001112520-19-000015.xml     11898
25     data/raw/edgar/13f/akre/2019-06-30_0001112520-19-000017.xml     11429
26     data/raw/edgar/13f/akre/2019-09-30_0001112520-19-000024.xml     11887
27     data/raw/edgar/13f/akre/2019-12-31_0001112520-20-000010.xml     11886
28     data/raw/edgar/13f/akre/2020-03-31_0001112520-20-000016.xml     13268
29     data/raw/edgar/13f/akre/2020-06-30_0001112520-20-000022.xml     13274
30     data/raw/edgar/13f/akre/2020-09-30_0001112520-20-000024.xml     13313
31     data/raw/edgar/13f/akre/2020-12-31_0001112520-21-000003.xml     13271
32     data/raw/edgar/13f/akre/2021-03-31_0001112520-21-000012.xml     13707
33     data/raw/edgar/13f/akre/2021-03-31_0001112520-21-000016.xml     11437
34     data/raw/edgar/13f/akre/2021-06-30_0001112520-21-000020.xml     11908
35     data/raw/edgar/13f/akre/2021-09-30_0001112520-21-000023.xml     11949
36     data/raw/edgar/13f/akre/2021-12-31_0001112520-22-000005.xml     11487
37     data/raw/edgar/13f/akre/2022-03-31_0001112520-22-000009.xml     10522
38     data/raw/edgar/13f/akre/2022-06-30_0001112520-22-000013.xml     11037
39     data/raw/edgar/13f/akre/2022-09-30_0001112520-22-000015.xml     10590
40     data/raw/edgar/13f/akre/2022-12-31_0001112520-23-000006.xml     10833
41     data/raw/edgar/13f/akre/2023-03-31_0001112520-23-000008.xml      9744
42     data/raw/edgar/13f/akre/2023-06-30_0001112520-23-000013.xml      9831
43     data/raw/edgar/13f/akre/2023-09-30_0001112520-23-000019.xml      9331
44     data/raw/edgar/13f/akre/2023-12-31_0001112520-24-000006.xml      8768
45     data/raw/edgar/13f/akre/2024-03-31_0001112520-24-000010.xml     10298
46     data/raw/edgar/13f/akre/2024-03-31_0001112520-24-000012.xml     10800
47     data/raw/edgar/13f/akre/2024-06-30_0001112520-24-000014.xml      9801
48     data/raw/edgar/13f/akre/2024-09-30_0001112520-24-000025.xml      9306
49     data/raw/edgar/13f/akre/2024-12-31_0001112520-25-000003.xml      9301
50     data/raw/edgar/13f/akre/2025-03-31_0001112520-25-000015.xml      9298
51     data/raw/edgar/13f/akre/2025-06-30_0001112520-25-000019.xml      9765
52     data/raw/edgar/13f/akre/2025-09-30_0001112520-25-000029.xml      9767
53     data/raw/edgar/13f/akre/2025-12-31_0001112520-26-000008.xml      9273
54     data/raw/edgar/13f/akre/2026-03-31_0001112520-26-000009.xml     10295
55     data/raw/edgar/13f/akre/2026-06-30_0001112520-26-000014.xml     10293
56                             data/raw/edgar/13f/filings_akre.csv      9109
57                           data/raw/edgar/13f/filings_jensen.csv      8790
58                            data/raw/edgar/13f/filings_polen.csv      8583
59   data/raw/edgar/13f/jensen/2019-03-31_0001171200-19-000211.xml     35650
60   data/raw/edgar/13f/jensen/2019-06-30_0001171200-19-000284.xml     35653
61   data/raw/edgar/13f/jensen/2019-09-30_0001171200-19-000366.xml     35215
62   data/raw/edgar/13f/jensen/2019-12-31_0001171200-20-000061.xml     34764
63   data/raw/edgar/13f/jensen/2020-03-31_0001171200-20-000338.xml     34744
64   data/raw/edgar/13f/jensen/2020-06-30_0001171200-20-000521.xml     34336
65   data/raw/edgar/13f/jensen/2020-09-30_0001171200-20-000622.xml     36170
66   data/raw/edgar/13f/jensen/2020-12-31_0001171200-21-000057.xml     35277
67   data/raw/edgar/13f/jensen/2021-03-31_0001171200-21-000236.xml     34849
68   data/raw/edgar/13f/jensen/2021-06-30_0001171200-21-000290.xml     35322
69   data/raw/edgar/13f/jensen/2021-09-30_0001171200-21-000388.xml     35781
70   data/raw/edgar/13f/jensen/2021-12-31_0001171200-22-000037.xml     36216
71   data/raw/edgar/13f/jensen/2022-03-31_0001171200-22-000245.xml     37146
72   data/raw/edgar/13f/jensen/2022-06-30_0001171200-22-000293.xml     37581
73   data/raw/edgar/13f/jensen/2022-09-30_0001171200-22-000347.xml     37571
74   data/raw/edgar/13f/jensen/2022-12-31_0001171200-23-000057.xml     39184
75   data/raw/edgar/13f/jensen/2022-12-31_0001171200-23-000206.xml     39184
76   data/raw/edgar/13f/jensen/2023-03-31_0001171200-23-000298.xml     37789
77   data/raw/edgar/13f/jensen/2023-06-30_0001171200-23-000356.xml     38256
78   data/raw/edgar/13f/jensen/2023-09-30_0001171200-23-000445.xml     38712
79   data/raw/edgar/13f/jensen/2023-12-31_0001171200-24-000016.xml     38246
80   data/raw/edgar/13f/jensen/2024-03-31_0001171200-24-000202.xml     39147
81   data/raw/edgar/13f/jensen/2024-06-30_0001171200-24-000243.xml     40534
82   data/raw/edgar/13f/jensen/2024-09-30_0001171200-24-000330.xml     40546
83   data/raw/edgar/13f/jensen/2024-12-31_0001171200-25-000017.xml     39627
84   data/raw/edgar/13f/jensen/2025-03-31_0001171200-25-000219.xml     39160
85   data/raw/edgar/13f/jensen/2025-06-30_0001171200-25-000262.xml     38689
86   data/raw/edgar/13f/jensen/2025-09-30_0001171200-25-000265.xml     40495
87   data/raw/edgar/13f/jensen/2025-12-31_0001171200-26-000003.xml     41404
88   data/raw/edgar/13f/jensen/2026-03-31_0001171200-26-000007.xml     39061
89   data/raw/edgar/13f/jensen/2026-06-30_0001171200-26-000010.xml     38558
90    data/raw/edgar/13f/polen/2019-03-31_0001172661-19-001172.xml     27292
91    data/raw/edgar/13f/polen/2019-06-30_0001172661-19-001677.xml     25941
92    data/raw/edgar/13f/polen/2019-09-30_0001172661-19-002155.xml     26850
93    data/raw/edgar/13f/polen/2019-12-31_0001172661-20-000333.xml     28676
94    data/raw/edgar/13f/polen/2020-03-31_0001172661-20-001182.xml     29138
95    data/raw/edgar/13f/polen/2020-06-30_0001172661-20-001647.xml     29140
96    data/raw/edgar/13f/polen/2020-09-30_0001172661-20-002092.xml     30087
97    data/raw/edgar/13f/polen/2020-12-31_0001172661-21-000318.xml     33301
98    data/raw/edgar/13f/polen/2021-03-31_0001172661-21-001092.xml     32870
99    data/raw/edgar/13f/polen/2021-06-30_0001172661-21-001640.xml     37425
100   data/raw/edgar/13f/polen/2021-09-30_0001172661-21-002146.xml     41931
101   data/raw/edgar/13f/polen/2021-12-31_0001172661-22-000331.xml     42445
102   data/raw/edgar/13f/polen/2022-03-31_0001172661-22-001239.xml     41999
103   data/raw/edgar/13f/polen/2022-06-30_0001172661-22-001764.xml     38788
104   data/raw/edgar/13f/polen/2022-09-30_0001172661-22-002289.xml     39294
105   data/raw/edgar/13f/polen/2022-12-31_0001172661-23-000805.xml     45973
106   data/raw/edgar/13f/polen/2023-03-31_0001172661-23-002012.xml     46460
107   data/raw/edgar/13f/polen/2023-06-30_0001172661-23-002916.xml     46391
108   data/raw/edgar/13f/polen/2023-09-30_0001172661-23-003726.xml     45950
109   data/raw/edgar/13f/polen/2023-12-31_0001172661-24-000776.xml     49646
110   data/raw/edgar/13f/polen/2023-12-31_0001172661-24-001616.xml     49658
111   data/raw/edgar/13f/polen/2023-12-31_0001172661-24-002148.xml     49658
112   data/raw/edgar/13f/polen/2024-03-31_0001172661-24-002149.xml     48248
113   data/raw/edgar/13f/polen/2024-06-30_0001172661-24-003233.xml     51019
114   data/raw/edgar/13f/polen/2024-09-30_0001172661-24-004624.xml     54699
115   data/raw/edgar/13f/polen/2024-09-30_0001172661-25-000622.xml     54699
116   data/raw/edgar/13f/polen/2024-12-31_0001172661-25-000623.xml     57481
117   data/raw/edgar/13f/polen/2025-03-31_0001172661-25-001713.xml     54193
118   data/raw/edgar/13f/polen/2025-06-30_0001172661-25-003133.xml    110717
119   data/raw/edgar/13f/polen/2025-09-30_0001172661-25-004691.xml    107087
120   data/raw/edgar/13f/polen/2025-12-31_0001172661-26-000654.xml    108047
121   data/raw/edgar/13f/polen/2026-03-31_0001172661-26-001911.xml    102050
122   data/raw/edgar/13f/polen/2026-06-30_0001172661-26-003035.xml    101083
123                           data/raw/edgar/nport/filings_ivv.csv      1733
124                           data/raw/edgar/nport/filings_iwf.csv      1675
125                          data/raw/edgar/nport/holdings_ivv.csv   2421411
126                          data/raw/edgar/nport/holdings_iwf.csv   2014998
127                  data/raw/edgar/nport_returns/akre_monthly.csv     20219
128                data/raw/edgar/nport_returns/jensen_monthly.csv     30294
129                 data/raw/edgar/nport_returns/polen_monthly.csv     16091
130               data/raw/edgar/nport_returns/series_resolved.csv       491
131                                 data/raw/french/Siccodes12.txt      1764
132                                data/raw/french/ff5_monthly.csv     46265
133                                data/raw/french/mom_monthly.csv     17945
134                                 data/raw/openfigi/fallback.csv    269486
135                                  data/raw/openfigi/mapping.csv    134575
136                               data/raw/prices/adjclose.parquet  21354976
137                                    data/raw/prices/missing.csv       890
138                               data/raw/prices/nav_adjclose.csv    241114
139                            data/raw/sec/cik_override_check.csv      1693
140                              data/raw/sec/company_tickers.json    799085
141                           data/raw/sec/company_tickers_mf.json   1234903
142                               data/raw/sec/series_resolved.csv       113
143                                           data/raw/sec/sic.csv     88678
144                                              decisions/OPEN.md       229
145                                      decisions/data_sources.md       465
146                                      decisions/dependencies.md       505
147                              decisions/funds_and_benchmarks.md       452
148                                     decisions/pricing_rules.md       429
149                                  decisions/section_0_review.md      4641
150                                  decisions/section_2_review.md      1840
151                                      decisions/sectors_ff12.md       432
152                                   docs/CONVENTIONS_RESOLVED.md      4904
153                                                docs/METHODS.md     51175
154                                        docs/README_template.md     14135
155                                     examples/akre_holdings.csv      6414
156                                      examples/ivv_holdings.csv    227460
157                                     instructions/00_kickoff.md     44738
158                              instructions/00_kickoff.status.md      3501
159                                   instructions/01_section_1.md     13264
160                            instructions/01_section_1.status.md      2246
161                       instructions/01b_section_1_completion.md      8581
162                instructions/01b_section_1_completion.status.md      3300
163                                   instructions/02_section_2.md      9277
164                            instructions/02_section_2.status.md      3151
165                       instructions/02b_section_2_completion.md     10235
166                instructions/02b_section_2_completion.status.md      2923
167                       instructions/02c_section_2_completion.md      4001
168                instructions/02c_section_2_completion.status.md      3501
169                                   instructions/03_section_3.md      9806
170                            instructions/03_section_3.status.md      3920
171                                   instructions/04_section_4.md      7410
172                            instructions/04_section_4.status.md      3623
173                                   instructions/05_section_5.md      6695
174                            instructions/05_section_5.status.md      3468
175                                   instructions/06_section_6.md      6097
176                            instructions/06_section_6.status.md      3144
177                                   instructions/07_section_7.md      8253
178                            instructions/07_section_7.status.md      2720
179                                   instructions/08_section_8.md      9320
180                                       outputs/figures/.gitkeep         0
181                          outputs/figures/akre_alloc_vs_sel.png     87648
182                             outputs/figures/akre_cte_top15.png     50865
183                    outputs/figures/akre_exposures_hb_vs_rb.png    128839
184                         outputs/figures/akre_rolling_betas.png    106271
185                        outputs/figures/jensen_alloc_vs_sel.png     79970
186                           outputs/figures/jensen_cte_top15.png     51363
187                  outputs/figures/jensen_exposures_hb_vs_rb.png    126035
188                       outputs/figures/jensen_rolling_betas.png     98436
189                         outputs/figures/polen_alloc_vs_sel.png     84308
190                            outputs/figures/polen_cte_top15.png     51887
191                   outputs/figures/polen_exposures_hb_vs_rb.png    121463
192                        outputs/figures/polen_rolling_betas.png     86572
193                                       outputs/reports/.gitkeep         0
194                                       outputs/reports/akre.pdf    263867
195                                     outputs/reports/jensen.pdf    253318
196                                      outputs/reports/polen.pdf    249676
197                                        outputs/tables/.gitkeep         0
198                                     outputs/tables/answers.csv      7206
199                                outputs/tables/book_monthly.csv     14521
200                              outputs/tables/book_quarterly.csv      8926
201                                   outputs/tables/bootstrap.csv      1012
202                           outputs/tables/brinson_quarterly.csv    175021
203                                     outputs/tables/buckets.csv     92585
204                                    outputs/tables/coverage.csv     20273
205                               outputs/tables/cte_positions.csv   3836114
206                                 outputs/tables/cte_sectors.csv     45591
207                              outputs/tables/factor_by_year.csv     14942
208                                  outputs/tables/factor_fit.csv      7033
209                                        outputs/tables/gate.csv       427
210                          outputs/tables/holdings_exposures.csv     41375
211                                 outputs/tables/large_moves.csv     55217
212                                      outputs/tables/linked.csv      8894
213                                 outputs/tables/nav_monthly.csv     10941
214                                   outputs/tables/nocik_top.csv      6492
215                              outputs/tables/reconstruction.csv     13124
216                              outputs/tables/risk_quarterly.csv     15929
217                               outputs/tables/rolling_betas.csv     34288
218                                 outputs/tables/te_realised.csv       193
219                                outputs/tables/unmapped_top.csv     10786
220                                outputs/tables/unpriced_top.csv      4013
221                                                 pyproject.toml       591
222                                          requirements-lock.txt      3631
223                                                review/.gitkeep         0
224                                             review/TEMPLATE.md       464
225                                            review/section_1.md    133612
226                                            review/section_2.md    190535
227                                            review/section_3.md    126738
228                                            review/section_4.md     29675
229                                            review/section_5.md     42114
230                                            review/section_6.md     45585
231                                            review/section_7.md     17569
232                             review/section_7_pages/akre_p1.png    123000
233                             review/section_7_pages/akre_p2.png    105407
234                             review/section_7_pages/akre_p3.png     70260
235                             review/section_7_pages/akre_p4.png     54890
236                           review/section_7_pages/jensen_p1.png    119307
237                           review/section_7_pages/jensen_p2.png    102057
238                           review/section_7_pages/jensen_p3.png     70045
239                           review/section_7_pages/jensen_p4.png     54929
240                            review/section_7_pages/polen_p1.png    121058
241                            review/section_7_pages/polen_p2.png     98345
242                            review/section_7_pages/polen_p3.png     69877
243                            review/section_7_pages/polen_p4.png     54902
244                                        scripts/build_readme.py      7498
245                                           scripts/pull_data.py     46828
246                                             scripts/run_all.py     52143
247                                        tests/fixtures/.gitkeep         0
248    tests/fixtures/13f/akre/2022-06-30_0001112520-22-000013.xml     11037
249    tests/fixtures/13f/akre/2023-06-30_0001112520-23-000013.xml      9831
250                                   tests/fixtures/FIXTURES.json       705
251                     tests/fixtures/mini/holdings_benchmark.csv       314
252                          tests/fixtures/mini/holdings_fund.csv       312
253                       tests/fixtures/mini/manual/overrides.csv        42
254                  tests/fixtures/mini/raw/french/Siccodes12.txt      1764
255                 tests/fixtures/mini/raw/french/ff5_monthly.csv      2154
256                 tests/fixtures/mini/raw/french/mom_monthly.csv       676
257                  tests/fixtures/mini/raw/openfigi/fallback.csv       113
258                   tests/fixtures/mini/raw/openfigi/mapping.csv       343
259                    tests/fixtures/mini/raw/prices/adjclose.csv     79314
260               tests/fixtures/mini/raw/sec/company_tickers.json       266
261                            tests/fixtures/mini/raw/sec/sic.csv       181
262   tests/fixtures/nport/ivv_2023-06-30_0001752724-23-191503.xml    511918
263                                             tests/real_data.py      3358
264                                          tests/test_answers.py      4574
265                                        tests/test_attribute.py      2441
266                                          tests/test_brinson.py      5504
267                                           tests/test_config.py      3353
268                                     tests/test_data_loaders.py      1191
269                                        tests/test_edgar_13f.py      6212
270                                     tests/test_edgar_client.py      3277
271                                      tests/test_edgar_nport.py      7541
272                                        tests/test_exposures.py      3976
273                                          tests/test_factors.py      3075
274                                          tests/test_linking.py      6171
275                                         tests/test_manifest.py       586
276                                          tests/test_mapping.py      9398
277                                      tests/test_nav_returns.py      3285
278                                        tests/test_overrides.py      3640
279                                      tests/test_placeholder.py        40
280                                           tests/test_readme.py      1733
281                                           tests/test_report.py      4718
282                                     tests/test_returns_book.py      7987
283                                 tests/test_returns_calendar.py      1732
284                                             tests/test_risk.py      7346
```

## Tests run

```
$ .venv\Scripts\python.exe -m pytest -p socket --disable-socket -q
........................................................................ [ 85%]
............                                                             [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\Utkarsh\10. Quant Projects\6) Attribution Engine On Real Holdings\repo-clone\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
84 passed, 1 warning in 33.76s
```

## Fresh-clone check

The step commits were pushed to `7ef86d4` first. The check ran on Windows at `C:\fc8`.

```
$ git clone https://github.com/uty101/Attribution-Engine-On-Real-Holdings.git /c/fc8
7ef86d4 step 8.5: tidy; CLAUDE.md amendment 12 for min_factor_months and --retry-missing
$ uv venv --python 3.12
$ uv pip install -r requirements-lock.txt
$ uv pip install -e . --no-deps
$ python scripts/run_all.py
section 1: all checks passed
section 2: all checks passed
section 3: all checks passed
section 4: all checks passed
section 5: all checks passed
section 6: all checks passed
outputs/reports/akre.pdf: 263867 bytes, 4 pages
outputs/reports/jensen.pdf: 253318 bytes, 4 pages
outputs/reports/polen.pdf: 249676 bytes, 4 pages
section 7: all checks passed
wrote README.md: 13675 bytes
section 8: all checks passed
run_all: 82 s
$ pytest -p socket --disable-socket -q
........................................................................ [ 85%]
............                                                             [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\fc8\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
84 passed, 1 warning in 34.01s
pytest: 36 s
$ git status --short
(end of git status)
```

## Runtime per step

- 8.0: `run_all.py --section 7`, 140 s; 3 test files, 30 s.
- 8.1 and 8.2: `run_all.py` with section 8, 223 s (first run after the edits, cold disk cache).
- 8.3: `run_all.py`, 201 s; the README example (`attribute()` on the 2 example files), 35 s.
- 8.4: no run.
- 8.5: `run_all.py` twice, 53 s and 55 s; the full suite, 35 s. Fresh clone: `run_all.py` 82 s, suite 36 s.

## Deviations from PLAN.md

1. **2 tests read committed outputs.** `test_answers_trace_to_source` and both README tests read `outputs/tables/`, `README.md` and the template, as instruction 08 requires them to. Rule 7 says tests read only `data/raw/`, `tests/fixtures/` or synthetic data. Instruction 08 wins (rule 13). The files are committed, so the tests pass in a fresh clone before `run_all.py` runs.
2. **Placeholder syntax beyond D.1's example.** `{fund.figure@lo:fmt}` and `{fund.figure@hi:fmt}` give the interval columns. `{fund.largest_cte_*:fmt}` matches the 1 figure with the fund's ticker in its name, and the format `ticker` prints that ticker. The 5 number formats are as D.1 lists them. `pct2` is read as × 100 with 2 decimals and "%". Negative numbers use the minus sign U+2212.
3. **Table placeholders.** `{table:carino_totals}`, `{table:factor_fit}`, `{table:risk}`, `{table:gate}` and `{table:unpriced}`. Table 1's D column comes from `answers.csv` (`cum_excess_D`); everything else comes from the CSV the table shows. Table 4 adds the gap bootstrap interval from `bootstrap.csv`, as on report page 4. The unpriced table covers all 5 books, from `book_quarterly.csv`.
4. **`largest_cte_<TICKER>` is the largest signed CTE.** For Akre and Polen it is also the largest |CTE| (MA and NVDA). For Jensen, the largest |CTE| is KLAC at −0.70 pp, which reduces TE. The largest signed CTE is MU at +0.67 pp, the name that adds most to TE, so the row uses MU.
5. **`answers.csv` row order** is figure by figure in Section C's order, the 3 funds in config order within each figure. For `book_quarterly` rows, `source_row` names both books, as `entity=akre|ivv,t=1..28`. `top15_cte_share` names `top=15`.
6. **Numbers that are constants, not results, appear outside placeholders.** Examples: 3 managers, 28 quarters, 84 months, 36-month windows, the 0.90 gate, "2 HAC standard errors", 24 months in the example, 1e-10 relative. D.4's "no number that is not a placeholder" is read as applying to results. The Answers section passes the stricter digit test.
7. **The "below −2 HAC standard errors" claim is in Results, not Answers.** It needs the digit 2, which the Answers digit test forbids. Answers gives the 4 t statistics for Jensen and Polen. The sentence before Table 2 makes the claim.
8. **`run_all.py` does not apply the short-window rule.** It always runs the fit for the 3 funds, which have 83 months. The rule lives in `attribute()`, the only path a short window can take. `report_results` passes `min_factor_months` so `build_report` gets the same keys on both paths.
9. **No step 8.1 run-twice check inside `run_all.py`.** D-01 B says 8.1 "adds only the run-twice check". The check was run by hand: E.5 locally and the fresh clone, with `git status` printed. It is not coded as a function.

## Not verified

- The README on GitHub's renderer. It was read as plain Markdown here: image paths are relative and the tables use standard pipe syntax.
- `--retry-missing` against the network. Only the default skip and the refused flag were run (E.1). With `--retry-missing`, the code path is the 7.3 path that section 7 ran.
- Cross-platform output of this section. Everything ran on Windows. Item 25 already accepts byte differences across operating systems.

## Open questions

1. **D.3 names FICO and CoStar as BusEq names. They are in FF12 Other.** FICO and CoStar (CSGP) both have SIC 7389, which is in no FF12 range, so they are in Other in every quarter held (E.4). The BusEq selection loss comes from Roper, Danaher, CCC and Verisk, in that order. The README names those 4. Options: (a) keep the README as it is; (b) name FICO and CoStar in the Other sentence instead, as part of the weight that drives the interaction.
2. **D.3 says Akre holds 39% to 56% in FF12 Other. The data says 34.0% to 56.2%** (E.4, `brinson_quarterly.csv` `wP`, t = 1 to 28). No `answers.csv` row carries this range, so D.1 gives the README no placeholder for it. The README states the mechanism without the numbers. Options: (a) add 2 rows to `answers.csv`, for example question 1 `other_weight_min` and `other_weight_max` from `brinson_quarterly`, and add the numbers through placeholders; (b) leave the sentence without numbers.
3. **FICO's −48% and the 4 September date have no source row either.** FICO's September 2026 return is −48.4% (E.4, month-end adjusted closes). It is not in any output table, so it cannot be a placeholder under D.1. The Answers digit test also forbids the bare "4" of "4 September". The README says FICO "collapsed after the FHFA's September order". Options: (a) add a question 3 row such as `largest_month_akre` (month, active return) and a FICO return row sourced from `book_monthly.csv` and a new position table, then cite them; (b) keep the wording without numbers.
4. **Polen's correlation prints as 1.00.** D.3 says 0.998. D.1's formats give at most 2 decimals for a plain number, so `num2` rounds 0.998184 to 1.00. Jensen's 0.9996 also prints as 1.00. Options: (a) add a `num3` format for correlations; (b) keep `num2`.

## Files changed

```
config.toml
attrib/config.py
attrib/__init__.py
attrib/report.py
scripts/pull_data.py
scripts/run_all.py
scripts/build_readme.py                           (new)
tests/test_config.py
tests/test_attribute.py
tests/test_answers.py                             (new)
tests/test_readme.py                              (new)
outputs/tables/answers.csv                        (new)
docs/README_template.md                           (new)
docs/METHODS.md                                   (new)
examples/akre_holdings.csv                        (new)
examples/ivv_holdings.csv                         (new)
README.md
CLAUDE.md
review/section_8.md                               (new)
instructions/08_section_8.status.md               (new)
```

## Reviewer reads

1. `instructions/08_section_8.status.md`
2. Open questions above, with E.4
3. E.3 (the README) and `docs/README_template.md`
4. E.2 and `tests/test_answers.py`
5. `scripts/build_readme.py` and `tests/test_readme.py`
6. `docs/METHODS.md`
7. `attrib/__init__.py` (`_run`, Section 5 block), `attrib/report.py` (`_page_2`), `scripts/pull_data.py` (`stage_holdings`)
