# Review — Section 6

## Section

Section 6, Risk, run from `instructions/06_section_6.md`. Precedence (rule 13): that file over the `CLAUDE.md` amendments and `PLAN.md`, which beat the kickoff.

Outcome: **completed.** No rule 4 stop.

- Step 6.0 changed `resid_vol_ann` to the regression standard error. Only that column of `factor_fit.csv` changed (E.7).
- All 3 funds passed the gate in Section 3, so all 3 are in scope at all 28 holdings dates.
- On the real data, Σ CTE = TE holds to 5.6e-17 at worst over all 84 fund-dates, and the sector sums hold to the same bound. `section_6` stops under rule 4 if either misses 1e-12.
- Polen's covariance is ridged at 10 of its 28 dates, 2023-12-31 to 2026-03-31. Akre's and Jensen's never are. E.5 shows why: near-duplicate tickers that Polen's own 13F holds, not the fill rule.
- 2 runs of `run_all.py --section 6` gave byte-identical CSVs and PNGs. The SHA-256 of all 34 files in `outputs/tables` and `outputs/figures` matched.

## Steps completed

- 6.0 `resid_vol_ann` = √(SSR / (n − 7)) × √12; `docs/CONVENTIONS_RESOLVED.md` item 24; `factor_fit.csv` regenerated — `0ece094`
- 6.1 `attrib/risk.py`: `risk_weights`, `ticker_buckets`, `fill_daily`, `active_cov`; `tests/test_risk.py` (4 tests); `real_risk_inputs` in `tests/real_data.py` — `5b3f0a0`
- 6.2 `attrib/risk.py`: `issuer_weights`, `active_share`, `te_decomposition`; 5 more tests; `section_6` in `scripts/run_all.py` writing `risk_quarterly.csv`, `cte_positions.csv`, `cte_sectors.csv`, `te_realised.csv` and Chart 3 per fund — `318a36a`

## Evidence

### Section 6 run

Sections 1 to 5 printed exactly as in `review/section_5.md`. The section 6 output follows. Per fund and date it shows:

- the window length;
- how many tickers were filled;
- the ticker with the largest fill share;
- the condition number before conditioning;
- the ridge added.

```
fill and conditioning per date:
      fund holdings_date  n_days  n_filled max_fill_ticker  max_fill_share   cond_before         ridge
0     akre    2019-09-30     753         8            CTVA        0.883134  3.024854e+03  0.000000e+00
1     akre    2019-12-31     754         6            CTVA        0.798408  3.258117e+03  0.000000e+00
2     akre    2020-03-31     754         6            CTVA        0.716180  1.699158e+03  0.000000e+00
3     akre    2020-06-30     754         7            CARR        0.905836  2.970338e+03  0.000000e+00
4     akre    2020-09-30     755         7            CARR        0.821192  3.237743e+03  0.000000e+00
5     akre    2020-12-31     756         8             VNT        0.910053  3.798287e+03  0.000000e+00
6     akre    2021-03-31     756         8            TDUP        0.996032  3.524616e+03  0.000000e+00
7     akre    2021-06-30     755         8             OGN        0.957616  3.674766e+03  0.000000e+00
8     akre    2021-09-30     756         9             OGN        0.873016  4.231103e+03  0.000000e+00
9     akre    2021-12-31     757         8             OGN        0.788639  4.180744e+03  0.000000e+00
10    akre    2022-03-31     758         6             CEG        0.934037  4.303296e+03  0.000000e+00
11    akre    2022-06-30     757         7            EMBC        0.908851  4.596413e+03  0.000000e+00
12    akre    2022-09-30     757         5             CEG        0.767503  4.755602e+03  0.000000e+00
13    akre    2022-12-31     756         5             BAM        0.973545  5.158245e+03  0.000000e+00
14    akre    2023-03-31     756         4            GEHC        0.904762  6.730404e+03  0.000000e+00
15    akre    2023-06-30     755         4            GEHC        0.822517  5.565679e+03  0.000000e+00
16    akre    2023-09-30     754         6            KVUE        0.864721  5.331604e+03  0.000000e+00
17    akre    2023-12-31     753         5            VLTO        0.920319  5.985252e+03  0.000000e+00
18    akre    2024-03-31     753         6            VLTO        0.839309  5.781933e+03  0.000000e+00
19    akre    2024-06-30     753         7             GEV        0.915007  5.378168e+03  0.000000e+00
20    akre    2024-09-30     753         7            AMTM        0.994688  5.152472e+03  0.000000e+00
21    akre    2024-12-31     753         6             GEV        0.745020  4.909937e+03  0.000000e+00
22    akre    2025-03-31     751         6            SNDK        0.958722  4.458741e+03  0.000000e+00
23    akre    2025-06-30     751         6             RAL        0.996005  4.015887e+03  0.000000e+00
24    akre    2025-09-30     751         5             GEV        0.496671  3.381704e+03  0.000000e+00
25    akre    2025-12-31     752         7               Q        0.940160  2.926847e+03  0.000000e+00
26    akre    2026-03-31     751         7               Q        0.858855  2.927926e+03  0.000000e+00
27    akre    2026-06-30     751         8            HONA        0.986684  3.025963e+03  0.000000e+00
28  jensen    2019-09-30     753         6            CTVA        0.883134  3.047698e+03  0.000000e+00
29  jensen    2019-12-31     754         5            CTVA        0.798408  3.341972e+03  0.000000e+00
30  jensen    2020-03-31     754         5            CTVA        0.716180  1.667173e+03  0.000000e+00
31  jensen    2020-06-30     754         7            CARR        0.905836  2.753731e+03  0.000000e+00
32  jensen    2020-09-30     755         7            CARR        0.821192  2.868341e+03  0.000000e+00
33  jensen    2020-12-31     756         8             VNT        0.910053  3.374486e+03  0.000000e+00
34  jensen    2021-03-31     756         7            CARR        0.656085  3.483119e+03  0.000000e+00
35  jensen    2021-06-30     755         8             OGN        0.957616  3.622798e+03  0.000000e+00
36  jensen    2021-09-30     756         9             OGN        0.873016  4.202166e+03  0.000000e+00
37  jensen    2021-12-31     757         8             OGN        0.788639  4.166046e+03  0.000000e+00
38  jensen    2022-03-31     758         5             CEG        0.934037  4.284886e+03  0.000000e+00
39  jensen    2022-06-30     757         5            EMBC        0.908851  4.523379e+03  0.000000e+00
40  jensen    2022-09-30     757         4             CEG        0.767503  4.731044e+03  0.000000e+00
41  jensen    2022-12-31     756         4             CEG        0.683862  6.419985e+03  0.000000e+00
42  jensen    2023-03-31     756         3            GEHC        0.904762  6.738921e+03  0.000000e+00
43  jensen    2023-06-30     755         3            GEHC        0.822517  5.582294e+03  0.000000e+00
44  jensen    2023-09-30     754         5            KVUE        0.864721  5.392023e+03  0.000000e+00
45  jensen    2023-12-31     753         4            VLTO        0.920319  6.017241e+03  0.000000e+00
46  jensen    2024-03-31     753         4            VLTO        0.839309  5.670965e+03  0.000000e+00
47  jensen    2024-06-30     753         6             GEV        0.915007  5.396762e+03  0.000000e+00
48  jensen    2024-09-30     753         7            AMTM        0.994688  5.175766e+03  0.000000e+00
49  jensen    2024-12-31     753         6             GEV        0.745020  4.870782e+03  0.000000e+00
50  jensen    2025-03-31     751         6            SNDK        0.958722  4.412195e+03  0.000000e+00
51  jensen    2025-06-30     751         6             RAL        0.996005  3.946146e+03  0.000000e+00
52  jensen    2025-09-30     751         5             GEV        0.496671  3.344876e+03  0.000000e+00
53  jensen    2025-12-31     752         8               Q        0.940160  3.880067e+03  0.000000e+00
54  jensen    2026-03-31     751         8               Q        0.858855  3.810717e+03  0.000000e+00
55  jensen    2026-06-30     751         9            HONA        0.986684  3.864034e+03  0.000000e+00
56   polen    2019-09-30     753        28              DT        0.945551  3.695536e+03  0.000000e+00
57   polen    2019-12-31     754        27            NVST        0.904509  3.930966e+03  0.000000e+00
58   polen    2020-03-31     754        30            REYN        0.945623  2.661956e+03  0.000000e+00
59   polen    2020-06-30     754        33            CARR        0.905836  3.109361e+03  0.000000e+00
60   polen    2020-09-30     755        37             RKT        0.949669  2.984591e+03  0.000000e+00
61   polen    2020-12-31     756        44            ALGM        0.943122  4.248760e+03  0.000000e+00
62   polen    2021-03-31     756        53            SANA        0.949735  3.343913e+03  0.000000e+00
63   polen    2021-06-30     755        56              DV        0.935099  8.724390e+03  0.000000e+00
64   polen    2021-09-30     756        60             CNM        0.935185  9.441831e+03  0.000000e+00
65   polen    2021-12-31     757        61            RIVN        0.953765  9.173616e+03  0.000000e+00
66   polen    2022-03-31     758        59            RIVN        0.872032  9.587894e+03  0.000000e+00
67   polen    2022-06-30     757        53             GFS        0.778071  9.377396e+03  0.000000e+00
68   polen    2022-09-30     757        47             GFS        0.693527  5.858143e+05  0.000000e+00
69   polen    2022-12-31     756        49             MBC        0.981481  1.066993e+04  0.000000e+00
70   polen    2023-03-31     756        51            GEHC        0.904762  1.729144e+04  0.000000e+00
71   polen    2023-06-30     755        43            GEHC        0.822517  1.481844e+04  0.000000e+00
72   polen    2023-09-30     754        34            CAVA        0.903183  1.437942e+04  0.000000e+00
73   polen    2023-12-31     753        29            BIRK        0.926959  2.089072e+07  1.074860e-07
74   polen    2024-03-31     753        25            BIRK        0.845950  1.889424e+07  1.027907e-07
75   polen    2024-06-30     753        17            GRAL        0.985392  1.784997e+07  1.021616e-07
76   polen    2024-09-30     753        13            LOAR        0.856574  2.110279e+07  1.066171e-07
77   polen    2024-12-31     753        13            INGM        0.938911  7.265845e+06  9.559042e-08
78   polen    2025-03-31     751        10            INGM        0.858855  1.561713e+07  9.165885e-08
79   polen    2025-06-30     751        21            RHLD        0.884154  9.674642e+06  1.124956e-07
80   polen    2025-09-30     751        27             NIQ        0.936085  9.347277e+06  1.029181e-07
81   polen    2025-12-31     752        30            FIGR        0.897606  9.044262e+06  9.700222e-08
82   polen    2026-03-31     751        29            OFRM        0.952064  2.095464e+07  1.036602e-07
83   polen    2026-06-30     751        33            SPCX        0.985353  1.446335e+04  0.000000e+00
largest |sum CTE - TE| over funds and dates and over sector sums: np.float64(5.551115123125783e-17)
section 6: all checks passed
```

### E.1 `risk_quarterly.csv` (Table 3) in full

The columns are in Section C order: the 2 new columns come right after `active_share`.

- `unmapped_weight_*` is the Convention 4.5 weight of the `no_match` rows. Each such row is its own issuer in the active share.
- `excluded_weight_*` is the Unmapped plus Unpriced weight that risk leaves out (Convention 4.18).
- `n_names` is the number of tickers in the union of the 2 books' priced, mapped tickers. That is also the dimension of Σ (Deviation 1).

```
      fund holdings_date  active_share  unmapped_weight_fund  unmapped_weight_bench  te_exante  excluded_weight_fund  excluded_weight_bench  n_names  max_fill_share  delta_lw  ridged
0     akre    2019-09-30      0.955386              0.000054               0.014817   0.062405              0.003761               0.041684      452        0.883134  0.114575   False
1     akre    2019-12-31      0.955177              0.000000               0.014029   0.063773              0.007186               0.036303      457        0.798408  0.111404   False
2     akre    2020-03-31      0.951194              0.000000               0.010862   0.068520              0.012230               0.031404      459        0.716180  0.468177   False
3     akre    2020-06-30      0.949819              0.000000               0.010609   0.073553              0.014800               0.026920      463        0.905836  0.302005   False
4     akre    2020-09-30      0.950289              0.000000               0.010964   0.075027              0.016689               0.026419      463        0.821192  0.275736   False
5     akre    2020-12-31      0.954220              0.000000               0.010840   0.076578              0.018502               0.026963      466        0.910053  0.235608   False
6     akre    2021-03-31      0.957351              0.000000               0.010804   0.080009              0.018733               0.027243      467        0.996032  0.230248   False
7     akre    2021-06-30      0.950166              0.000288               0.009317   0.080989              0.018432               0.025799      471        0.957616  0.223963   False
8     akre    2021-09-30      0.949935              0.000000               0.009166   0.081654              0.016687               0.023250      472        0.873016  0.192963   False
9     akre    2021-12-31      0.953473              0.000000               0.007557   0.083144              0.019270               0.021403      473        0.788639  0.189764   False
10    akre    2022-03-31      0.956652              0.000000               0.007645   0.090070              0.018643               0.019823      476        0.934037  0.181249   False
11    akre    2022-06-30      0.955859              0.000000               0.006882   0.091697              0.006410               0.018877      481        0.908851  0.174565   False
12    akre    2022-09-30      0.957354              0.000000               0.006476   0.090685              0.005108               0.018438      477        0.767503  0.169005   False
13    akre    2022-12-31      0.960008              0.000000               0.005256   0.096449              0.004941               0.015410      482        0.973545  0.161687   False
14    akre    2023-03-31      0.961099              0.000000               0.005597   0.090680              0.005423               0.014515      482        0.904762  0.083781   False
15    akre    2023-06-30      0.961085              0.000000               0.005096   0.087728              0.006156               0.013448      483        0.822517  0.085101   False
16    akre    2023-09-30      0.967104              0.000000               0.004770   0.090137              0.007179               0.013292      483        0.864721  0.091135   False
17    akre    2023-12-31      0.967122              0.000000               0.004030   0.089535              0.006497               0.010456      486        0.920319  0.081316   False
18    akre    2024-03-31      0.964612              0.000000               0.003366   0.087990              0.006550               0.009461      489        0.839309  0.083098   False
19    akre    2024-06-30      0.968088              0.000000               0.002761   0.093625              0.004391               0.006979      490        0.915007  0.085539   False
20    akre    2024-09-30      0.967483              0.000000               0.002583   0.093856              0.001546               0.006509      492        0.994688  0.085457   False
21    akre    2024-12-31      0.966850              0.000000               0.002106   0.094953              0.000746               0.006150      493        0.745020  0.088888   False
22    akre    2025-03-31      0.963688              0.000000               0.001998   0.087736              0.000140               0.006388      494        0.958722  0.095449   False
23    akre    2025-06-30      0.965031              0.000000               0.001987   0.094126              0.000000               0.005078      495        0.996005  0.122343   False
24    akre    2025-09-30      0.968516              0.000000               0.001572   0.099431              0.000000               0.003166      499        0.496671  0.134409   False
25    akre    2025-12-31      0.970321              0.000000               0.001040   0.101217              0.000000               0.002607      502        0.940160  0.139842   False
26    akre    2026-03-31      0.969660              0.000000               0.000834   0.108819              0.000000               0.002546      503        0.858855  0.140071   False
27    akre    2026-06-30      0.973743              0.000000               0.000000   0.134562              0.000000               0.001123      506        0.986684  0.131569   False
28  jensen    2019-09-30      0.764880              0.000357               0.014817   0.034485              0.000430               0.041684      456        0.883134  0.116900   False
29  jensen    2019-12-31      0.758860              0.000433               0.014029   0.033649              0.000511               0.036303      461        0.798408  0.111501   False
30  jensen    2020-03-31      0.746977              0.000395               0.010862   0.039775              0.000583               0.031404      461        0.716180  0.480485   False
31  jensen    2020-06-30      0.733662              0.000419               0.010609   0.044761              0.000621               0.026920      466        0.905836  0.308594   False
32  jensen    2020-09-30      0.733242              0.000330               0.010964   0.046537              0.000581               0.026419      466        0.821192  0.286815   False
33  jensen    2020-12-31      0.740047              0.000457               0.010840   0.052658              0.000706               0.026963      469        0.910053  0.245825   False
34  jensen    2021-03-31      0.744790              0.000564               0.010804   0.057631              0.000922               0.027243      473        0.656085  0.237764   False
35  jensen    2021-06-30      0.736229              0.000608               0.009317   0.056240              0.001028               0.025799      478        0.957616  0.232537   False
36  jensen    2021-09-30      0.728816              0.000783               0.009166   0.056277              0.000783               0.023250      480        0.873016  0.199658   False
37  jensen    2021-12-31      0.714589              0.000786               0.007557   0.055917              0.000786               0.021403      481        0.788639  0.195510   False
38  jensen    2022-03-31      0.716916              0.000895               0.007645   0.056982              0.000895               0.019823      485        0.934037  0.187370   False
39  jensen    2022-06-30      0.714294              0.000999               0.006882   0.055449              0.000999               0.018877      488        0.908851  0.181377   False
40  jensen    2022-09-30      0.718994              0.000942               0.006476   0.057334              0.000942               0.018438      486        0.767503  0.174060   False
41  jensen    2022-12-31      0.729365              0.000969               0.005256   0.056584              0.000969               0.015410      493        0.683862  0.165768   False
42  jensen    2023-03-31      0.721042              0.001034               0.005597   0.053187              0.001034               0.014515      490        0.904762  0.085696   False
43  jensen    2023-06-30      0.711800              0.001008               0.005096   0.051172              0.001008               0.013448      491        0.822517  0.086391   False
44  jensen    2023-09-30      0.719621              0.000926               0.004770   0.051853              0.000926               0.013292      492        0.864721  0.092444   False
45  jensen    2023-12-31      0.721545              0.000935               0.004030   0.051450              0.000935               0.010456      495        0.920319  0.082530   False
46  jensen    2024-03-31      0.728975              0.000979               0.003366   0.054668              0.000979               0.009461      496        0.839309  0.086816   False
47  jensen    2024-06-30      0.712671              0.000474               0.002761   0.057998              0.000474               0.006979      500        0.915007  0.089325   False
48  jensen    2024-09-30      0.715050              0.000095               0.002583   0.059534              0.000095               0.006509      501        0.994688  0.088330   False
49  jensen    2024-12-31      0.717333              0.000415               0.002106   0.064324              0.000415               0.006150      501        0.745020  0.091870   False
50  jensen    2025-03-31      0.723605              0.000455               0.001998   0.060053              0.000455               0.006388      501        0.958722  0.099078   False
51  jensen    2025-06-30      0.684027              0.000551               0.001987   0.056979              0.000551               0.005078      502        0.996005  0.126799   False
52  jensen    2025-09-30      0.657188              0.000576               0.001572   0.056512              0.000576               0.003166      507        0.496671  0.138798   False
53  jensen    2025-12-31      0.588233              0.000762               0.001040   0.047591              0.000762               0.002607      510        0.940160  0.142734   False
54  jensen    2026-03-31      0.604651              0.000570               0.000834   0.048792              0.000570               0.002546      510        0.858855  0.141215   False
55  jensen    2026-06-30      0.615721              0.000507               0.000000   0.057537              0.000507               0.001123      513        0.986684  0.131413   False
56   polen    2019-09-30      0.728359              0.000135               0.014844   0.040440              0.000177               0.045211      456        0.945551  0.154982   False
57   polen    2019-12-31      0.715778              0.000113               0.012891   0.042183              0.000113               0.037752      461        0.904509  0.148302   False
58   polen    2020-03-31      0.707240              0.000177               0.010131   0.046982              0.000177               0.032489      464        0.945623  0.343109   False
59   polen    2020-06-30      0.680891              0.000271               0.010380   0.052837              0.000271               0.031257      387        0.905836  0.216088   False
60   polen    2020-09-30      0.681849              0.000303               0.010594   0.056539              0.000303               0.031099      391        0.949669  0.209579   False
61   polen    2020-12-31      0.689249              0.000292               0.011139   0.059747              0.000292               0.030540      402        0.943122  0.199269   False
62   polen    2021-03-31      0.626392              0.000654               0.010991   0.055714              0.000654               0.029535      410        0.949735  0.192160   False
63   polen    2021-06-30      0.637800              0.000598               0.010782   0.057806              0.000598               0.024779      457        0.935099  0.133832   False
64   polen    2021-09-30      0.647447              0.000795               0.009633   0.056511              0.000795               0.019811      467        0.935185  0.127337   False
65   polen    2021-12-31      0.663607              0.000812               0.007952   0.058692              0.000812               0.016896      473        0.953765  0.128879   False
66   polen    2022-03-31      0.677776              0.000889               0.006447   0.064367              0.000889               0.014036      474        0.872032  0.129985   False
67   polen    2022-06-30      0.694986              0.000761               0.006973   0.070073              0.000761               0.018333      495        0.778071  0.141063   False
68   polen    2022-09-30      0.703176              0.000697               0.006913   0.078091              0.000697               0.017794      496        0.693527  0.137440   False
69   polen    2022-12-31      0.712126              0.000712               0.005386   0.076945              0.000712               0.014655      502        0.981481  0.132613   False
70   polen    2023-03-31      0.712981              0.000433               0.005079   0.080554              0.000433               0.013133      506        0.904762  0.086550   False
71   polen    2023-06-30      0.697651              0.000324               0.003429   0.075451              0.000324               0.010164      461        0.822517  0.092219   False
72   polen    2023-09-30      0.681716              0.000237               0.002635   0.067106              0.000237               0.010280      463        0.903183  0.095264   False
73   polen    2023-12-31      0.659831              0.000200               0.002258   0.062841              0.000200               0.005486      474        0.926959  0.090577    True
74   polen    2024-03-31      0.656199              0.000313               0.001789   0.062708              0.000313               0.003793      471        0.845950  0.095328    True
75   polen    2024-06-30      0.654932              0.000341               0.001129   0.071228              0.000341               0.002834      475        0.985392  0.100258    True
76   polen    2024-09-30      0.666356              0.000432               0.001296   0.079152              0.000432               0.002586      440        0.856574  0.054221    True
77   polen    2024-12-31      0.648728              0.000171               0.001348   0.082397              0.000171               0.002506      444        0.938911  0.083953    True
78   polen    2025-03-31      0.683312              0.000161               0.001215   0.081751              0.000161               0.002679      438        0.858855  0.094426    True
79   polen    2025-06-30      0.708051              0.000833               0.001038   0.097283              0.000833               0.001223      531        0.884154  0.109963    True
80   polen    2025-09-30      0.625161              0.000743               0.000911   0.078327              0.000743               0.000928      534        0.936085  0.105136    True
81   polen    2025-12-31      0.610309              0.000698               0.001022   0.069204              0.000698               0.001057      543        0.897606  0.123589    True
82   polen    2026-03-31      0.593295              0.001295               0.000852   0.068201              0.001295               0.000852      540        0.952064  0.123726    True
83   polen    2026-06-30      0.617790              0.002927               0.000022   0.084263              0.002927               0.000231      491        0.985353  0.115814   False
```

### E.2 `te_realised.csv` in full

```
     fund  te_realised  te_exante_mean  n_months
0    akre     0.103945        0.088177        83
1  jensen     0.052394        0.052712        83
2   polen     0.064250        0.067050        83
```

Section C fixes the sample at the 83 months, October 2019 to August 2026, which is the Section 5 monthly sample. `book_monthly.csv` also has September 2026. For comparison only, the same statistic over all 84 book months is below. Nothing writes it to a file:

```
     fund  te_realised_84  n_months_84    first     last
0    akre        0.114092           84  2019-10  2026-09
1  jensen        0.052607           84  2019-10  2026-09
2   polen        0.065670           84  2019-10  2026-09
```

Akre's figure moves by 1 point because its book trails IVV by 13.3% in September 2026 alone. That is the largest monthly active return of any fund (Deviation 2).

### E.3 Top 15 CTE rows at h = 2026-06-30

The rows are sorted by |CTE|, with ties broken by ticker. `a` is the risk weight difference; `mcte` and `cte` are in annualised TE units.

```
akre: TE = np.float64(0.1345624243935982), sum CTE over all 506 tickers = np.float64(0.1345624243935956), top 15 sum = np.float64(0.10236738907369511), share of TE = np.float64(0.7607427521836864)
   ticker bucket         a      mcte       cte
0      MA  Other  0.193689  0.079407  0.015380
1    NVDA  BusEq -0.075271 -0.203778  0.015338
2    FICO  Other  0.084222  0.154472  0.013010
3     MCO  Other  0.101546  0.089415  0.009080
4    CSGP  Other  0.064699  0.122605  0.007932
5     ROP  BusEq  0.077430  0.075400  0.005838
6     KKR  Money  0.088541  0.062470  0.005531
7    AVGO  BusEq -0.027778 -0.197459  0.005485
8      MU  BusEq -0.020220 -0.267388  0.005406
9       V  Other  0.065787  0.065506  0.004309
10    AMD  BusEq -0.014712 -0.230620  0.003393
11     BN  Money  0.101077  0.030346  0.003067
12    CCC  BusEq  0.030170  0.098552  0.002973
13   AAPL  BusEq -0.066008 -0.044367  0.002929
14  GOOGL  BusEq -0.032546 -0.082783  0.002694
jensen: TE = np.float64(0.0575370576385392), sum CTE over all 513 tickers = np.float64(0.057537057638533784), top 15 sum = np.float64(0.021009041719240496), share of TE = np.float64(0.3651393133660752)
   ticker bucket         a      mcte       cte
0    KLAC  BusEq  0.051718 -0.135380 -0.007002
1      MU  BusEq -0.020220 -0.332426  0.006721
2    TSLA  Durbl -0.018391 -0.247037  0.004543
3     AMD  BusEq -0.014712 -0.255708  0.003762
4    NVDA  BusEq -0.017156 -0.156271  0.002681
5    INTC  BusEq -0.010246 -0.247994  0.002541
6     APH  BusEq  0.022917 -0.087531 -0.002006
7    MRSH  Money  0.038567  0.051466  0.001985
8   GOOGL  BusEq  0.036544 -0.050161 -0.001833
9    LRCX  Manuf -0.008417 -0.208014  0.001751
10   SNDK  BusEq -0.005229 -0.324362  0.001696
11   AMAT  BusEq -0.008911 -0.183773  0.001638
12   GOOG  BusEq -0.025937 -0.060724  0.001575
13    SYK   Hlth  0.043341  0.035707  0.001548
14     WM  Other  0.032834  0.042906  0.001409
polen: TE = np.float64(0.0842633803188094), sum CTE over all 491 tickers = np.float64(0.0842633803188076), top 15 sum = np.float64(0.0644543329002469), share of TE = np.float64(0.76491511088666)
   ticker bucket         a      mcte       cte
0    NVDA  BusEq -0.069753 -0.249619  0.017412
1      MU  BusEq -0.038613 -0.374743  0.014470
2     AMD  BusEq -0.028020 -0.314848  0.008822
3    TSLA  Durbl -0.036136 -0.244021  0.008818
4   GOOGL  BusEq -0.060936 -0.096874  0.005903
5    AAPL  BusEq -0.067188 -0.075384  0.005065
6    AMAT  BusEq -0.017009 -0.260578  0.004432
7    LRCX  Manuf  0.016083 -0.272143 -0.004377
8     TSM  BusEq  0.020676 -0.168006 -0.003474
9     NOW  BusEq  0.043030  0.075438  0.003246
10   SNDK  BusEq -0.009779 -0.323214  0.003161
11   KLAC  BusEq -0.011712 -0.252058  0.002952
12   MRVL  BusEq -0.007711 -0.307945  0.002375
13   AVGO  BusEq  0.011811 -0.196354 -0.002319
14   AMZN  Shops  0.052115 -0.038968 -0.002031
```

### E.4 Sector CTE at h = 2026-06-30

There are 12 FF12 rows per fund (Deviation 3), and each set sums to TE:

```
    fund bucket       cte
0   akre  NoDur -0.000481
1   akre  Durbl  0.002622
2   akre  Manuf  0.005083
3   akre  Enrgy  0.000036
4   akre  Chems -0.000275
5   akre  BusEq  0.064857
6   akre  Telcm -0.000236
7   akre  Utils -0.000020
8   akre  Shops  0.006126
9   akre   Hlth -0.000498
10  akre  Money  0.006962
11  akre  Other  0.050385
akre: sum of sector CTE = np.float64(0.13456242439359822), te_exante = np.float64(0.1345624243935982), diff = 2.776e-17
      fund bucket       cte
0   jensen  NoDur  0.000204
1   jensen  Durbl  0.004804
2   jensen  Manuf  0.007568
3   jensen  Enrgy  0.001901
4   jensen  Chems  0.001317
5   jensen  BusEq  0.021756
6   jensen  Telcm  0.000243
7   jensen  Utils  0.000860
8   jensen  Shops  0.000395
9   jensen   Hlth  0.003649
10  jensen  Money  0.009272
11  jensen  Other  0.005568
jensen: sum of sector CTE = np.float64(0.057537057638538606), te_exante = np.float64(0.0575370576385392), diff = 5.967e-16
     fund bucket       cte
0   polen  NoDur  0.000032
1   polen  Durbl  0.008736
2   polen  Manuf -0.005265
3   polen  Enrgy  0.000045
4   polen  Chems -0.000039
5   polen  BusEq  0.075550
6   polen  Telcm  0.000146
7   polen  Utils  0.000540
8   polen  Shops -0.001764
9   polen   Hlth  0.001407
10  polen  Money  0.000624
11  polen  Other  0.004251
polen: sum of sector CTE = np.float64(0.08426338031880926), te_exante = np.float64(0.0842633803188094), diff = 1.388e-16
```

### E.5 Shrinkage, ridging and fill over the 28 dates

```
        delta_lw_min  delta_lw_max  n_ridged  n_dates  max_fill_share_min  max_fill_share_max
fund                                                                                         
akre        0.081316      0.468177         0       28            0.496671            0.996032
jensen      0.082530      0.480485         0       28            0.496671            0.996005
polen       0.054221      0.343109        10       28            0.693527            0.985392
     fund holdings_date  delta_lw  n_names
73  polen    2023-12-31  0.090577      474
74  polen    2024-03-31  0.095328      471
75  polen    2024-06-30  0.100258      475
76  polen    2024-09-30  0.054221      440
77  polen    2024-12-31  0.083953      444
78  polen    2025-03-31  0.094426      438
79  polen    2025-06-30  0.109963      531
80  polen    2025-09-30  0.105136      534
81  polen    2025-12-31  0.123589      543
82  polen    2026-03-31  0.123726      540
```

**Why Polen is ridged.** The table below gives the most correlated pair in Polen's filled window at 3 dates. Every ticker in these pairs has a full history, so none of their returns are filled:

```
2023-12-31 most correlated pair: VONG IWF corr=0.9986870690 fill shares 0.0 0.0 buckets ['Other', 'Other']
2026-03-31 most correlated pair: GOOG GOOGL corr=0.9976893918 fill shares 0.0 0.0 buckets ['BusEq', 'BusEq']
2026-06-30 most correlated pair: SPY VOO corr=0.9981127097 fill shares 0.0 0.0 buckets ['Other', 'Other']
```

Polen's 13F carries small index-ETF positions. IWF itself is held at every date, and VONG, SPY, VOO, VUG, IWM and IVV at some dates. Most active weights are below 0.1%; IWF reaches 1.6%.

Near-duplicate ETF pairs push cond(Σ_d) to about 1e7, above `max_cond` = 1e6. `condition_cov` then adds a ridge of about 1e-7 to the daily matrix.

The largest fill shares belong to tickers that listed inside the 36-month window, mostly spin-offs and IPOs (HONA, RAL, TDUP, AMTM). Their series are almost entirely their bucket's daily mean.

### E.6 Chart 3

![Akre Chart 3](../outputs/figures/akre_cte_top15.png)

![Jensen Chart 3](../outputs/figures/jensen_cte_top15.png)

![Polen Chart 3](../outputs/figures/polen_cte_top15.png)

### E.7 Step 6.0: `resid_vol_ann` before and after

The old values are from `factor_fit.csv` at `19988b5`, the new ones at `0ece094`. Every other column of the file is unchanged.

The ratio is exactly √((n − 1)/(n − 7)), because OLS residuals with a constant have mean 0.

```
other columns unchanged: True
             n_months  resid_vol_ann_old  resid_vol_ann_new  ratio_new_old  sqrt((n-1)/(n-7))
series_id                                                                                    
akre_book          83           0.096548           0.100287       1.038724           1.038724
akre_nav           80           0.092097           0.095807       1.040284           1.040284
jensen_book        83           0.043476           0.045160       1.038724           1.038724
jensen_nav         83           0.044737           0.046470       1.038724           1.038724
polen_book         83           0.053928           0.056017       1.038724           1.038724
polen_nav          83           0.055568           0.057720       1.038724           1.038724
ivv_book           83           0.009860           0.010242       1.038724           1.038724
iwf_book           83           0.032160           0.033405       1.038724           1.038724
```

## Tests run

```
$ .venv/Scripts/python.exe -m pytest -p socket --disable-socket -q
........................................................................ [ 94%]
....                                                                     [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\Utkarsh\10. Quant Projects\6) Attribution Engine On Real Holdings\repo-clone\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
76 passed, 1 warning in 121.04s (0:02:01)
```

The 9 Section 6 tests, by name (`-v`):

```
tests/test_risk.py::test_pc_imports_offline PASSED
tests/test_risk.py::test_fill_rule_synthetic PASSED
tests/test_risk.py::test_cov_symmetric_positive_definite PASSED
tests/test_risk.py::test_fill_share_bounds PASSED
tests/test_risk.py::test_euler_identity PASSED
tests/test_risk.py::test_active_share_identical_is_zero PASSED
tests/test_risk.py::test_active_share_disjoint_is_one PASSED
tests/test_risk.py::test_share_classes_net PASSED
tests/test_risk.py::test_te_matches_direct_quadratic PASSED
```

The real-data tests use the Akre inputs at 2026-06-30. Their `-s` output:

- `test_cov_symmetric_positive_definite`: 506 tickers and 751 days. max|S − S′| = 0, the smallest eigenvalue is 3.67e-4, δ_LW is 0.1316, and the matrix is not ridged.
- `test_fill_share_bounds`: 498 of the 506 tickers have a full history, all with share 0. The other 8 have shares in (0, 1).
- `test_te_matches_direct_quadratic`: Σ CTE = 0.13456242439359828 against a direct value of 0.13456242439359822.

## Fresh-clone check

Per Section F, the 3 step commits were pushed first (`19988b5..318a36a`). `git ls-remote` then returned `318a36aed4939a060fe07aa564587d1205ecf5d8` for `refs/heads/main`, equal to local `HEAD`.

GitHub was cloned into `C:\t\s6`. The install output is trimmed to its last lines, and the `run_all` output to its status lines:

```
$ git clone -q https://github.com/uty101/Attribution-Engine-On-Real-Holdings.git /c/t/s6
$ cd /c/t/s6
$ git log --oneline -1
318a36a step 6.2: active share, ex-ante TE with its Euler split, realised TE and Chart 3
$ uv venv --python 3.12
Using CPython 3.12.13
Creating virtual environment at: .venv
Activate with: .venv\Scripts\activate
$ uv pip install -r requirements-lock.txt
 + websockets==17.1
 + wrapt==2.5.0
 + yfinance==1.7.0
$ uv pip install -e . --no-deps
 + attrib==0.0.0 (from file:///C:/t/s6)
$ .venv/Scripts/python.exe -m pytest -p socket --disable-socket -q
........................................................................ [ 94%]
....                                                                     [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\t\s6\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
76 passed, 1 warning in 123.59s (0:02:03)
$ .venv/Scripts/python.exe scripts/run_all.py --section 6
section 1: all checks passed
section 2: all checks passed
benchmark quarters with |gap| > benchmark_gap_max (0.01):
  entity   t     q_start       q_end  book_return  nav_return       gap  unmapped_weight  unpriced_weight  delisted_weight
0    iwf  27  2026-03-31  2026-06-30      0.15426    0.165848 -0.011588         0.000852              0.0              0.0
section 3: all checks passed
section 4: all checks passed
beta coverage per side, the largest value over the holdings dates:
section 5: all checks passed
largest |sum CTE - TE| over funds and dates and over sector sums: np.float64(5.551115123125783e-17)
section 6: all checks passed
$ git status --short
```

The final `git status --short` printed nothing, so the clone regenerated every committed output byte for byte.

## Runtime per step

Measured on the Windows machine:

- 6.0: `run_all.py --section 5`, about 2 minutes.
- 6.1 and 6.2: `run_all.py --section 6` takes about 2 minutes for sections 1 to 6. The 84 covariances are a small part of that.
- Full suite: 121 s locally, 124 s in the fresh clone. `tests/test_risk.py` alone takes 7 to 10 s.

## Deviations from PLAN.md

1. **`n_names` is the number of tickers in the TE ticker set.** That set is the union of both books' priced, mapped tickers, so `n_names` is also the dimension of Σ. Neither the kickoff nor the instructions define the column.
2. **Realised TE uses the 83 months Section C names**, October 2019 to August 2026. The kickoff says "over the full window", and `book_monthly.csv` has 84 months. E.2 prints the 84-month values for comparison.
3. **`cte_sectors.csv` carries all 12 FF12 buckets per fund and date**, in French's order, with 0 where the TE set has no ticker. This matches `buckets.csv`, which always carries its 14 rows.
4. **Chart 3 sort order and colours:**
   - the 15 bars are selected by |CTE| and sorted by signed CTE, largest at the top, so the negative bars sit together at the bottom;
   - positive bars are red (#d62728) and negative bars blue (#1f77b4), with no legend;
   - {Fund} is the capitalised fund id and {benchmark} the ETF ticker, as on Chart 1.
5. **Issuer keys.** `PLAN.md` 6.2 says the issuer is the first 6 CUSIP characters; amendment 10 and Section C replace that with the CIK. Internally the keys are `cik:<n>` or `sec_id:<id>`, so a CIK and a `sec_id` can never collide. The keys appear in no output file.
6. **Helper functions beyond the fixed signatures.** `attrib/risk.py` adds `risk_weights(pos, smap)`, `ticker_buckets(smap, tickers)` and `issuer_weights(pos, smap)`. `run_all` and the tests share them, so the real-data tests run the same code path. `tests/real_data.py` gains `real_risk_inputs`, which rebuilds Akre and IVV at 2026-06-30 from `data/raw/`.
7. **Call order.**
   - `run_all` takes the window rows with `window_daily(returns, q_start(h), 36)`.
   - It fills them with `fill_daily`, so the fill share is over the window's rows.
   - It passes the filled window to `active_cov`, which applies `window_daily` again (the rows do not change) and then estimates.
   - `active_cov` raises if it is handed a panel with gaps.
8. **The constants 21 and 12** are literals in `attrib/risk.py` (`DAILY_TO_MONTHLY`, `MONTHS_PER_YEAR`), each citing kickoff 5.10. The reason is that `active_cov` and `te_decomposition` have fixed signatures with no config argument (rule 6 exception). `section_6` stops if `risk.daily_to_monthly` or `risk.months_per_year` in `config.toml` differs from them.
9. **Daily returns** come from the existing `daily_returns` (Section 2). Each return is taken from that ticker's previous available close, so after a missing close the next return spans 2 days rather than leaving 2 gaps. No Section 6 window has a day on which none of the union's tickers has a return.

## Not verified

- **Akre's −13.3% active month in September 2026** (E.2) was not traced to positions. It comes from `book_monthly.csv`, which Section 3 built and the reviewer approved; Section 6 only reads it.
- **Heavily filled series.** Some tickers' series are more than 80% their bucket's mean. Their effect on the TE level was not measured beyond the fill shares reported.

## Open questions

1. **`n_names`** (Deviation 1): is the TE ticker-set size the intended definition?
2. **Realised TE sample** (Deviation 2): keep the 83 months, or use all 84 book months? It matters only for Akre: 10.4% against 11.4%.
3. **Polen's ETF holdings** (E.5) cause the ridging at 10 dates, and IWF sits in Polen's own book against an IWF benchmark. They are kept as priced, mapped equity rows, as the rules require. Should they stay?
4. **For the write-up:**
   - Ex-ante TE at 2026-06-30 is 13.5% for Akre, 5.8% for Jensen and 8.4% for Polen.
   - The top 15 positions explain 76% of TE for Akre and Polen, but only 37% for Jensen.
   - Over the 28 dates, the mean ex-ante TE is close to the realised TE for Jensen (5.27% against 5.24%) and Polen (6.71% against 6.43%). It falls short for Akre: 8.82% against 10.39%.
   - GOOG and GOOGL appear separately in Jensen's top 15, with opposite signs. Active share nets them at the CIK, but risk is per ticker (Section C), so the 2 contributions partly offset.

## Files changed

```
 attrib/factors.py                    |     7 +-
 attrib/risk.py                       |   123 +
 docs/CONVENTIONS_RESOLVED.md         |     1 +
 outputs/figures/akre_cte_top15.png   |   Bin 0 -> 50865 bytes
 outputs/figures/jensen_cte_top15.png |   Bin 0 -> 51363 bytes
 outputs/figures/polen_cte_top15.png  |   Bin 0 -> 51887 bytes
 outputs/tables/cte_positions.csv     | 40255 +++++++++++++++++++++++++++++++++
 outputs/tables/cte_sectors.csv       |  1009 +
 outputs/tables/factor_fit.csv        |   112 +-
 outputs/tables/risk_quarterly.csv    |    85 +
 outputs/tables/te_realised.csv       |     4 +
 scripts/run_all.py                   |   141 +-
 tests/real_data.py                   |    40 +
 tests/test_risk.py                   |   164 +
```

Plus this file and `instructions/06_section_6.status.md`.

## Reviewer reads

1. `attrib/risk.py`: the whole Section 6 method, in about 120 lines.
2. `section_6`, `realised_te` and `chart_3` in `scripts/run_all.py`: how the inputs are assembled per fund and date.
3. `tests/test_risk.py`: the 9 tests.
4. E.1, E.2 and E.5 above, then the 3 charts under E.6.
