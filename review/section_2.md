# Review — Section 2

## Section

Section 2, Mapping, sectors, prices and factors. **Completed.** `python scripts/run_all.py --section 2` passes every check. Every step of instructions 02, 02b and 02c is built:

- the security map, now with 3 fallback passes after OpenFIGI's first pass;
- the fund NAV series, with Akre's taken from its own N-PORT returns;
- prices, the quarter calendar and monthly returns;
- the coverage mapping columns and the review lists.

This file replaces the session 2 and 2b reviews and covers all of Section 2.

The section stopped twice before finishing:

- Session 2 stopped at 2.3 because yfinance has no AKRIX data. 02b resolved it with OPEN-31 (c).
- Session 2b stopped at 2.1b because Akre has no NAV return for 2025-08 to 2025-10. 02c resolved it with OPEN-33 (b), accepting the gap.

The evidence for both stops is in the git history (`764b38b`, `264f520`) and is summarised under "Stops, for the record".

What the reviewer needs to act on:

- 254 `sec_id`s remain unmatched. 52 books keep `unmapped_weight` above 2%: Akre to 2022-09, IVV to 2024-09, IWF to 2022-12, and 4 Jensen books. `unmapped_top.csv` lists the 60 largest, for the ticker overrides of instruction 03.
- The name check of 02b rejects 12 results. Some of them are the right company under a changed name: Exxon, GE, National Oilwell Varco, Quidel and Liberty Formula One. See Open questions.

## Steps completed

- 2.1 `--stage figi` and `--stage sec`, `data/raw/openfigi/mapping.csv`, `sic.csv` — `0b64589`
- 2.2 `attrib/mapping.py`, `--stage french`, `tests/test_mapping.py`, `security_map.csv` via `run_all.py --section 2` — `097028f`
- 2.3 `--stage prices`, the price and French loaders, `tests/test_data_loaders.py` (session 2 stop) — `c233354`
- 2.1b `parse_nport` B.5 returns, `--stage navret`, `nav_source` and `etf_successor` config keys, `tests/test_nav_returns.py` (session 2b stop) — `b8cd7e2`
- 2.0c 02c decisions: `CLAUDE.md` amendment 11, `decisions/OPEN.md` pointer line, `decisions/section_2_review.md` — `035da83`
- 2.1c `other_id` in HOLDINGS_RAW_NPORT and `--stage edgar` rerun, `--stage figi2` (passes 2 to 4 with name check), `data/raw/openfigi/fallback.csv`, `build_security_map(figi, fallback, overrides, tickers, sic, ff12)`, 3 new tests, `--stage sec` rerun — `e21e4c1`
- 2.3b `--stage prices` on the extended map; `nav_adjclose.csv` with JENIX, POLIX, IVV, IWF, AKRE — `6d637e2`
- 2.1b-2 `outputs/tables/nav_monthly.csv`, class-page URLs in the manifest, the B.5 cross-check — `da938d2`
- 2.4 `quarter_calendar`, `daily_returns`, `tests/test_returns_calendar.py` (`monthly_returns` came in 2.1b-2) — `3853eff`
- 2.5 the mapping columns of `coverage.csv`, `unmapped_top.csv` (60), `unpriced_top.csv`, `nocik_top.csv`, `large_moves.csv` — `8f996a0`

## Evidence

### Section 2 run

`python scripts/run_all.py --section 2`, exit code 0, about 20 s:

```
section 1: all checks passed
section 2: all checks passed
```

The section 2 check is the 02c stop rule. A `nport` fund may miss only the months 2025-08 to 2025-10, and it passes. Two runs in a row gave byte-identical files (sha256 prefixes):

```
True 7FACD20083ECAD24 outputs\tables\coverage.csv
True FFA48BD0EA8FC4BE outputs\tables\unmapped_top.csv
True EFC75AEDDC362978 outputs\tables\unpriced_top.csv
True ECA60976A01CE84B outputs\tables\nocik_top.csv
True 95D7A7CE41A8DEC4 outputs\tables\large_moves.csv
True 26395B50CD2CD8EB outputs\tables\nav_monthly.csv
True DE9DD41707200A34 data\processed\security_map.csv
```

### Stops, for the record

Session 2, step 2.3: `stop under rule 4: yfinance returned no data for ['AKRIX']: {}`. AKRIX, AKREX and AKRSX return 0 rows; AKRE exists from 2025-10-27.

Session 2b, step 2.1b: Akre's last NPORT-P (`0000894189-25-009200`, filed 2025-09-26) is for period 2025-07-31. Its series then filed only an N-CSR, a 24F-2NT and an N-CEN in October 2025. So 2025-08, 2025-09 and 2025-10 have no return, against a limit of 1 missing month. 02c accepted the gap.

### 2.1c EDGAR rerun: 13F XML byte-identical

`--stage edgar` was rerun for `other_id` (1 min 58 s). Comparing `MANIFEST.json` before and after:

```
96 13F XML; identical: 96
changed files: ['edgar/nport/holdings_ivv.csv', 'edgar/nport/holdings_iwf.csv']
new/removed: set()
```

`python scripts/run_all.py --section 1` still passes, and `coverage.csv` columns through `isin_only_weight` are unchanged.

### Test prints: fallback precedence and name check

```
          ticker                    source map_status
sec_id
00000000A    P1A                  openfigi     mapped
00000000B    P2B                 figi_isin     mapped
00000000C    P3C               figi_noexch     mapped
00000000D    P4D                yahoo_isin     mapped
00000000E    OVR  openfigi;override_ticker     mapped
      sec_id  pass    query_type   query_value  rank ticker              name exch_code market_sector security_type  accepted                  reject_reason
0  G1151C101     4  yahoo_search  IE00B4BNMY34     1   ACNB  ACNB Corporation       NMS                      EQUITY     False  name check: ACCENTURE != ACNB
1  G1151C101     4  yahoo_search  IE00B4BNMY34     2    ACN     Accenture plc       NYQ                      EQUITY      True
```

### 2.1 and 2.1c distinct sec_ids per entity, by id_type and map_status (all 28 books)

```
map_status    mapped  no_match  no_cik  no_sic
akre   cusip      39         9       0       0
jensen cusip     122        16       2       1
polen  cusip     477        59      30       1
ivv    cusip     540        63      12       0
       isin       36         9       1       0
iwf    cusip     822       151      28       0
       isin       32         7       2       0
```

### 2.1c SECURITY_MAP over all 1622 sec_ids: map_status, source

```
  id_type map_status     n
0   cusip     mapped  1249
1   cusip     no_cik    61
2   cusip   no_match   242
3   cusip     no_sic     1
4    isin     mapped    54
5    isin     no_cik     3
6    isin   no_match    12

        source     n
0     openfigi  1522
1    figi_isin    46
2  figi_noexch    30
3   yahoo_isin    24
```

### 2.1 sic.csv: CIKs with and without SIC

```
   ciks  with_sic  without_sic
0  1258      1257            1

        cik                    name sic sic_description
366  884394  SPDR S&P 500 ETF TRUST
```

### 2.1c per pass: sec_ids queried, accepted and rejected

```
pass  sec_ids_queried  accepted  rejected
   2              310        46       264
   3              308        30       278
   4              234        24       210

sec_ids with no pass-1 equity result: 354; accepted by a fallback pass: 100; still no_match: 254
fallback.csv rows: 2519

reject reasons over all rejected rows:
                    reject_reason  rows
0  exchCode 'X' is not a US venue  1579
1            No identifier found.   367
2  an earlier result was accepted   263
3                       no result   185
4  exchange 'X' is not a US venue    13
5     name check: <tokens differ>    12
```

### 2.1c the 20 largest accepted fallback mappings, by maximum weight

```
      sec_id pass  query_value ticker exch_code                                 holding_name                                    result_name  max_weight entity period_date
   G1151C101    2 IE00B4BNMY34    ACN        US                        Accenture plc Class A                             ACCENTURE PLC-CL A    0.072669 jensen  2024-12-31
   G0403H108    2 IE00BLP1HW54    AON        US                                      AON PLC                                AON PLC-CLASS A    0.037693  polen  2025-03-31
   G4705A100    2 IE0005711209   ICLR        US                                     ICON PLC                                       ICON PLC    0.009100  polen  2023-06-30
   25401T603    4 US25401T6038   DBRG       NYQ                      DIGITALBRIDGE GROUP INC                      DigitalBridge Group, Inc.    0.007179   akre  2023-09-30
   151020104    3    151020104   CELG        UW                                 Celgene Corp                                   CELGENE CORP    0.005011    iwf  2019-09-30
   438516106    4 US4385161066    HON       NMS                  Honeywell International Inc                   Honeywell International Inc.    0.004927    ivv  2019-09-30
   L8681T102    2 LU1778762911   SPOT        US                      SPOTIFY TECHNOLOGY S.A.                          SPOTIFY TECHNOLOGY SA    0.004009    iwf  2025-06-30
   G96629103    2 IE00BDB6Q211    WTW        US                 WILLIS TOWERS WATSON PLC LTD                       WILLIS TOWERS WATSON PLC    0.003890  polen  2025-03-31
   L44385109    2 LU0974299876   GLOB        US                                  GLOBANT S A                                     GLOBANT SA    0.003676  polen  2024-12-31
   G8994E103    2 IE00BK9ZQ967     TT        US                       TRANE TECHNOLOGIES PLC                         TRANE TECHNOLOGIES PLC    0.003357    iwf  2026-03-31
GB00B5BT0K07    4 GB00B5BT0K07    AON       NYQ                                      Aon PLC                                        Aon plc    0.003252    iwf  2019-09-30
   V7780T103    2 LR0008862868    RCL        US                 ROYAL CARIBBEAN CRUISES LTD.                    ROYAL CARIBBEAN CRUISES LTD    0.002629    iwf  2025-09-30
   647581107    4 US6475811070    EDU       NYQ                 NEW ORIENTAL ED & TECHNOLOGY New Oriental Education & Technology Group Inc.    0.002275  polen  2020-12-31
IE00B6330302    4 IE00B6330302     IR       NYQ                           Ingersoll-Rand PLC                            Ingersoll Rand Inc.    0.002007    iwf  2019-09-30
   G54950103    2 IE000S9YS762    LIN        US                 LINDE PUBLIC LIMITED COMPANY                                      LINDE PLC    0.001894    iwf  2023-03-31
   G6683N103    2 KYG6683N1034     NU        US                              Nu Holdings Ltd                   NU HOLDINGS LTD/CAYMAN ISL-A    0.001862    iwf  2025-12-31
   42809H107    3    42809H107    HES        UA                             HESS CORPORATION                                      HESS CORP    0.001825    iwf  2022-12-31
   931427108    3    931427108    WBA        UW                 Walgreens Boots Alliance Inc                   WALGREENS BOOTS ALLIANCE INC    0.001696    ivv  2019-09-30
   G3643J108    2 IE00BWT6H894   FLUT        US FLUTTER ENTERTAINMENT PUBLIC LIMITED COMPANY                   FLUTTER ENTERTAINMENT PLC-DI    0.001407    iwf  2025-06-30
   G25457105    2 KYG254571055   CRDO        US           Credo Technology Group Holding Ltd                   CREDO TECHNOLOGY GROUP HOLDI    0.001329    iwf  2026-06-30
```

### 2.1c every name-check rejection

```
   sec_id pass  query_value ticker                            name exch_code                       reject_reason                           holding_name
054937107    4 US0549371070    BBT    Beacon Financial Corporation       NYQ            name check: BB != BEACON                              BB&T Corp
30231G102    4 US30231G1022    XOM ExxonMobil Holdings Corporation       NYQ     name check: EXXON != EXXONMOBIL                      Exxon Mobil Corp.
369604103    4 US3696041033     GE                    GE Aerospace       NYQ           name check: GENERAL != GE                    General Electric Co
501797104    4 US5017971046     LB          LandBridge Company LLC       NYQ         name check: L != LANDBRIDGE                           L Brands Inc
531229854    4 US5312298541  FWONK               Formula One Group       NMS      name check: LIBERTY != FORMULA LIBERTY MEDIA CORP - FORMULA ONE GROUP
531229870    4 US5312298707  FWONA               Formula One Group       NMS      name check: LIBERTY != FORMULA Liberty Media Corp-Liberty Formula One
637071101    4 US6370711011    NOV                        NOV Inc.       NYQ         name check: NATIONAL != NOV             National Oilwell Varco Inc
72941B106    4 US72941B1061     PS            Pershing Square Inc.       NYQ name check: PLURALSIGHT != PERSHING                        Pluralsight Inc
74838J101    4 US74838J1016   QDEL         QuidelOrtho Corporation       NMS   name check: QUIDEL != QUIDELORTHO                            Quidel Corp
81761R109    4 US81761R1095   SERV             Serve Robotics Inc.       NCM  name check: SERVICEMASTER != SERVE      ServiceMaster Global Holdings Inc
867914103    4 US8679141031    STI       Solidion Technology, Inc.       NCM    name check: SUNTRUST != SOLIDION                     SunTrust Banks Inc
87236Y108    4 US87236Y1082   AMTD                 AMTD IDEA Group       NYQ              name check: TD != AMTD             TD Ameritrade Holding Corp
```

### 2.1b fund series resolution (data/raw/edgar/nport_returns/series_resolved.csv)

```
   entity nav_ticker      cik   series_id    class_id           class_name                 found_by                                                       series_classes etf_class_ids
0    akre      AKRIX   811030  S000026760  C000080287  Institutional Class  company_tickers_mf.json                   C000080286:AKREX;C000080287:AKRIX;C000159797:AKRSX              
1  jensen      JENIX   887215  S000004905  C000013260             I Shares  company_tickers_mf.json  C000013259:JENSX;C000013260:JENIX;C000013261:JENRX;C000175790:JENYX              
2   polen      POLIX  1388485  S000029264  C000089998  Institutional Class  company_tickers_mf.json                                    C000089997:POLRX;C000089998:POLIX
```

### 02c D: nav_monthly.csv per fund

```
entity   first    last  months                   by_source                 missing
  akre 2019-10 2026-09      81 nport_b5=70;yfinance_etf=11 2025-08;2025-09;2025-10
jensen 2019-10 2026-09      84                 yfinance=84                    none
 polen 2019-10 2026-09      84                 yfinance=84                    none
```

### nav_monthly.csv, Akre rows 2025-05 to 2026-01

```
   entity    month                     ret        source
67   akre  2025-05    0.031600000000000003      nport_b5
68   akre  2025-06    0.013600000000000001      nport_b5
69   akre  2025-07    0.027099999999999999      nport_b5
70   akre  2025-11  -0.0062911776006495668  yfinance_etf
71   akre  2025-12    0.011581222595117957  yfinance_etf
72   akre  2026-01   -0.081972257235084722  yfinance_etf
```

### 02b D item 2: B.5 against yfinance month returns, Jensen and Polen

```
entity ticker  n_months   first    last  max_abs_diff  mean_abs_diff  mean_diff         b5_gaps_in_span
jensen  JENIX        78 2019-09 2026-05      0.002898       0.000109   0.000016 2024-12;2025-01;2025-02
 polen  POLIX        84 2019-08 2026-07      0.003505       0.000209  -0.000020                    none

5 months with the largest absolute difference per fund:
entity   month      b5  yfinance      diff
jensen 2025-11  0.0115  0.008602  0.002898
jensen 2020-12  0.0396  0.040639 -0.001039
jensen 2021-12  0.0685  0.069424 -0.000924
jensen 2022-12 -0.0406 -0.041299  0.000699
jensen 2023-12  0.0222  0.021629  0.000571
 polen 2023-10 -0.0073 -0.003795 -0.003505
 polen 2024-01  0.0399  0.036445  0.003455
 polen 2023-12  0.0324  0.035801 -0.003401
 polen 2023-09 -0.0656 -0.068905  0.003305
 polen 2025-12 -0.0104 -0.009397 -0.001003
```

### 2.3b price panel, missing.csv and NAV series

```
panel shape (2723, 1301), first 2015-12-01, last 2026-09-30, columns sorted True

missing.csv:
   yf_ticker       sec_ids
0   9990302D     037411105
1       ALXN     015351109
2       AMED     023436108
3        ATH  BMG0684D1074
4       AZEK     05478C105
5        CDK     12508E101
6       CELG     151020104
7       CIVI     17888H103
8       CLGX     21871D103
9        CMA     200340107
10       CMD     138098108
11      CTRA     127097103
12      CVAC  NL0015436031
13      DBRG     25401T603
14       DNB     26484T106
15      DNKN     265504100
16      FLIR     302445101
17       HES     42809H107
18       HRC     431475102
19      IMMU     452907108
20      IPHI     45772F107
21      LVGO     539183103
22      MDLA     584021109
23      MXIM     57772K101
24       MYL  NL0011031208
25      PFPT     743424103
26      PRAH     69354M108
27        RP     75606N109
28       STL     85917A100
29      VIAB     92553P201
30       WBA     931427108
31      WORK     83088V102
32      XLRN     00434H108

nav_adjclose.csv:
            JENIX       POLIX         IVV         IWF        AKRE
first  2015-12-01  2015-12-01  2015-12-01  2015-12-01  2025-10-27
last   2026-09-30  2026-09-30  2026-09-30  2026-09-30  2026-09-30
n            2723        2723        2723        2723         233
```

### 2.3 last French month

```
ff5_monthly.csv last row '202608,    2.56,   -0.53,   -3.54,   -4.08,   -2.01,    0.29'
mom_monthly.csv last row '202608,  -5.70'
```

### 2.4 QUARTERS in full

```
 t holdings_date    q_start      q_end
 1    2019-09-30 2019-09-30 2019-12-31
 2    2019-12-31 2019-12-31 2020-03-31
 3    2020-03-31 2020-03-31 2020-06-30
 4    2020-06-30 2020-06-30 2020-09-30
 5    2020-09-30 2020-09-30 2020-12-31
 6    2020-12-31 2020-12-31 2021-03-31
 7    2021-03-31 2021-03-31 2021-06-30
 8    2021-06-30 2021-06-30 2021-09-30
 9    2021-09-30 2021-09-30 2021-12-31
10    2021-12-31 2021-12-31 2022-03-31
11    2022-03-31 2022-03-31 2022-06-30
12    2022-06-30 2022-06-30 2022-09-30
13    2022-09-30 2022-09-30 2022-12-30
14    2022-12-31 2022-12-30 2023-03-31
15    2023-03-31 2023-03-31 2023-06-30
16    2023-06-30 2023-06-30 2023-09-29
17    2023-09-30 2023-09-29 2023-12-29
18    2023-12-31 2023-12-29 2024-03-28
19    2024-03-31 2024-03-28 2024-06-28
20    2024-06-30 2024-06-28 2024-09-30
21    2024-09-30 2024-09-30 2024-12-31
22    2024-12-31 2024-12-31 2025-03-31
23    2025-03-31 2025-03-31 2025-06-30
24    2025-06-30 2025-06-30 2025-09-30
25    2025-09-30 2025-09-30 2025-12-31
26    2025-12-31 2025-12-31 2026-03-31
27    2026-03-31 2026-03-31 2026-06-30
28    2026-06-30 2026-06-30 2026-09-30
```

### 2.5 unmapped_weight per entity per period

```
entity          akre   jensen    polen      ivv      iwf
period_date                                             
2019-09-30  0.031626 0.058564 0.002725 0.069375 0.042467
2019-12-31  0.040312 0.059740 0.002930 0.064875 0.040271
2020-03-31  0.043155 0.043299 0.003417 0.054003 0.034800
2020-06-30  0.043307 0.000702 0.003147 0.046934 0.035365
2020-09-30  0.048245 0.000627 0.004282 0.043978 0.032236
2020-12-31  0.054871 0.000557 0.004679 0.047199 0.033911
2021-03-31  0.058245 0.000666 0.003885 0.048998 0.033252
2021-06-30  0.059374 0.069895 0.004088 0.047815 0.027849
2021-09-30  0.059950 0.000881 0.004946 0.042814 0.026407
2021-12-31  0.065264 0.000889 0.004377 0.040729 0.024598
2022-03-31  0.070049 0.000995 0.004609 0.040169 0.020689
2022-06-30  0.053842 0.001099 0.004563 0.040913 0.025819
2022-09-30  0.048268 0.001040 0.004399 0.041170 0.025132
2022-12-31  0.000000 0.001059 0.005018 0.041754 0.020763
2023-03-31  0.000000 0.001034 0.004937 0.035687 0.018299
2023-06-30  0.000000 0.001008 0.004813 0.033144 0.015678
2023-09-30  0.000000 0.000926 0.004972 0.034542 0.016039
2023-12-31  0.000000 0.000935 0.007993 0.029310 0.012042
2024-03-31  0.000059 0.000979 0.004677 0.029663 0.010368
2024-06-30  0.000774 0.000474 0.004610 0.028204 0.009887
2024-09-30  0.000680 0.000095 0.004903 0.025547 0.009678
2024-12-31  0.000594 0.000415 0.003943 0.016210 0.001485
2025-03-31  0.000714 0.000455 0.003751 0.017681 0.001336
2025-06-30  0.001129 0.000551 0.003836 0.014189 0.001056
2025-09-30  0.001765 0.000576 0.003020 0.012654 0.000928
2025-12-31  0.001904 0.000762 0.002488 0.012028 0.001057
2026-03-31  0.003010 0.000570 0.003539 0.016106 0.000852
2026-06-30  0.004202 0.000507 0.006081 0.010765 0.000231
```

### 2.5 unpriced_weight per entity per period

```
entity          akre   jensen    polen      ivv      iwf
period_date                                             
2019-09-30  0.000000 0.000000 0.000042 0.008820 0.010057
2019-12-31  0.000000 0.000000 0.000000 0.005467 0.004684
2020-03-31  0.000000 0.000079 0.000000 0.004694 0.004311
2020-06-30  0.000000 0.000142 0.000000 0.004545 0.004969
2020-09-30  0.000000 0.000170 0.000000 0.003892 0.005440
2020-12-31  0.000000 0.000249 0.000000 0.003973 0.004344
2021-03-31  0.000000 0.000358 0.000000 0.004227 0.004606
2021-06-30  0.000000 0.000420 0.000000 0.004070 0.004450
2021-09-30  0.000000 0.000000 0.000000 0.002036 0.001146
2021-12-31  0.000000 0.000000 0.000000 0.002587 0.000599
2022-03-31  0.000000 0.000000 0.000000 0.002977 0.000663
2022-06-30  0.000000 0.000000 0.000000 0.003095 0.001847
2022-09-30  0.005108 0.000000 0.000000 0.003080 0.001639
2022-12-31  0.004941 0.000000 0.000000 0.003160 0.002026
2023-03-31  0.005423 0.000000 0.000000 0.002519 0.001654
2023-06-30  0.006156 0.000000 0.000000 0.002226 0.000974
2023-09-30  0.007179 0.000000 0.000000 0.002342 0.001134
2023-12-31  0.006497 0.000000 0.000000 0.002126 0.000943
2024-03-31  0.006550 0.000000 0.000000 0.001946 0.000898
2024-06-30  0.004391 0.000000 0.000000 0.001511 0.000805
2024-09-30  0.001546 0.000000 0.000000 0.001266 0.001112
2024-12-31  0.000746 0.000000 0.000000 0.001250 0.001021
2025-03-31  0.000140 0.000000 0.000000 0.001544 0.001343
2025-06-30  0.000000 0.000000 0.000000 0.001257 0.000166
2025-09-30  0.000000 0.000000 0.000000 0.000316 0.000000
2025-12-31  0.000000 0.000000 0.000000 0.000344 0.000000
2026-03-31  0.000000 0.000000 0.000000 0.000477 0.000000
2026-06-30  0.000000 0.000000 0.000000 0.000000 0.000000
```

### 2.5 other_nosic_weight per entity per period

```
entity          akre   jensen    polen      ivv      iwf
period_date                                             
2019-09-30  0.000000 0.000000 0.000377 0.009478 0.010274
2019-12-31  0.000000 0.000000 0.000351 0.006215 0.004923
2020-03-31  0.000000 0.000079 0.002715 0.005341 0.004498
2020-06-30  0.000000 0.000142 0.000401 0.005254 0.004969
2020-09-30  0.000000 0.000170 0.000143 0.004566 0.005440
2020-12-31  0.000000 0.000249 0.000462 0.004775 0.004344
2021-03-31  0.000000 0.000358 0.000976 0.005102 0.004606
2021-06-30  0.000000 0.000420 0.001073 0.004969 0.004450
2021-09-30  0.000000 0.000000 0.000507 0.002971 0.001146
2021-12-31  0.000000 0.000000 0.002137 0.003504 0.000599
2022-03-31  0.000000 0.000000 0.007015 0.003734 0.000663
2022-06-30  0.000000 0.000000 0.007565 0.003911 0.001847
2022-09-30  0.000000 0.000000 0.004681 0.003876 0.001639
2022-12-31  0.000000 0.000019 0.018368 0.003854 0.002026
2023-03-31  0.000000 0.000000 0.001422 0.002595 0.001654
2023-06-30  0.000000 0.000000 0.001141 0.002226 0.000974
2023-09-30  0.000000 0.000000 0.002340 0.002342 0.001134
2023-12-31  0.000000 0.000000 0.006980 0.002126 0.000943
2024-03-31  0.000000 0.000000 0.001327 0.001946 0.000898
2024-06-30  0.000000 0.000000 0.003733 0.001511 0.000805
2024-09-30  0.000000 0.000000 0.002508 0.001266 0.001112
2024-12-31  0.000000 0.000000 0.007889 0.001250 0.001021
2025-03-31  0.000000 0.000000 0.006404 0.001544 0.001343
2025-06-30  0.000000 0.000000 0.003706 0.001257 0.000166
2025-09-30  0.000000 0.000000 0.005803 0.000316 0.000000
2025-12-31  0.000000 0.002205 0.021439 0.000344 0.000000
2026-03-31  0.000000 0.002755 0.016701 0.000477 0.000000
2026-06-30  0.000000 0.003582 0.009513 0.000000 0.000000
```

### 2.5 the largest of each across all 140 books

```
            column entity period_date    value
   unmapped_weight   akre  2022-03-31 0.070049
   unpriced_weight    iwf  2019-09-30 0.010057
other_nosic_weight  polen  2025-12-31 0.021439
```

### 02b D item 4: unmapped_weight per entity, mean and max over 28 books, before (pass 1 only) and after the fallbacks

```
        mean_before  max_before  mean_after  max_after
entity                                                
akre        2.6429%     7.0049%     2.4691%    7.0049%
jensen      5.4901%    11.6654%     0.8904%    6.9895%
polen       5.8902%     8.5174%     0.4308%    0.7993%
ivv         4.1792%     8.7346%     3.5231%    6.9375%
iwf         3.0968%     6.2638%     1.8661%    4.2467%
```

### 02b C 2.5: every book whose remaining unmapped_weight exceeds 2% (52 of 140)

```
entity period_date  unmapped_weight
  akre  2019-09-30         0.031626
  akre  2019-12-31         0.040312
  akre  2020-03-31         0.043155
  akre  2020-06-30         0.043307
  akre  2020-09-30         0.048245
  akre  2020-12-31         0.054871
  akre  2021-03-31         0.058245
  akre  2021-06-30         0.059374
  akre  2021-09-30         0.059950
  akre  2021-12-31         0.065264
  akre  2022-03-31         0.070049
  akre  2022-06-30         0.053842
  akre  2022-09-30         0.048268
   ivv  2019-09-30         0.069375
   ivv  2019-12-31         0.064875
   ivv  2020-03-31         0.054003
   ivv  2020-06-30         0.046934
   ivv  2020-09-30         0.043978
   ivv  2020-12-31         0.047199
   ivv  2021-03-31         0.048998
   ivv  2021-06-30         0.047815
   ivv  2021-09-30         0.042814
   ivv  2021-12-31         0.040729
   ivv  2022-03-31         0.040169
   ivv  2022-06-30         0.040913
   ivv  2022-09-30         0.041170
   ivv  2022-12-31         0.041754
   ivv  2023-03-31         0.035687
   ivv  2023-06-30         0.033144
   ivv  2023-09-30         0.034542
   ivv  2023-12-31         0.029310
   ivv  2024-03-31         0.029663
   ivv  2024-06-30         0.028204
   ivv  2024-09-30         0.025547
   iwf  2019-09-30         0.042467
   iwf  2019-12-31         0.040271
   iwf  2020-03-31         0.034800
   iwf  2020-06-30         0.035365
   iwf  2020-09-30         0.032236
   iwf  2020-12-31         0.033911
   iwf  2021-03-31         0.033252
   iwf  2021-06-30         0.027849
   iwf  2021-09-30         0.026407
   iwf  2021-12-31         0.024598
   iwf  2022-03-31         0.020689
   iwf  2022-06-30         0.025819
   iwf  2022-09-30         0.025132
   iwf  2022-12-31         0.020763
jensen  2019-09-30         0.058564
jensen  2019-12-31         0.059740
jensen  2020-03-31         0.043299
jensen  2021-06-30         0.069895
```

### OPEN-32 (a): rows counted in both unpriced_weight and other_nosic_weight

```
entity period_date       sec_id   ticker                           name map_status       weight
   ivv  2019-09-30    015351109     ALXN    Alexion Pharmaceuticals Inc     no_cik 8.888445e-04
   ivv  2019-09-30    037411105 9990302D                    Apache Corp     no_cik 3.879532e-04
   ivv  2019-09-30    127097103     CTRA           Cabot Oil & Gas Corp     no_cik 2.942672e-04
   ivv  2019-09-30    151020104     CELG                   Celgene Corp     no_cik 2.848486e-03
   ivv  2019-09-30    200340107      CMA                   Comerica Inc     no_cik 3.987367e-04
   ivv  2019-09-30    302445101     FLIR               FLIR Systems Inc     no_cik 2.816504e-04
   ivv  2019-09-30    42809H107      HES                      Hess Corp     no_cik 6.334683e-04
   ivv  2019-09-30    57772K101     MXIM  Maxim Integrated Products Inc     no_cik 6.354483e-04
   ivv  2019-09-30    92553P201     VIAB                     Viacom Inc     no_cik 3.490349e-04
   ivv  2019-09-30    931427108      WBA   Walgreens Boots Alliance Inc     no_cik 1.696175e-03
   ivv  2019-09-30 NL0011031208      MYL                       Mylan NV     no_cik 4.056990e-04
   ivv  2019-12-31    015351109     ALXN    Alexion Pharmaceuticals Inc     no_cik 8.942938e-04
   ivv  2019-12-31    037411105 9990302D                    Apache Corp     no_cik 3.692135e-04
   ivv  2019-12-31    127097103     CTRA           Cabot Oil & Gas Corp     no_cik 2.589713e-04
   ivv  2019-12-31    200340107      CMA                   Comerica Inc     no_cik 3.864467e-04
   ivv  2019-12-31    302445101     FLIR               FLIR Systems Inc     no_cik 2.569748e-04
   ivv  2019-12-31    42809H107      HES                      Hess Corp     no_cik 6.460894e-04
   ivv  2019-12-31    57772K101     MXIM  Maxim Integrated Products Inc     no_cik 6.130948e-04
   ivv  2019-12-31    931427108      WBA   Walgreens Boots Alliance Inc     no_cik 1.649286e-03
   ivv  2019-12-31 NL0011031208      MYL                       Mylan NV     no_cik 3.924889e-04
   ivv  2020-03-31    015351109     ALXN    Alexion Pharmaceuticals Inc     no_cik 9.310362e-04
   ivv  2020-03-31    037411105 9990302D                    Apache Corp     no_cik 7.366258e-05
   ivv  2020-03-31    127097103     CTRA           Cabot Oil & Gas Corp     no_cik 3.206454e-04
   ivv  2020-03-31    200340107      CMA                   Comerica Inc     no_cik 1.981656e-04
   ivv  2020-03-31    302445101     FLIR               FLIR Systems Inc     no_cik 1.973654e-04
   ivv  2020-03-31    42809H107      HES                      Hess Corp     no_cik 4.038229e-04
   ivv  2020-03-31    57772K101     MXIM  Maxim Integrated Products Inc     no_cik 6.075863e-04
   ivv  2020-03-31    931427108      WBA   Walgreens Boots Alliance Inc     no_cik 1.604839e-03
   ivv  2020-03-31 NL0011031208      MYL                       Mylan NV     no_cik 3.568758e-04
   ivv  2020-06-30    015351109     ALXN    Alexion Pharmaceuticals Inc     no_cik 9.673432e-04
   ivv  2020-06-30    037411105 9990302D                    Apache Corp     no_cik 1.973542e-04
   ivv  2020-06-30    127097103     CTRA           Cabot Oil & Gas Corp     no_cik 2.651401e-04
   ivv  2020-06-30    200340107      CMA                   Comerica Inc     no_cik 2.043136e-04
   ivv  2020-06-30    302445101     FLIR               FLIR Systems Inc     no_cik 1.989019e-04
   ivv  2020-06-30    42809H107      HES                      Hess Corp     no_cik 5.325379e-04
   ivv  2020-06-30    57772K101     MXIM  Maxim Integrated Products Inc     no_cik 6.301796e-04
   ivv  2020-06-30    931427108      WBA   Walgreens Boots Alliance Inc     no_cik 1.219093e-03
   ivv  2020-06-30 NL0011031208      MYL                       Mylan NV     no_cik 3.300123e-04
   ivv  2020-09-30    015351109     ALXN    Alexion Pharmaceuticals Inc     no_cik 8.996671e-04
   ivv  2020-09-30    037411105 9990302D                    Apache Corp     no_cik 1.277057e-04
   ivv  2020-09-30    127097103     CTRA           Cabot Oil & Gas Corp     no_cik 2.474877e-04
   ivv  2020-09-30    200340107      CMA                   Comerica Inc     no_cik 1.985694e-04
   ivv  2020-09-30    302445101     FLIR               FLIR Systems Inc     no_cik 1.721662e-04
   ivv  2020-09-30    42809H107      HES                      Hess Corp     no_cik 4.000333e-04
   ivv  2020-09-30    57772K101     MXIM  Maxim Integrated Products Inc     no_cik 6.476934e-04
   ivv  2020-09-30    931427108      WBA   Walgreens Boots Alliance Inc     no_cik 9.276025e-04
   ivv  2020-09-30 NL0011031208      MYL                       Mylan NV     no_cik 2.713681e-04
   ivv  2020-12-31    015351109     ALXN    Alexion Pharmaceuticals Inc     no_cik 1.083285e-03
   ivv  2020-12-31    037411105 9990302D                    Apache Corp     no_cik 1.626923e-04
   ivv  2020-12-31    127097103     CTRA           Cabot Oil & Gas Corp     no_cik 1.986299e-04
   ivv  2020-12-31    200340107      CMA                   Comerica Inc     no_cik 2.394429e-04
   ivv  2020-12-31    302445101     FLIR               FLIR Systems Inc     no_cik 1.783685e-04
   ivv  2020-12-31    42809H107      HES                      Hess Corp     no_cik 4.533121e-04
   ivv  2020-12-31    57772K101     MXIM  Maxim Integrated Products Inc     no_cik 7.485114e-04
   ivv  2020-12-31    931427108      WBA   Walgreens Boots Alliance Inc     no_cik 9.085962e-04
   ivv  2021-03-31    015351109     ALXN    Alexion Pharmaceuticals Inc     no_cik 9.999460e-04
   ivv  2021-03-31    127097103     CTRA           Cabot Oil & Gas Corp     no_cik 2.265323e-04
   ivv  2021-03-31    200340107      CMA                   Comerica Inc     no_cik 3.007446e-04
   ivv  2021-03-31    302445101     FLIR               FLIR Systems Inc     no_cik 2.272322e-04
   ivv  2021-03-31    42809H107      HES                      Hess Corp     no_cik 5.733757e-04
   ivv  2021-03-31    57772K101     MXIM  Maxim Integrated Products Inc     no_cik 7.283701e-04
   ivv  2021-03-31    931427108      WBA   Walgreens Boots Alliance Inc     no_cik 1.170877e-03
   ivv  2021-06-30    015351109     ALXN    Alexion Pharmaceuticals Inc     no_cik 1.120872e-03
   ivv  2021-06-30    127097103     CTRA           Cabot Oil & Gas Corp     no_cik 1.843851e-04
   ivv  2021-06-30    200340107      CMA                   Comerica Inc     no_cik 2.671192e-04
   ivv  2021-06-30    42809H107      HES                      Hess Corp     no_cik 6.639555e-04
   ivv  2021-06-30    57772K101     MXIM  Maxim Integrated Products Inc     no_cik 7.866944e-04
   ivv  2021-06-30    931427108      WBA   Walgreens Boots Alliance Inc     no_cik 1.047193e-03
   ivv  2021-09-30    127097103     CTRA           Cabot Oil & Gas Corp     no_cik 2.407189e-04
   ivv  2021-09-30    200340107      CMA                   Comerica Inc     no_cik 2.893576e-04
   ivv  2021-09-30    42809H107      HES                      Hess Corp     no_cik 5.815369e-04
   ivv  2021-09-30    931427108      WBA   Walgreens Boots Alliance Inc     no_cik 9.248738e-04
   ivv  2021-12-31    127097103     CTRA             Coterra Energy Inc     no_cik 3.909549e-04
   ivv  2021-12-31    200340107      CMA                   Comerica Inc     no_cik 2.823170e-04
   ivv  2021-12-31    42809H107      HES                      Hess Corp     no_cik 4.968871e-04
   ivv  2021-12-31    82669G104     SBNY     Signature Bank/New York NY     no_cik 4.802785e-04
   ivv  2021-12-31    931427108      WBA   Walgreens Boots Alliance Inc     no_cik 9.368766e-04
   ivv  2022-03-31    127097103     CTRA             Coterra Energy Inc     no_cik 5.730849e-04
   ivv  2022-03-31    200340107      CMA                   Comerica Inc     no_cik 3.083210e-04
   ivv  2022-03-31    42809H107      HES                      Hess Corp     no_cik 7.798350e-04
   ivv  2022-03-31    82669G104     SBNY     Signature Bank/New York NY     no_cik 4.793209e-04
   ivv  2022-03-31    931427108      WBA   Walgreens Boots Alliance Inc     no_cik 8.366196e-04
   ivv  2022-06-30    127097103     CTRA             Coterra Energy Inc     no_cik 6.470823e-04
   ivv  2022-06-30    200340107      CMA                   Comerica Inc     no_cik 3.089582e-04
   ivv  2022-06-30    42809H107      HES                      Hess Corp     no_cik 9.217305e-04
   ivv  2022-06-30    82669G104     SBNY     Signature Bank/New York NY     no_cik 3.604367e-04
   ivv  2022-06-30    931427108      WBA   Walgreens Boots Alliance Inc     no_cik 8.564227e-04
   ivv  2022-09-30    127097103     CTRA           Coterra Energy, Inc.     no_cik 6.899360e-04
   ivv  2022-09-30    200340107      CMA                 Comerica, Inc.     no_cik 3.065097e-04
   ivv  2022-09-30    42809H107      HES                     Hess Corp.     no_cik 1.013130e-03
   ivv  2022-09-30    82669G104     SBNY                 Signature Bank     no_cik 3.208774e-04
   ivv  2022-09-30    931427108      WBA Walgreens Boots Alliance, Inc.     no_cik 7.496787e-04
   ivv  2022-12-31    127097103     CTRA           Coterra Energy, Inc.     no_cik 6.028909e-04
   ivv  2022-12-31    200340107      CMA                 Comerica, Inc.     no_cik 2.724228e-04
   ivv  2022-12-31    42809H107      HES                     Hess Corp.     no_cik 1.224241e-03
   ivv  2022-12-31    82669G104     SBNY                 Signature Bank     no_cik 2.256042e-04
   ivv  2022-12-31    931427108      WBA Walgreens Boots Alliance, Inc.     no_cik 8.345336e-04
   ivv  2023-03-31    127097103     CTRA           Coterra Energy, Inc.     no_cik 5.634133e-04
   ivv  2023-03-31    200340107      CMA                 Comerica, Inc.     no_cik 1.655859e-04
   ivv  2023-03-31    42809H107      HES                     Hess Corp.     no_cik 1.069268e-03
   ivv  2023-03-31    931427108      WBA Walgreens Boots Alliance, Inc.     no_cik 7.208292e-04
   ivv  2023-06-30    127097103     CTRA           Coterra Energy, Inc.     no_cik 5.156719e-04
   ivv  2023-06-30    200340107      CMA                 Comerica, Inc.     no_cik 1.500867e-04
   ivv  2023-06-30    42809H107      HES                     Hess Corp.     no_cik 1.010950e-03
   ivv  2023-06-30    931427108      WBA Walgreens Boots Alliance, Inc.     no_cik 5.490039e-04
   ivv  2023-09-30    127097103     CTRA           Coterra Energy, Inc.     no_cik 5.701314e-04
   ivv  2023-09-30    200340107      CMA                 Comerica, Inc.     no_cik 1.523381e-04
   ivv  2023-09-30    42809H107      HES                     Hess Corp.     no_cik 1.176588e-03
   ivv  2023-09-30    931427108      WBA Walgreens Boots Alliance, Inc.     no_cik 4.434172e-04
   ivv  2023-12-31    127097103     CTRA           Coterra Energy, Inc.     no_cik 4.794431e-04
   ivv  2023-12-31    200340107      CMA                 Comerica, Inc.     no_cik 1.837951e-04
   ivv  2023-12-31    42809H107      HES                     Hess Corp.     no_cik 9.953034e-04
   ivv  2023-12-31    931427108      WBA Walgreens Boots Alliance, Inc.     no_cik 4.676059e-04
   ivv  2024-03-31    127097103     CTRA           Coterra Energy, Inc.     no_cik 4.757899e-04
   ivv  2024-03-31    200340107      CMA                 Comerica, Inc.     no_cik 1.647328e-04
   ivv  2024-03-31    42809H107      HES                     Hess Corp.     no_cik 9.532672e-04
   ivv  2024-03-31    931427108      WBA Walgreens Boots Alliance, Inc.     no_cik 3.522241e-04
   ivv  2024-06-30    127097103     CTRA           Coterra Energy, Inc.     no_cik 4.329743e-04
   ivv  2024-06-30    42809H107      HES                     Hess Corp.     no_cik 8.893744e-04
   ivv  2024-06-30    931427108      WBA Walgreens Boots Alliance, Inc.     no_cik 1.887787e-04
   ivv  2024-09-30    127097103     CTRA           Coterra Energy, Inc.     no_cik 3.635621e-04
   ivv  2024-09-30    42809H107      HES                     Hess Corp.     no_cik 7.706093e-04
   ivv  2024-09-30    931427108      WBA Walgreens Boots Alliance, Inc.     no_cik 1.318144e-04
   ivv  2024-12-31    127097103     CTRA           Coterra Energy, Inc.     no_cik 3.777363e-04
   ivv  2024-12-31    42809H107      HES                     Hess Corp.     no_cik 7.381215e-04
   ivv  2024-12-31    931427108      WBA Walgreens Boots Alliance, Inc.     no_cik 1.345196e-04
   ivv  2025-03-31    127097103     CTRA           Coterra Energy, Inc.     no_cik 4.474358e-04
   ivv  2025-03-31    42809H107      HES                     Hess Corp.     no_cik 9.284087e-04
   ivv  2025-03-31    931427108      WBA Walgreens Boots Alliance, Inc.     no_cik 1.683449e-04
   ivv  2025-06-30    127097103     CTRA           Coterra Energy, Inc.     no_cik 3.689447e-04
   ivv  2025-06-30    42809H107      HES                     Hess Corp.     no_cik 7.316641e-04
   ivv  2025-06-30    931427108      WBA Walgreens Boots Alliance, Inc.     no_cik 1.563449e-04
   ivv  2025-09-30    127097103     CTRA           Coterra Energy, Inc.     no_cik 3.163905e-04
   ivv  2025-12-31    127097103     CTRA           Coterra Energy, Inc.     no_cik 3.436701e-04
   ivv  2026-03-31    127097103     CTRA           Coterra Energy, Inc.     no_cik 4.768906e-04
   iwf  2019-09-30    015351109     ALXN    Alexion Pharmaceuticals Inc     no_cik 1.156192e-03
   iwf  2019-09-30    12508E101      CDK                 CDK Global Inc     no_cik 4.265074e-04
   iwf  2019-09-30    127097103     CTRA           Cabot Oil & Gas Corp     no_cik 3.266268e-04
   iwf  2019-09-30    138098108      CMD            Cantel Medical Corp     no_cik 1.201650e-04
   iwf  2019-09-30    151020104     CELG                   Celgene Corp     no_cik 5.011131e-03
   iwf  2019-09-30    200340107      CMA                   Comerica Inc     no_cik 5.084928e-05
   iwf  2019-09-30    21871D103     CLGX    CoreLogic Inc/United States     no_cik 1.475612e-05
   iwf  2019-09-30    265504100     DNKN       Dunkin' Brands Group Inc     no_cik 4.446150e-04
   iwf  2019-09-30    302445101     FLIR               FLIR Systems Inc     no_cik 4.766619e-05
   iwf  2019-09-30    431475102      HRC          Hill-Rom Holdings Inc     no_cik 2.687253e-04
   iwf  2019-09-30    57772K101     MXIM  Maxim Integrated Products Inc     no_cik 4.303776e-04
   iwf  2019-09-30    584021109     MDLA                   Medallia Inc     no_cik 2.494324e-05
   iwf  2019-09-30    69354M108     PRAH        PRA Health Sciences Inc     no_cik 4.499718e-04
   iwf  2019-09-30    743424103     PFPT                 Proofpoint Inc     no_cik 5.065261e-04
   iwf  2019-09-30    75606N109       RP                   RealPage Inc     no_cik 3.567200e-04
   iwf  2019-09-30    82669G104     SBNY     Signature Bank/New York NY     no_cik 2.355691e-04
   iwf  2019-09-30 BMG0684D1074      ATH             Athene Holding Ltd     no_cik 1.852069e-04
   iwf  2019-12-31    015351109     ALXN    Alexion Pharmaceuticals Inc     no_cik 1.138560e-03
   iwf  2019-12-31    12508E101      CDK                 CDK Global Inc     no_cik 4.395961e-04
   iwf  2019-12-31    127097103     CTRA           Cabot Oil & Gas Corp     no_cik 2.819795e-04
   iwf  2019-12-31    138098108      CMD            Cantel Medical Corp     no_cik 1.041102e-04
   iwf  2019-12-31    200340107      CMA                   Comerica Inc     no_cik 3.014123e-05
   iwf  2019-12-31    21871D103     CLGX    CoreLogic Inc/United States     no_cik 2.121791e-05
   iwf  2019-12-31    265504100     DNKN       Dunkin' Brands Group Inc     no_cik 3.738246e-04
   iwf  2019-12-31    302445101     FLIR               FLIR Systems Inc     no_cik 2.849781e-05
   iwf  2019-12-31    431475102      HRC          Hill-Rom Holdings Inc     no_cik 2.628341e-04
   iwf  2019-12-31    57772K101     MXIM  Maxim Integrated Products Inc     no_cik 4.149256e-04
   iwf  2019-12-31    584021109     MDLA                   Medallia Inc     no_cik 3.515525e-05
   iwf  2019-12-31    69354M108     PRAH        PRA Health Sciences Inc     no_cik 4.567998e-04
   iwf  2019-12-31    743424103     PFPT                 Proofpoint Inc     no_cik 4.171709e-04
   iwf  2019-12-31    75606N109       RP                   RealPage Inc     no_cik 2.871228e-04
   iwf  2019-12-31    82669G104     SBNY     Signature Bank/New York NY     no_cik 2.241663e-04
   iwf  2019-12-31 BMG0684D1074      ATH             Athene Holding Ltd     no_cik 1.677779e-04
   iwf  2020-03-31    015351109     ALXN    Alexion Pharmaceuticals Inc     no_cik 1.116184e-03
   iwf  2020-03-31    12508E101      CDK                 CDK Global Inc     no_cik 2.989761e-04
   iwf  2020-03-31    127097103     CTRA           Cabot Oil & Gas Corp     no_cik 3.339468e-04
   iwf  2020-03-31    138098108      CMD            Cantel Medical Corp     no_cik 4.858555e-05
   iwf  2020-03-31    200340107      CMA                   Comerica Inc     no_cik 2.418438e-05
   iwf  2020-03-31    21871D103     CLGX    CoreLogic Inc/United States     no_cik 6.057913e-08
   iwf  2020-03-31    265504100     DNKN       Dunkin' Brands Group Inc     no_cik 3.181529e-04
   iwf  2020-03-31    302445101     FLIR               FLIR Systems Inc     no_cik 2.906960e-05
   iwf  2020-03-31    431475102      HRC          Hill-Rom Holdings Inc     no_cik 2.624987e-04
   iwf  2020-03-31    57772K101     MXIM  Maxim Integrated Products Inc     no_cik 3.733742e-04
   iwf  2020-03-31    584021109     MDLA                   Medallia Inc     no_cik 8.491642e-05
   iwf  2020-03-31    69354M108     PRAH        PRA Health Sciences Inc     no_cik 3.986159e-04
   iwf  2020-03-31    743424103     PFPT                 Proofpoint Inc     no_cik 4.362501e-04
   iwf  2020-03-31    75606N109       RP                   RealPage Inc     no_cik 3.191229e-04
   iwf  2020-03-31    82669G104     SBNY     Signature Bank/New York NY     no_cik 1.633665e-04
   iwf  2020-03-31 BMG0684D1074      ATH             Athene Holding Ltd     no_cik 1.034958e-04
   iwf  2020-06-30    00434H108     XLRN           Acceleron Pharma Inc     no_cik 2.807288e-04
   iwf  2020-06-30    015351109     ALXN    Alexion Pharmaceuticals Inc     no_cik 2.511288e-04
   iwf  2020-06-30    023436108     AMED                   Amedisys Inc     no_cik 4.282073e-04
   iwf  2020-06-30    12508E101      CDK                 CDK Global Inc     no_cik 4.373126e-05
   iwf  2020-06-30    21871D103     CLGX    CoreLogic Inc/United States     no_cik 1.799550e-05
   iwf  2020-06-30    265504100     DNKN       Dunkin' Brands Group Inc     no_cik 3.062040e-04
   iwf  2020-06-30    431475102      HRC          Hill-Rom Holdings Inc     no_cik 5.844339e-05
   iwf  2020-06-30    452907108     IMMU               Immunomedics Inc     no_cik 4.982759e-04
   iwf  2020-06-30    45772F107     IPHI                     Inphi Corp     no_cik 3.834630e-04
   iwf  2020-06-30    539183103     LVGO             Livongo Health Inc     no_cik 2.765707e-04
   iwf  2020-06-30    57772K101     MXIM  Maxim Integrated Products Inc     no_cik 3.647415e-04
   iwf  2020-06-30    584021109     MDLA                   Medallia Inc     no_cik 1.410927e-04
   iwf  2020-06-30    69354M108     PRAH        PRA Health Sciences Inc     no_cik 3.658959e-04
   iwf  2020-06-30    743424103     PFPT                 Proofpoint Inc     no_cik 4.295244e-04
   iwf  2020-06-30    75606N109       RP                   RealPage Inc     no_cik 3.271156e-04
   iwf  2020-06-30    83088V102     WORK         Slack Technologies Inc     no_cik 7.959467e-04
   iwf  2020-09-30    00434H108     XLRN           Acceleron Pharma Inc     no_cik 3.312199e-04
   iwf  2020-09-30    015351109     ALXN    Alexion Pharmaceuticals Inc     no_cik 2.172253e-04
   iwf  2020-09-30    023436108     AMED                   Amedisys Inc     no_cik 4.512380e-04
   iwf  2020-09-30    05478C105     AZEK                AZEK Co Inc/The     no_cik 1.353027e-05
   iwf  2020-09-30    12508E101      CDK                 CDK Global Inc     no_cik 3.098808e-05
   iwf  2020-09-30    21871D103     CLGX    CoreLogic Inc/United States     no_cik 1.591109e-05
   iwf  2020-09-30    26484T106      DNB  Dun & Bradstreet Holdings Inc     no_cik 6.531117e-05
   iwf  2020-09-30    265504100     DNKN       Dunkin' Brands Group Inc     no_cik 3.509814e-04
   iwf  2020-09-30    431475102      HRC          Hill-Rom Holdings Inc     no_cik 2.961255e-05
   iwf  2020-09-30    452907108     IMMU               Immunomedics Inc     no_cik 1.058628e-03
   iwf  2020-09-30    45772F107     IPHI                     Inphi Corp     no_cik 3.245593e-04
   iwf  2020-09-30    539183103     LVGO             Livongo Health Inc     no_cik 4.681596e-04
   iwf  2020-09-30    57772K101     MXIM  Maxim Integrated Products Inc     no_cik 3.602193e-04
   iwf  2020-09-30    584021109     MDLA                   Medallia Inc     no_cik 1.455582e-04
   iwf  2020-09-30    69354M108     PRAH        PRA Health Sciences Inc     no_cik 3.282158e-04
   iwf  2020-09-30    743424103     PFPT                 Proofpoint Inc     no_cik 3.613388e-04
   iwf  2020-09-30    75606N109       RP                   RealPage Inc     no_cik 2.677017e-04
   iwf  2020-09-30    83088V102     WORK         Slack Technologies Inc     no_cik 6.196156e-04
   iwf  2020-12-31    00434H108     XLRN           Acceleron Pharma Inc     no_cik 3.290089e-04
   iwf  2020-12-31    015351109     ALXN    Alexion Pharmaceuticals Inc     no_cik 2.787318e-04
   iwf  2020-12-31    023436108     AMED                   Amedisys Inc     no_cik 5.141839e-04
   iwf  2020-12-31    05478C105     AZEK                AZEK Co Inc/The     no_cik 2.697328e-05
   iwf  2020-12-31    12508E101      CDK                 CDK Global Inc     no_cik 4.390066e-05
   iwf  2020-12-31    21871D103     CLGX    CoreLogic Inc/United States     no_cik 2.591972e-05
   iwf  2020-12-31    26484T106      DNB  Dun & Bradstreet Holdings Inc     no_cik 6.606131e-05
   iwf  2020-12-31    431475102      HRC          Hill-Rom Holdings Inc     no_cik 5.157910e-05
   iwf  2020-12-31    45772F107     IPHI                     Inphi Corp     no_cik 4.071896e-04
   iwf  2020-12-31    57772K101     MXIM  Maxim Integrated Products Inc     no_cik 4.248478e-04
   iwf  2020-12-31    584021109     MDLA                   Medallia Inc     no_cik 1.491736e-04
   iwf  2020-12-31    69354M108     PRAH        PRA Health Sciences Inc     no_cik 3.754513e-04
   iwf  2020-12-31    743424103     PFPT                 Proofpoint Inc     no_cik 4.200649e-04
   iwf  2020-12-31    75606N109       RP                   RealPage Inc     no_cik 3.644726e-04
   iwf  2020-12-31    83088V102     WORK         Slack Technologies Inc     no_cik 8.667729e-04
   iwf  2021-03-31    00434H108     XLRN           Acceleron Pharma Inc     no_cik 3.560712e-04
   iwf  2021-03-31    015351109     ALXN    Alexion Pharmaceuticals Inc     no_cik 2.708694e-04
   iwf  2021-03-31    023436108     AMED                   Amedisys Inc     no_cik 4.509118e-04
   iwf  2021-03-31    05478C105     AZEK                AZEK Co Inc/The     no_cik 2.704569e-05
   iwf  2021-03-31    12508E101      CDK                 CDK Global Inc     no_cik 4.547152e-05
   iwf  2021-03-31    21871D103     CLGX    CoreLogic Inc/United States     no_cik 1.589212e-05
   iwf  2021-03-31    26484T106      DNB  Dun & Bradstreet Holdings Inc     no_cik 8.764704e-05
   iwf  2021-03-31    431475102      HRC          Hill-Rom Holdings Inc     no_cik 4.646756e-05
   iwf  2021-03-31    45772F107     IPHI                     Inphi Corp     no_cik 4.600322e-04
   iwf  2021-03-31    57772K101     MXIM  Maxim Integrated Products Inc     no_cik 4.345549e-04
   iwf  2021-03-31    584021109     MDLA                   Medallia Inc     no_cik 1.341170e-04
   iwf  2021-03-31    69354M108     PRAH        PRA Health Sciences Inc     no_cik 4.443921e-04
   iwf  2021-03-31    743424103     PFPT                 Proofpoint Inc     no_cik 3.844920e-04
   iwf  2021-03-31    75606N109       RP                   RealPage Inc     no_cik 3.616450e-04
   iwf  2021-03-31    83088V102     WORK         Slack Technologies Inc     no_cik 1.085993e-03
   iwf  2021-06-30    00434H108     XLRN           Acceleron Pharma Inc     no_cik 3.118815e-04
   iwf  2021-06-30    023436108     AMED                   Amedisys Inc     no_cik 3.270618e-04
   iwf  2021-06-30    05478C105     AZEK                AZEK Co Inc/The     no_cik 1.199095e-04
   iwf  2021-06-30    12508E101      CDK                 CDK Global Inc     no_cik 5.075977e-05
   iwf  2021-06-30    127097103     CTRA           Cabot Oil & Gas Corp     no_cik 3.843059e-05
   iwf  2021-06-30    42809H107      HES                      Hess Corp     no_cik 7.760531e-05
   iwf  2021-06-30    57772K101     MXIM  Maxim Integrated Products Inc     no_cik 1.268856e-03
   iwf  2021-06-30    584021109     MDLA                   Medallia Inc     no_cik 9.005836e-05
   iwf  2021-06-30    69354M108     PRAH        PRA Health Sciences Inc     no_cik 4.550916e-04
   iwf  2021-06-30    743424103     PFPT                 Proofpoint Inc     no_cik 4.642920e-04
   iwf  2021-06-30    83088V102     WORK         Slack Technologies Inc     no_cik 1.044634e-03
   iwf  2021-06-30    85917A100      STL            Sterling Bancorp/DE     no_cik 1.762612e-05
   iwf  2021-06-30 NL0015436031     CVAC                     CureVac NV     no_cik 1.838952e-04
   iwf  2021-09-30    00434H108     XLRN           Acceleron Pharma Inc     no_cik 4.249492e-04
   iwf  2021-09-30    023436108     AMED                   Amedisys Inc     no_cik 2.064697e-04
   iwf  2021-09-30    05478C105     AZEK                AZEK Co Inc/The     no_cik 1.123420e-04
   iwf  2021-09-30    12508E101      CDK                 CDK Global Inc     no_cik 3.250383e-05
   iwf  2021-09-30    127097103     CTRA           Cabot Oil & Gas Corp     no_cik 4.744995e-05
   iwf  2021-09-30    42809H107      HES                      Hess Corp     no_cik 6.876025e-05
   iwf  2021-09-30    584021109     MDLA                   Medallia Inc     no_cik 1.000614e-04
   iwf  2021-09-30    85917A100      STL            Sterling Bancorp/DE     no_cik 1.759457e-05
   iwf  2021-09-30 NL0015436031     CVAC                     CureVac NV     no_cik 1.354146e-04
   iwf  2021-12-31    023436108     AMED                   Amedisys Inc     no_cik 1.910211e-04
   iwf  2021-12-31    05478C105     AZEK                AZEK Co Inc/The     no_cik 1.170172e-04
   iwf  2021-12-31    12508E101      CDK                 CDK Global Inc     no_cik 3.885885e-05
   iwf  2021-12-31    127097103     CTRA             Coterra Energy Inc     no_cik 1.014468e-04
   iwf  2021-12-31    42809H107      HES                      Hess Corp     no_cik 5.848987e-05
   iwf  2021-12-31    85917A100      STL            Sterling Bancorp/DE     no_cik 1.631269e-05
   iwf  2021-12-31 NL0015436031     CVAC                     CureVac NV     no_cik 7.634164e-05
   iwf  2022-03-31    023436108     AMED                   Amedisys Inc     no_cik 2.342851e-04
   iwf  2022-03-31    05478C105     AZEK                AZEK Co Inc/The     no_cik 7.786866e-05
   iwf  2022-03-31    12508E101      CDK                 CDK Global Inc     no_cik 4.029255e-05
   iwf  2022-03-31    127097103     CTRA             Coterra Energy Inc     no_cik 1.694578e-04
   iwf  2022-03-31    42809H107      HES                      Hess Corp     no_cik 9.313870e-05
   iwf  2022-03-31 NL0015436031     CVAC                     CureVac NV     no_cik 4.805197e-05
   iwf  2022-06-30    12508E101      CDK                 CDK Global Inc     no_cik 2.975961e-04
   iwf  2022-06-30    127097103     CTRA             Coterra Energy Inc     no_cik 1.936765e-04
   iwf  2022-06-30    42809H107      HES                      Hess Corp     no_cik 1.324263e-03
   iwf  2022-06-30    82669G104     SBNY     Signature Bank/New York NY     no_cik 3.182267e-05
   iwf  2022-09-30    127097103     CTRA            Coterra Energy Inc.     no_cik 1.951255e-04
   iwf  2022-09-30    42809H107      HES               HESS CORPORATION     no_cik 1.416398e-03
   iwf  2022-09-30    82669G104     SBNY                 SIGNATURE BANK     no_cik 2.789838e-05
   iwf  2022-12-31    127097103     CTRA            Coterra Energy Inc.     no_cik 1.801171e-04
   iwf  2022-12-31    42809H107      HES               HESS CORPORATION     no_cik 1.825408e-03
   iwf  2022-12-31    82669G104     SBNY                 SIGNATURE BANK     no_cik 2.093219e-05
   iwf  2023-03-31    127097103     CTRA            Coterra Energy Inc.     no_cik 1.577530e-04
   iwf  2023-03-31    42809H107      HES               HESS CORPORATION     no_cik 1.496396e-03
   iwf  2023-06-30    42809H107      HES               HESS CORPORATION     no_cik 9.741261e-04
   iwf  2023-09-30    42809H107      HES               HESS CORPORATION     no_cik 1.134078e-03
   iwf  2023-12-31    42809H107      HES               HESS CORPORATION     no_cik 9.425466e-04
   iwf  2024-03-31    42809H107      HES               HESS CORPORATION     no_cik 8.979275e-04
   iwf  2024-06-30    42809H107      HES               HESS CORPORATION     no_cik 8.051521e-04
   iwf  2024-09-30    05478C105     AZEK          THE AZEK COMPANY INC.     no_cik 1.702558e-04
   iwf  2024-09-30    17888H103     CIVI        CIVITAS RESOURCES, INC.     no_cik 5.025805e-05
   iwf  2024-09-30    42809H107      HES               HESS CORPORATION     no_cik 8.916965e-04
   iwf  2024-12-31    05478C105     AZEK          THE AZEK COMPANY INC.     no_cik 1.615158e-04
   iwf  2024-12-31    17888H103     CIVI        CIVITAS RESOURCES, INC.     no_cik 4.255572e-05
   iwf  2024-12-31    42809H107      HES               HESS CORPORATION     no_cik 8.168541e-04
   iwf  2025-03-31    05478C105     AZEK          THE AZEK COMPANY INC.     no_cik 1.881371e-04
   iwf  2025-03-31    17888H103     CIVI        CIVITAS RESOURCES, INC.     no_cik 3.602091e-05
   iwf  2025-03-31    42809H107      HES               HESS CORPORATION     no_cik 1.119026e-03
   iwf  2025-06-30    05478C105     AZEK          THE AZEK COMPANY INC.     no_cik 1.663792e-04
jensen  2020-03-31    431475102      HRC         Hill-Rom Holdings Inc.     no_cik 7.874190e-05
jensen  2020-06-30    431475102      HRC         Hill-Rom Holdings Inc.     no_cik 1.415822e-04
jensen  2020-09-30    431475102      HRC         Hill-Rom Holdings Inc.     no_cik 1.699024e-04
jensen  2020-12-31    431475102      HRC         Hill-Rom Holdings Inc.     no_cik 2.492212e-04
jensen  2021-03-31    431475102      HRC         Hill-Rom Holdings Inc.     no_cik 3.582517e-04
jensen  2021-06-30    431475102      HRC         Hill-Rom Holdings Inc.     no_cik 4.200825e-04
 polen  2019-09-30    138098108      CMD            CANTEL MEDICAL CORP     no_cik 4.173041e-05
```

### 2.5 outputs/tables/unmapped_top.csv (all 60, 60 rows)

```
          sec_id id_type                                         name              max_weight entity_of_max                                                                                                                                                                                                                                                                                                              periods
0      38259P508   cusip                    Alphabet Inc Cap Stk Cl A    0.069193604892453145        jensen                                                                                                                                                                                                                                                                                                           2021-06-30
1      913017109   cusip                     United Technologies Corp     0.05879446238479915        jensen                                                                                                                                                                                                                                                                                     2019-09-30;2019-12-31;2020-03-31
2      112585104   cusip                    BROOKFIELD ASSET MGMT INC     0.05140617414847453          akre                                                                                                                                                                       2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30
3      03662Q105   cusip                                    ANSYS INC    0.014990865878743822          akre                                              2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30
4      30231G102   cusip                            Exxon Mobil Corp.    0.014136562085076007           ivv  2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31;2026-06-30
5      25401T108   cusip                      DIGITALBRIDGE GROUP INC   0.0064097319194375939          akre                                                                                                                                                                                                                                                               2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30
6   IE00BZ12WP82    isin                                    Linde plc   0.0050183679514159826           ivv                                                                                                                                                            2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31
7      512807108   cusip                     LAM RESEARCH CORPORATION   0.0046730321919345669           iwf                                                                               2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30
8      19626G108   cusip                           COLONY CAP INC NEW   0.0046349892355709733          akre                                                                                                                                                                                                                                         2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31
9      H82027105   cusip                           SOPHIA GENETICS SA   0.0042020722489042699          akre                                                                                                                                                                                                        2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31;2026-06-30
10     74165N105   cusip                               PRIMO WTR CORP   0.0037007831867074247          akre                                                                                                                                                                                                                                                                                                2019-09-30;2019-12-31
11     369604103   cusip                          General Electric Co   0.0036422585348026182           ivv                                                                                                                                                                                                                              2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30
12     040413106   cusip                        ARISTA NETWORKS, INC.   0.0035872482310876563           iwf                                                                               2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30
13     09247X101   cusip                                BlackRock Inc   0.0034116204579662276           ivv                                                                               2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30
14  IE00BY9D5467    isin                                 Allergan PLC   0.0027137046650727898           ivv                                                                                                                                                                                                                                                                                     2019-09-30;2019-12-31;2020-03-31
15     N07059210   cusip                                 ASML HLDG NV   0.0026433944619528712         polen                                                                               2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31;2026-06-30
16  GB00BZ09BD16    isin                           Atlassian Corp PLC   0.0025023809271421029           iwf                                                                                                                                                                                  2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30
17     755111507   cusip                                  Raytheon Co   0.0024940986451726758           iwf                                                                                                                                                                                                                                                                                     2019-09-30;2019-12-31;2020-03-31
18     G5960L103   cusip                                MEDTRONIC PLC   0.0023774982197734547         polen             2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31
19     00507V109   cusip                      Activision Blizzard Inc   0.0022824099847269549           ivv                                                                                                                           2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30
20     90184L102   cusip                                  Twitter Inc   0.0022354721179680139           iwf                                                                                                                                                                       2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30
21     983919101   cusip                                   Xilinx Inc   0.0021865392745658726           iwf                                                                                                                                                                                                        2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31
22     848637104   cusip                                   Splunk Inc   0.0021575729902274235           iwf                                                                                                                2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31
23     26614N102   cusip                        DuPont de Nemours Inc   0.0021516225056716757           ivv             2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31
24     285512109   cusip                          Electronic Arts Inc   0.0019811053373857751           iwf  2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31;2026-06-30
25     G5494J103   cusip                 LINDE PUBLIC LIMITED COMPANY   0.0019773995325109146           iwf                                                                                                                                                            2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31
26     G4388N106   cusip                            HELEN OF TROY LTD   0.0019538919005247569         polen                                                                                                                           2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31
27     Y4600W108   cusip                                 KAROOOOO LTD   0.0019538919005247569         polen                                                                                                                2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31
28     339041105   cusip                    FleetCor Technologies Inc   0.0017489969392823458           iwf                                                                                                                2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31
29     723787107   cusip            PIONEER NATURAL RESOURCES COMPANY   0.0017437215595318715           iwf                                                                                                     2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31
30     928563402   cusip                                 VMWARE, INC.   0.0017104344832561313           iwf                                                                                                                           2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30
31     G06242104   cusip                    ATLASSIAN CORPORATION PLC   0.0017018437578084418           iwf                                                                                                                                                                                                                                                                                                           2022-09-30
32     44919P508   cusip                              Match Group Inc   0.0016560488750206393           iwf                                                                                                                                                                                                                                                                          2019-09-30;2019-12-31;2020-03-31;2020-06-30
33     054937107   cusip                                    BB&T Corp   0.0016549973924982475           ivv                                                                                                                                                                                                                                                                                                           2019-09-30
34     156782104   cusip                                  Cerner Corp   0.0015447921569672095           iwf                                                                                                                                                                                             2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31
35     812578102   cusip                         Seattle Genetics Inc     0.00145059621221608           iwf                                                                                                                                                                                                                                                               2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30
36     81181C104   cusip                                  SEAGEN INC.   0.0014198585738567793           iwf                                                                                                                                                                                  2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30
37     74167P108   cusip                               PRIMO WTR CORP   0.0013914422464520798          akre                                                                                                                                                                                                                                                                          2020-03-31;2020-06-30;2020-09-30;2020-12-31
38     G46188101   cusip  HORIZON THERAPEUTICS PUBLIC LIMITED COMPANY   0.0013754631593144628           iwf                                                                                                                                                                                                                                                               2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30
39  BMG475671050    isin                               IHS Markit Ltd   0.0013148758770604322           ivv                                                                                                                                                                                                        2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31
40  CH0102993182    isin                          TE Connectivity Ltd   0.0013038361552020741           ivv                                                                                          2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30
41     682680103   cusip                                  ONEOK, Inc.   0.0012944637950438869           ivv  2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31;2026-06-30
42     22266L106   cusip                           Coupa Software Inc   0.0012677090440158928           iwf                                                                                                                                                            2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31
43     867914103   cusip                           SunTrust Banks Inc   0.0012420351652246086           ivv                                                                                                                                                                                                                                                                                                           2019-09-30
44     904767704   cusip                                 UNILEVER PLC   0.0012336342102053195         polen                                                                    2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31
45     053484101   cusip                    AvalonBay Communities Inc   0.0012165837000948439           ivv  2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31;2026-06-30
46  JE00B783TY65    isin                                    Aptiv PLC   0.0011719446732489217           ivv                                                                               2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30
47     86800U104   cusip                   Super Micro Computer, Inc.   0.0011537600810265411           ivv                                                                                                                                                                                                                                                                                     2024-03-31;2024-06-30;2024-09-30
48     177376100   cusip                           Citrix Systems Inc   0.0011325468665715507           iwf                                                                                                                                                                       2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30
49     254709108   cusip                  Discover Financial Services   0.0010493905201596208           ivv                                                         2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31
50     M22465104   cusip                 CHECK POINT SOFTWARE TECH LT     0.00104513053095289         polen                                                                                                                                                                                                                                         2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31
51     78486Q101   cusip                          SVB Financial Group   0.0010425421873051755           ivv                                                                                                                                                            2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31
52     94946T106   cusip                    WellCare Health Plans Inc  0.00098361538930914348           iwf                                                                                                                                                                                                                                                                                                2019-09-30;2019-12-31
53     G29018101   cusip                                   DLOCAL LTD   0.0009701981747949021         polen                                                                                                                                                 2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31;2026-06-30
54  IE00BQPVQZ61    isin                     Horizon Therapeutics Plc  0.00094655988798231997           iwf                                                                                                                                                                                  2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30
55     M7S64H106   cusip                               MONDAY COM LTD  0.00094166196127842426         polen                                                                                                                                                                                                                                                               2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31
56     30063P105   cusip                          Exact Sciences Corp  0.00093458293020870172           iwf                        2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31
57     98936J101   cusip                                  Zendesk Inc  0.00090320389623948594           iwf                                                                                                                                                                       2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30
58     44891N109   cusip                          IAC/InterActiveCorp  0.00087413096564512808           iwf                                                                                                                                                                                                                                                                                     2020-09-30;2020-12-31;2021-03-31
59     124857202   cusip                                     CBS Corp  0.00086512604766223844           iwf                                                                                                                                                                                                                                                                                                           2019-09-30
```

### 2.5 outputs/tables/unpriced_top.csv (all, 20 rows)

```
          sec_id yf_ticker                           name              max_weight entity_of_max                                                                                                                                                                                                                                                                                                   periods
0      25401T603      DBRG        DIGITALBRIDGE GROUP INC   0.0071786368817792993          akre                                                                                                                                                                                  2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31
1      151020104      CELG                   Celgene Corp   0.0050111311371948261           iwf                                                                                                                                                                                                                                                                                                2019-09-30
2      42809H107       HES               HESS CORPORATION    0.001825407708934378           iwf                                   2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30
3      931427108       WBA   Walgreens Boots Alliance Inc   0.0016961745832553099           ivv                                   2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30
4      57772K101      MXIM  Maxim Integrated Products Inc    0.001268856328926718           iwf                                                                                                                                                                                                                   2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30
5      015351109      ALXN    Alexion Pharmaceuticals Inc   0.0011561920224645689           iwf                                                                                                                                                                                                                   2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30
6      83088V102      WORK         Slack Technologies Inc   0.0010859932540489539           iwf                                                                                                                                                                                                                                                    2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30
7      452907108      IMMU               Immunomedics Inc   0.0010586276812981708           iwf                                                                                                                                                                                                                                                                                     2020-06-30;2020-09-30
8      127097103      CTRA           Coterra Energy, Inc.   0.0006899359770872203           ivv  2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31
9      023436108      AMED                   Amedisys Inc  0.00051418393892262301           iwf                                                                                                                                                                                                                   2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31
10     743424103      PFPT                 Proofpoint Inc  0.00050652611622481252           iwf                                                                                                                                                                                                                   2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30
11     82669G104      SBNY     Signature Bank/New York NY  0.00048027853844539276           ivv                                                                                                                                                                                                                   2019-09-30;2019-12-31;2020-03-31;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31
12     539183103      LVGO             Livongo Health Inc  0.00046815956921926434           iwf                                                                                                                                                                                                                                                                                     2020-06-30;2020-09-30
13     45772F107      IPHI                     Inphi Corp   0.0004600321955553089           iwf                                                                                                                                                                                                                                                               2020-06-30;2020-09-30;2020-12-31;2021-03-31
14     69354M108      PRAH        PRA Health Sciences Inc  0.00045679984306724793           iwf                                                                                                                                                                                                                   2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30
15     265504100      DNKN       Dunkin' Brands Group Inc   0.0004446149749949921           iwf                                                                                                                                                                                                                                                    2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30
16     12508E101       CDK                 CDK Global Inc  0.00043959608852186155           iwf                                                                                                                                                                       2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30
17     00434H108      XLRN           Acceleron Pharma Inc  0.00042494920987947956           iwf                                                                                                                                                                                                                                         2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30
18     431475102       HRC         Hill-Rom Holdings Inc.  0.00042008246583797801        jensen                                                                                                                                                                                                                   2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30
19  NL0011031208       MYL                       Mylan NV  0.00040569902450858931           ivv                                                                                                                                                                                                                                                    2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30
```

### 2.5 outputs/tables/nocik_top.csv (all, 40 rows)

```
          sec_id    ticker                           name              max_weight entity_of_max                                                                                                                                                                                                                                                                                                              periods
0      464287614       IWF                     ISHARES TR    0.015883659898640261         polen  2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31;2026-06-30
1      151020104      CELG                   Celgene Corp   0.0050111311371948261           iwf                                                                                                                                                                                                                                                                                                           2019-09-30
2      464288257      ACWI                     ISHARES TR   0.0036867412205562485         polen                                                                    2020-12-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31;2026-06-30
3      89834G562      JGRW      Jensen Quality Growth ETF   0.0035821358841665926        jensen                                                                                                                                                                                                                                                                                     2025-12-31;2026-03-31;2026-06-30
4      42809H107       HES               HESS CORPORATION    0.001825407708934378           iwf                                              2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30
5      931427108       WBA   Walgreens Boots Alliance Inc   0.0016961745832553099           ivv                                              2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30
6      46436E718      SGOV                     ISHARES TR   0.0016364686906730438         polen                                                                                                                                                                                                        2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31
7      78468R663       BIL                    SPDR SER TR   0.0013368918808974979         polen                                                                                                                                                                                                                                                    2023-12-31;2024-03-31;2024-06-30;2024-09-30;2025-03-31;2026-03-31
8      57772K101      MXIM  Maxim Integrated Products Inc    0.001268856328926718           iwf                                                                                                                                                                                                                              2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30
9      015351109      ALXN    Alexion Pharmaceuticals Inc   0.0011561920224645689           iwf                                                                                                                                                                                                                              2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30
10     83088V102      WORK         Slack Technologies Inc   0.0010859932540489539           iwf                                                                                                                                                                                                                                                               2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30
11     452907108      IMMU               Immunomedics Inc   0.0010586276812981708           iwf                                                                                                                                                                                                                                                                                                2020-06-30;2020-09-30
12     33616C100      FRCB         First Republic Bank/CA  0.00093432590389135376           ivv                                                                                                                                                 2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31
13     922908736       VUG             VANGUARD INDEX FDS  0.00069012380312469365         polen                                                                                                                                                                                             2023-06-30;2023-09-30;2023-12-31;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31;2026-06-30
14     127097103      CTRA           Coterra Energy, Inc.   0.0006899359770872203           ivv             2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31
15     464288240      ACWX                     ISHARES TR  0.00056688498129407261         polen                                   2019-12-31;2020-03-31;2020-06-30;2020-12-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31;2026-06-30
16     464288513       HYG                     ISHARES TR  0.00052716669800614467         polen                                                                                                                                                                                                                                                                                                           2025-09-30
17     023436108      AMED                   Amedisys Inc  0.00051418393892262301           iwf                                                                                                                                                                                                                              2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31
18     743424103      PFPT                 Proofpoint Inc  0.00050652611622481252           iwf                                                                                                                                                                                                                              2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30
19     82669G104      SBNY     Signature Bank/New York NY  0.00048027853844539276           ivv                                                                                                                                                                                                                              2019-09-30;2019-12-31;2020-03-31;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31
20     539183103      LVGO             Livongo Health Inc  0.00046815956921926434           iwf                                                                                                                                                                                                                                                                                                2020-06-30;2020-09-30
21     45772F107      IPHI                     Inphi Corp   0.0004600321955553089           iwf                                                                                                                                                                                                                                                                          2020-06-30;2020-09-30;2020-12-31;2021-03-31
22     69354M108      PRAH        PRA Health Sciences Inc  0.00045679984306724793           iwf                                                                                                                                                                                                                              2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30
23     265504100      DNKN       Dunkin' Brands Group Inc   0.0004446149749949921           iwf                                                                                                                                                                                                                                                               2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30
24     12508E101       CDK                 CDK Global Inc  0.00043959608852186155           iwf                                                                                                                                                                                  2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30
25     00434H108      XLRN           Acceleron Pharma Inc  0.00042494920987947956           iwf                                                                                                                                                                                                                                                    2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30
26     431475102       HRC         Hill-Rom Holdings Inc.  0.00042008246583797801        jensen                                                                                                                                                                                                                              2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30
27  NL0011031208       MYL                       Mylan NV  0.00040569902450858931           ivv                                                                                                                                                                                                                                                               2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30
28     464287200       IVV                     ISHARES TR  0.00039983547715280535         polen                                                                                                                                                                                                                                                                                     2024-09-30;2025-06-30;2025-12-31
29     200340107       CMA                   Comerica Inc  0.00039873670849460826           ivv                                                                                                     2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31
30     037411105  9990302D                    Apache Corp   0.0003879531884768909           ivv                                                                                                                                                                                                                                                    2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31
31     46429B671      MCHI                     ISHARES TR  0.00037623770531585674         polen                                                                                                                                                                                                                                                                                                           2026-03-31
32     75606N109        RP                   RealPage Inc  0.00036447255947318259           iwf                                                                                                                                                                                                                                         2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31
33     46434G772       EWT                    ISHARES INC  0.00035760814365859249         polen                                                                                                                                                                                                                                                                                                           2026-03-31
34     92553P201      VIAB                     Viacom Inc  0.00034903492585019454           ivv                                                                                                                                                                                                                                                                                                           2019-09-30
35     464287671      IUSG                     ISHARES TR  0.00032361338006341628         polen                                                                                                                                                                                                                                                                                                           2022-12-31
36     37954Y889      CATH                   GLOBAL X FDS  0.00032241996518511543         polen                                                                                          2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31;2026-06-30
37     302445101      FLIR               FLIR Systems Inc   0.0002816503516558018           ivv                                                                                                                                                                                                                                         2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31
38     46137V357       RSP   INVESCO EXCHANGE TRADED FD T    0.000275745647669204         polen                                                                                                                                                                                                                                                                                                           2025-09-30
39     922042742        VT   VANGUARD INTL EQUITY INDEX F  0.00020236081709101524         polen                                                                                                                                                                                                                              2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31;2026-06-30
```

### 2.5 outputs/tables/large_moves.csv (all, 702 rows)

```
     entity   t        sec_id yf_ticker        date          daily_return                  weight
0      akre   2     512816109      LAMR  2020-03-24   0.26291399985665254  0.00039723763953178408
1      akre   5     88339J105       TTD  2020-11-06    0.2657808413219207  1.6283814910123563e-05
2      akre  20     38267D109      GSHD  2024-07-25   0.29208528987345028   0.0018502611165914238
3      akre  26     12510Q100       CCC  2026-02-25   0.25296447120219234    0.021648896779320654
4      akre  28     303250104      FICO  2026-09-29  -0.26521901276766979    0.084651154606920562
5       ivv   1     09062X103      BIIB  2019-10-22   0.26110689474589321    0.001736388060087425
6       ivv   1     30212P303      EXPE  2019-11-07  -0.27386224375552959  0.00076436428299806749
7       ivv   2     25179M103       DVN  2020-03-09  -0.37397157580320994  0.00037549831029386687
8       ivv   2     25278X109      FANG  2020-03-09  -0.44645804720787963  0.00055789606113216964
9       ivv   2     26875P101       EOG  2020-03-09  -0.32007222215546116   0.0018209788059128573
10      ivv   2     406216101       HAL  2020-03-09  -0.37643457004500513  0.00080909723496695057
11      ivv   2     423452101        HP  2020-03-09  -0.32934804070389323  0.00017532023506533468
12      ivv   2     674599105       OXY  2020-03-09  -0.52013817818503938   0.0013774718085722878
13      ivv   2  AN8068571086       SLB  2020-03-09  -0.27421379481323205   0.0020796947534001001
14      ivv   2  BMG667211046      NCLH  2020-03-09  -0.26900372003360029  0.00046378038305224629
15      ivv   2  GB00BDSFG982       FTI  2020-03-09  -0.26269836472384833  0.00032736460198861354
16      ivv   2  LR0008862868       RCL  2020-03-09  -0.25749893551513026   0.0008571080041542145
17      ivv   2  BMG667211046      NCLH  2020-03-11   -0.2668292813184785  0.00046378038305224629
18      ivv   2     534187109       LNC  2020-03-12  -0.26670864731003108  0.00043181441927294702
19      ivv   2     56585A102       MPC  2020-03-12   -0.2700893532575086   0.0014618631226773692
20      ivv   2     92276F100       VTR  2020-03-12  -0.27897776607026037  0.00080765515733953171
21      ivv   2  BMG667211046      NCLH  2020-03-12  -0.35795077911005246  0.00046378038305224629
22      ivv   2  LR0008862868       RCL  2020-03-12  -0.31778221019493302   0.0008571080041542145
23      ivv   2     018581108       BFH  2020-03-16  -0.27065267082337374  0.00016371496702967885
24      ivv   2     23355L106       DXC  2020-03-16  -0.28335533695604631  0.00035607499961303493
25      ivv   2     552953101       MGM  2020-03-16  -0.33613982805897069  0.00063790804044805275
26      ivv   2     828806109       SPG  2020-03-16  -0.26712699494960646   0.0017146360037876246
27      ivv   2     87165B103       SYF  2020-03-16  -0.26025694717692993   0.0007999078840737261
28      ivv   2     876030107       TPR  2020-03-16  -0.29266780085997157  0.00027354826257020552
29      ivv   2     92276F100       VTR  2020-03-16  -0.28592871618855131  0.00080765515733953171
30      ivv   2  NL0009434992       LYB  2020-03-16  -0.25491034735023732   0.0009024538585146797
31      ivv   2  VGG1890L1076      CPRI  2020-03-16  -0.30653268946283696  0.00020654896552771074
32      ivv   2     018581108       BFH  2020-03-18  -0.26757364198992317  0.00016371496702967885
33      ivv   2     02376R102       AAL  2020-03-18  -0.25224649065601168  0.00040970074097865776
34      ivv   2     222070203      COTY  2020-03-18  -0.31376144212360357  0.00011496548849696978
35      ivv   2     247361702       DAL  2020-03-18  -0.25992437374693977   0.0012492201383027712
36      ivv   2     552953101       MGM  2020-03-18  -0.25235596164728247  0.00063790804044805275
37      ivv   2     61945C103       MOS  2020-03-18  -0.27507728588039493  0.00027513509157681577
38      ivv   2     910047109       UAL  2020-03-18  -0.30290188759105852  0.00071436114671078528
39      ivv   2     23355L106       DXC  2020-03-19   0.33941999276724988  0.00035607499961303493
40      ivv   2     416515104       HIG  2020-03-19   0.27695244123756257  0.00081589708933976638
41      ivv   2     913903100       UHS  2020-03-19    0.2533613316568093  0.00042748706534125752
42      ivv   2  VGG1890L1076      CPRI  2020-03-19   0.33244687276304252  0.00020654896552771074
43      ivv   2     018581108       BFH  2020-03-24   0.35428786814331836  0.00016371496702967885
44      ivv   2     02376R102       AAL  2020-03-24   0.35804878793111672  0.00040970074097865776
45      ivv   2     20825C104       COP  2020-03-24   0.25213878520672628   0.0026663587640866674
46      ivv   2     23355L106       DXC  2020-03-24   0.41015988802805015  0.00035607499961303493
47      ivv   2     237194105       DRI  2020-03-24   0.31342907631929529  0.00050482690320026999
48      ivv   2     35671D857       FCX  2020-03-24   0.29684565047088718   0.0007113502343229569
49      ivv   2     364760108       GAP  2020-03-24   0.29458597057075142  0.00013169276861318047
50      ivv   2     406216101       HAL  2020-03-24   0.26526719948749444  0.00080909723496695057
51      ivv   2     412822108       HOG  2020-03-24   0.26988285861409356  0.00021356165498559603
52      ivv   2     423452101        HP  2020-03-24   0.28025504777139032  0.00017532023506533468
53      ivv   2     500255104       KSS  2020-03-24   0.27043561087878309  0.00029434251622281738
54      ivv   2     534187109       LNC  2020-03-24   0.31700257558750944  0.00043181441927294702
55      ivv   2     552953101       MGM  2020-03-24   0.33114760768570295  0.00063790804044805275
56      ivv   2     854502101       SWK  2020-03-24   0.25322798242109679  0.00094688159552611855
57      ivv   2     876030107       TPR  2020-03-24   0.29678649825989445  0.00027354826257020552
58      ivv   2     910047109       UAL  2020-03-24   0.25714285714285712  0.00071436114671078528
59      ivv   2     91529Y106       UNM  2020-03-24   0.26204239436478827  0.00021598956595415435
60      ivv   2     962166104        WY  2020-03-24   0.25315473164801316  0.00084506519543972017
61      ivv   2     963320106       WHR  2020-03-24   0.29570230928280994  0.00035703453281412382
62      ivv   2  BMG667211046      NCLH  2020-03-24   0.42192346344527909  0.00046378038305224629
63      ivv   2     001055102       AFL  2020-03-25   0.26176565418716269   0.0014509567020640178
64      ivv   3     693656100       PVH  2020-04-06   0.28138085937706259  0.00013310636583966276
65      ivv   3  VGG1890L1076      CPRI  2020-04-06      0.25908559288749  7.3254009623459338e-05
66      ivv   3  BMG667211046      NCLH  2020-04-29   0.25362869794679521  0.00010912617392092046
67      ivv   3     02376R102       AAL  2020-06-04   0.41097036076894633  0.00021837143200345598
68      ivv   3     674599105       OXY  2020-06-05   0.33697722887140857    0.000485388751139838
69      ivv   4     79466L302       CRM  2020-08-26   0.26044878376843572   0.0065840065260170354
70      ivv   5     016255101      ALGN  2020-10-22   0.34966205378458493   0.0008421898223433678
71      ivv   5     09062X103      BIIB  2020-11-04   0.43973933359595518   0.0016148589975060893
72      ivv   5     09062X103      BIIB  2020-11-09  -0.28166616329827387   0.0016148589975060893
73      ivv   5     25278X109      FANG  2020-11-09   0.30962013334430827  0.00017723136054999342
74      ivv   5     44107P104       HST  2020-11-09   0.30028584987786311  0.00027484116150736668
75      ivv   5     49446R109       KIM  2020-11-09    0.3226115141634327  0.00016729132056979979
76      ivv   5     534187109       LNC  2020-11-09   0.25124747655503854  0.00020102278722205062
77      ivv   5     55261F104       MTB  2020-11-09   0.25095888485442552  0.00041756968598364777
78      ivv   5     758849103       REG  2020-11-09   0.34977930532382229  0.00021306937615459332
79      ivv   5     78440X101       SLG  2020-11-09   0.36923809711632094  0.00011633904907226319
80      ivv   5     828806109       SPG  2020-11-09   0.27869356592221917  0.00070674550858661992
81      ivv   5     91913Y100       VLO  2020-11-09   0.31202523813422811  0.00064024997971116047
82      ivv   5     929042109       VNO  2020-11-09   0.27395427401415717  0.00018742149842251361
83      ivv   5     983134107      WYNN  2020-11-09   0.27688279280076333   0.0002473855126097786
84      ivv   5  BMG667211046      NCLH  2020-11-09   0.26753100172223365  0.00017793362201894817
85      ivv   5  LR0008862868       RCL  2020-11-09   0.28786065777707592  0.00041244095808281515
86      ivv   7     09062X103      BIIB  2021-06-07   0.38341366407586164   0.0012712363578734438
87      ivv  10     30303M102      META  2022-02-03  -0.26390083075996218    0.019720437415419619
88      ivv  10     29414B104      EPAM  2022-02-28  -0.45676331883276866  0.00094430151240500789
89      ivv  10     29414B104      EPAM  2022-03-16   0.25186637764649711  0.00094430151240500789
90      ivv  11     64110L106      NFLX  2022-04-20  -0.35116607551133094   0.0043434911283030076
91      ivv  11     904311206        UA  2022-05-06    -0.258841203179632   8.741226840012043e-05
92      ivv  12     09062X103      BIIB  2022-09-28    0.3985034366799578  0.00094465865968710694
93      ivv  13     368736104      GNRC  2022-10-19  -0.25341817415282686  0.00037772544088963901
94      ivv  13     23918K108       DVA  2022-10-28  -0.27090438330204292  0.00015848594771210873
95      ivv  13     31620M106       FIS  2022-11-03  -0.28048336314296785   0.0015284516003983011
96      ivv  13     534187109       LNC  2022-11-03  -0.33147802279964556  0.00022801698068698905
97      ivv  13     070830104      BBWI  2022-11-17   0.25184690487970429    0.000248276506929398
98      ivv  14     016255101      ALGN  2023-02-02   0.27377625893786561  0.00047679997517138524
99      ivv  14     33616C100      FRCB  2023-03-13   -0.6182730153006869  0.00069386372936824751
100     ivv  14     493267108       KEY  2023-03-13  -0.27330769493909934  0.00050576976533342379
101     ivv  14     989701107      ZION  2023-03-13  -0.25724916872415726  0.00022971256002998259
102     ivv  14     33616C100      FRCB  2023-03-14   0.26978539668819246  0.00069386372936824751
103     ivv  14     33616C100      FRCB  2023-03-17  -0.32798364811727942  0.00069386372936824751
104     ivv  14     33616C100      FRCB  2023-03-20  -0.47112462257812071  0.00069386372936824751
105     ivv  14     33616C100      FRCB  2023-03-21   0.29474548954340762  0.00069386372936824751
106     ivv  15     33616C100      FRCB  2023-04-25  -0.49374997615814209  7.5957106837835472e-05
107     ivv  15     29355A107      ENPH  2023-04-26  -0.25734362058821458  0.00083228166720466319
108     ivv  15     33616C100      FRCB  2023-04-26  -0.29753089021607904  7.5957106837835472e-05
109     ivv  15     33616C100      FRCB  2023-04-28  -0.43295638804252645  7.5957106837835472e-05
110     ivv  15     33616C100      FRCB  2023-05-03  -0.90495726058274528  7.5957106837835472e-05
111     ivv  15     336433107      FSLR  2023-05-12   0.26475243929052761  0.00062791779022678871
112     ivv  15     00751Y106       AAP  2023-05-31  -0.35035651440482307  0.00020983049643748234
113     ivv  15     33616C100      FRCB  2023-06-16   0.48437496847085071  7.5957106837835472e-05
114     ivv  15     33616C100      FRCB  2023-06-28   0.76336239814177209  7.5957106837835472e-05
115     ivv  16     23355L106       DXC  2023-08-03  -0.29442184718156295  0.00016337616245157033
116     ivv  16     34959E109      FTNT  2023-08-04  -0.25065999396778349   0.0013256172812665236
117     ivv  17     83417M104      SEDG  2023-10-20  -0.27267942547541646  0.00020370823265788168
118     ivv  17     70432V102      PAYC  2023-11-01   -0.3848634889963235  0.00035530611306924841
119     ivv  18     697435105      PANW  2024-02-21  -0.28441092670854551    0.002289276635774978
120     ivv  19     37959E102        GL  2024-04-11  -0.53140185481263513  0.00022593607646468863
121     ivv  19     29414B104      EPAM  2024-05-09  -0.26994384067521737  0.00036141033953401971
122     ivv  20     513272104        LW  2024-07-24   -0.2823709610068863  0.00026471128705537865
123     ivv  20     28176E108        EW  2024-07-25  -0.31339847201516924   0.0012142047156436747
124     ivv  20     252131107      DXCM  2024-07-26  -0.40658320903586309  0.00098357412488402941
125     ivv  20     458140100      INTC  2024-08-02  -0.26058514559856982   0.0028759035168442627
126     ivv  20     34959E109      FTNT  2024-08-07   0.25300122889160459  0.00083361473051523998
127     ivv  20     256677105        DG  2024-08-29  -0.32146316291090937  0.00063363109761901341
128     ivv  21     74736K101      QRVO  2024-10-30  -0.27308918714832786  0.00020120895601851728
129     ivv  21     446413106       HII  2024-10-31   -0.2616072363940084  0.00021282508772544167
130     ivv  21     150870103        CE  2024-11-05  -0.26315786861700208  0.00030513136885583237
131     ivv  21     05464C101      AXON  2024-11-08   0.28678398437499997  0.00058875769921083038
132     ivv  22     21037T109       CEG  2025-01-10   0.25159957676666411   0.0014048804392642201
133     ivv  22     92840M102       VST  2025-01-27  -0.28271675428516507  0.00094179691282314146
134     ivv  22     302491303       FMC  2025-02-05  -0.33530727479951572  0.00012216220490570898
135     ivv  22     955306105       WST  2025-02-13  -0.38218315769840527  0.00047628372600219877
136     ivv  23     595017104      MCHP  2025-04-09   0.27051483349876881  0.00054687032020972232
137     ivv  23     910047109       UAL  2025-04-09   0.26144256288951184  0.00047780272754551124
138     ivv  23     159864107       CRL  2025-04-10  -0.28129724826126401  0.00016195488628253568
139     ivv  23     629377508       NRG  2025-05-12   0.26213023415488568  0.00040671033609429558
140     ivv  24     15135B101       CNC  2025-07-02  -0.40370701024843814  0.00051449755141951697
141     ivv  24     016255101      ALGN  2025-07-31  -0.36626226916931681  0.00024567362100341608
142     ivv  24     45168D104      IDXX  2025-08-04   0.27493755333054404  0.00082127752527860179
143     ivv  24     366651107        IT  2025-08-05  -0.27554869511995173  0.00059236508947639209
144     ivv  24     68389X105      ORCL  2025-09-10   0.35948826632664566   0.0067732117760270173
145     ivv  24     871607107      SNPS  2025-09-10   -0.3583731788271417   0.0015097459774649695
146     ivv  24     934423104       WBD  2025-09-11   0.28947369421718205  0.00049144934108705826
147     ivv  25     337738108      FISV  2025-10-29  -0.44043750892676059   0.0012285273394534323
148     ivv  25     513272104        LW  2025-12-19  -0.25939664683436015  0.00014192217321626712
149     ivv  26     80004C200      SNDK  2026-01-06   0.27564952572933255  0.00056553828647852035
150     ivv  26     60855R100       MOH  2026-02-06  -0.25514587226622709  0.00015263859008588927
151     ivv  26     86800U302      SMCI  2026-03-20  -0.33322507060101236  0.00025107254630412989
152     ivv  27     16119P108      CHTR  2026-04-24  -0.25498384567682997   0.0003324758698538292
153     ivv  27  NL0009538784      NXPI  2026-04-29   0.25547974901846637  0.00088641578184195326
154     ivv  27     23804L103      DDOG  2026-05-07   0.31326968833359392  0.00069318499043296644
155     ivv  27     00971T101      AKAM  2026-05-08   0.26583257882813971  0.00029560988885983991
156     ivv  27     24703L202      DELL  2026-05-29   0.32758240852375464  0.00087252071053376215
157     ivv  27     86800U302      SMCI  2026-06-10  -0.27977359996665896  0.00020461471165399614
158     ivv  28     459200101       IBM  2026-07-14  -0.25207595513952263   0.0041003233422104556
159     ivv  28     80004C200      SNDK  2026-07-30    0.2599395037665051   0.0052235890221965561
160     ivv  28     69608A108      PLTR  2026-08-04   0.29454836201182122   0.0041560279877676928
161     ivv  28     989207105      ZBRA  2026-08-04   0.26467551792190824  0.00019466887478076052
162     ivv  28     60770K107      MRNA  2026-08-19    1.7696951623021624  0.00038364153756567789
163     ivv  28     303250104      FICO  2026-09-29  -0.26521901276766979  0.00042900252458323736
164     iwf   1     76680R206       RNG  2019-10-04   0.28038256114593207  0.00064933219602445391
165     iwf   1     09062X103      BIIB  2019-10-22   0.26110689474589321   0.0010549276518623885
166     iwf   1     252131107      DXCM  2019-11-07   0.27155174475568788  0.00097026636415811145
167     iwf   1     30212P303      EXPE  2019-11-07  -0.27386224375552959   0.0011547913724449133
168     iwf   1     90353W103        UI  2019-11-08    0.3596432345476952  0.00013578187036999639
169     iwf   1     803607100      SRPT  2019-12-13   0.31432269779396815  0.00038342458710480167
170     iwf   2     25754A201       DPZ  2020-02-20   0.25600786570803735  0.00079101645761297189
171     iwf   2     60770K107      MRNA  2020-02-25   0.27810651069705528  0.00024424657159144658
172     iwf   2     67059N108      NTNX  2020-02-27  -0.28593323707156115  0.00034182561144013835
173     iwf   2     25278X109      FANG  2020-03-09  -0.44645804720787963  0.00019302389912767288
174     iwf   2  BMG667211046      NCLH  2020-03-09  -0.26900372003360029  0.00016344888577265188
175     iwf   2  BMG667211046      NCLH  2020-03-11   -0.2668292813184785  0.00016344888577265188
176     iwf   2     94419L101         W  2020-03-12  -0.26682956608304309  0.00037555878075433094
177     iwf   2  BMG667211046      NCLH  2020-03-12  -0.35795077911005246  0.00016344888577265188
178     iwf   2     018581108       BFH  2020-03-16  -0.27065267082337374  2.1347142127077516e-05
179     iwf   2     122017106      BURL  2020-03-16  -0.29829607754064724  0.00096393445019392289
180     iwf   2     33829M101      FIVE  2020-03-16  -0.25326541285230142  0.00045016791205912301
181     iwf   2     339750101       FND  2020-03-16  -0.25511734574020883  0.00021771504945520011
182     iwf   2     43283X105       HGV  2020-03-16  -0.25026288718825329  1.6725804711295053e-05
183     iwf   2     552953101       MGM  2020-03-16  -0.33613982805897069  8.1791793434148613e-05
184     iwf   2     62886E108       VYX  2020-03-16  -0.29280002056071042  0.00029240258130384142
185     iwf   2     72703H101      PLNT  2020-03-16  -0.28121527295120263  0.00039815995697938802
186     iwf   2     828806109       SPG  2020-03-16  -0.26712699494960646   0.0026482516812431213
187     iwf   2     852234103       XYZ  2020-03-16  -0.28561536903679519   0.0014017064349145629
188     iwf   2     87165B103       SYF  2020-03-16  -0.26025694717692993  0.00041078554732669318
189     iwf   2     88023U101       SGI  2020-03-16  -0.28579214483149873  0.00024790281990128303
190     iwf   2     95058W100       WEN  2020-03-16   -0.2648809462397288  0.00027620466236387116
191     iwf   2  VGG1890L1076      CPRI  2020-03-16  -0.30653268946283696   0.0001545636850945105
192     iwf   2     018581108       BFH  2020-03-18  -0.26757364198992317  2.1347142127077516e-05
193     iwf   2     02376R102       AAL  2020-03-18  -0.25224649065601168  6.4769745747507031e-05
194     iwf   2     146869102      CVNA  2020-03-18  -0.26348189298604341   0.0002765126813449939
195     iwf   2     247361702       DAL  2020-03-18  -0.25992437374693977  0.00044177843229675323
196     iwf   2     552953101       MGM  2020-03-18  -0.25235596164728247  8.1791793434148613e-05
197     iwf   2     78573M104      SABR  2020-03-18   -0.3184210646800093  6.9688837721932297e-05
198     iwf   2     88023U101       SGI  2020-03-18  -0.28050222639046185  0.00024790281990128303
199     iwf   2     910047109       UAL  2020-03-18  -0.30290188759105852   0.0002849981852415863
200     iwf   2     95058W100       WEN  2020-03-18  -0.28857141610649861  0.00027620466236387116
201     iwf   2     983793100       XPO  2020-03-18  -0.25216092532916812  0.00028381681249276127
202     iwf   2     55087P104      LYFT  2020-03-19   0.28971973501043746  5.4741097440975254e-05
203     iwf   2     62886E108       VYX  2020-03-19    0.2691000755141244  0.00029240258130384142
204     iwf   2     88023U101       SGI  2020-03-19   0.38861159534556866  0.00024790281990128303
205     iwf   2     90353T100      UBER  2020-03-19   0.38259110614382497  0.00019584153334269202
206     iwf   2     95058W100       WEN  2020-03-19   0.42704175182201087  0.00027620466236387116
207     iwf   2  VGG1890L1076      CPRI  2020-03-19   0.33244687276304252   0.0001545636850945105
208     iwf   2     018581108       BFH  2020-03-24   0.35428786814331836  2.1347142127077516e-05
209     iwf   2     02376R102       AAL  2020-03-24   0.35804878793111672  6.4769745747507031e-05
210     iwf   2     146869102      CVNA  2020-03-24   0.43044690564644461   0.0002765126813449939
211     iwf   2     237194105       DRI  2020-03-24   0.31342907631929529  0.00088095222160209979
212     iwf   2     477143101      JBLU  2020-03-24   0.37026230839366137  2.1838363545003332e-05
213     iwf   2     512816109      LAMR  2020-03-24   0.26291399985665254  0.00050003229777500254
214     iwf   2     552953101       MGM  2020-03-24   0.33114760768570295  8.1791793434148613e-05
215     iwf   2     78573M104      SABR  2020-03-24   0.28219170029021745  6.9688837721932297e-05
216     iwf   2     910047109       UAL  2020-03-24   0.25714285714285712   0.0002849981852415863
217     iwf   2     94419L101         W  2020-03-24   0.42838366555181184  0.00037555878075433094
218     iwf   2  BMG667211046      NCLH  2020-03-24   0.42192346344527909  0.00016344888577265188
219     iwf   2     78573M104      SABR  2020-03-25   0.26923082801247245  6.9688837721932297e-05
220     iwf   3     78573M104      SABR  2020-04-06   0.28904434941293444    2.15256835486678e-05
221     iwf   3     94419L101         W  2020-04-06   0.41220617206401489  0.00025960397574346266
222     iwf   3  VGG1890L1076      CPRI  2020-04-06      0.25908559288749   3.795727006865543e-05
223     iwf   3  BMG667211046      NCLH  2020-04-29   0.25362869794679521  3.5850967448643295e-05
224     iwf   3     90138F102      TWLO  2020-05-07   0.39616010832742798  0.00084557782610109511
225     iwf   3     98980G102        ZS  2020-05-29   0.29406322412563424  0.00032463834502160252
226     iwf   3     02376R102       AAL  2020-06-04   0.41097036076894633  4.1756979859976569e-05
227     iwf   4     100557107       SAM  2020-07-24   0.25652663167180578  0.00031752654174526643
228     iwf   4     72352L106      PINS  2020-07-31   0.36125447354263684  0.00050480491653100384
229     iwf   4     146869102      CVNA  2020-08-06   0.28066844395213741  0.00044851066464215343
230     iwf   4     09061G101      BMRN  2020-08-19  -0.35279230109526927   0.0013795519471796534
231     iwf   4     79466L302       CRM  2020-08-26   0.26044878376843572    0.010287450119975963
232     iwf   4     67059N108      NTNX  2020-08-28   0.29170505535266167  0.00028836934439381947
233     iwf   4     98980L101        ZM  2020-09-01   0.40784372146604153   0.0028957196145632724
234     iwf   4     69553P100        PD  2020-09-03  -0.25778799463914592   0.0001338265213721707
235     iwf   4     146869102      CVNA  2020-09-22   0.30609776053753257  0.00044851066464215343
236     iwf   5     31188V100      FSLY  2020-10-15  -0.27179739628176336  0.00044313003912350085
237     iwf   5     016255101      ALGN  2020-10-22   0.34966205378458493   0.0015437310986941542
238     iwf   5     72352L106      PINS  2020-10-29   0.26923854459965901  0.00083707984045712795
239     iwf   5     09062X103      BIIB  2020-11-04   0.43973933359595518  0.00081838900485803182
240     iwf   5     88339J105       TTD  2020-11-06    0.2657808413219207   0.0012937016459869579
241     iwf   5     09062X103      BIIB  2020-11-09  -0.28166616329827387  0.00081838900485803182
242     iwf   5     534187109       LNC  2020-11-09   0.25124747655503854    4.51774551389225e-05
243     iwf   5     828806109       SPG  2020-11-09   0.27869356592221917  0.00093398644181453248
244     iwf   5     983134107      WYNN  2020-11-09   0.27688279280076333  0.00010490390076276729
245     iwf   5     98980G102        ZS  2020-12-03   0.26445949383312661  0.00059811816891314532
246     iwf   5     69553P100        PD  2020-12-04    0.2620518968570007  0.00011224033876717204
247     iwf   5     00847X104      AGIO  2020-12-21   0.28334839225610686  1.8044211932582512e-05
248     iwf   6     803607100      SRPT  2021-01-08  -0.51293280614419379  0.00069969270375154328
249     iwf   6     090043100      BILL  2021-02-05    0.3204404725021055  0.00054477639619185067
250     iwf   6     88076W103       TDC  2021-02-05    0.3707949307537235   0.0001083794110065614
251     iwf   6     88076W103       TDC  2021-02-08   0.30124049669248887   0.0001083794110065614
252     iwf   6     77311W101       RKT  2021-03-02   0.71193429938910135   5.174344457341583e-05
253     iwf   6     77311W101       RKT  2021-03-03   -0.3266827098851327   5.174344457341583e-05
254     iwf   6     004225108      ACAD  2021-03-09  -0.45347310780011452  0.00032009679654265081
255     iwf   7  JE00BYSS4X48      NVCR  2021-04-13   0.49628445954639244  0.00071094436075997531
256     iwf   7     405024100       HAE  2021-04-19  -0.36154569953139593  0.00027831703808065027
257     iwf   7     88076W103       TDC  2021-04-22   0.26629886277449577  0.00017246760026660472
258     iwf   7     31188V100      FSLY  2021-05-06  -0.27127109244687986  0.00028213415652672931
259     iwf   7     88339J105       TTD  2021-05-10  -0.25978560458250455   0.0014493663728725528
260     iwf   7     04271T100      ARRY  2021-05-12  -0.46052105705181556  1.6638125972496288e-05
261     iwf   7     462260100      IOVA  2021-05-19  -0.39451240862212122  0.00023151672627602987
262     iwf   7     09062X103      BIIB  2021-06-07   0.38341366407586164  0.00069394900832062156
263     iwf   7     95058W100       WEN  2021-06-08   0.25850009824739595   0.0001961100541508703
264     iwf   8     100557107       SAM  2021-07-23   -0.2601895262937699  0.00044836128171626011
265     iwf   8     91680M107      UPST  2021-08-11   0.26179249845140373  7.2292025418973274e-05
266     iwf   8     36467W109       GME  2021-08-24   0.27533503586958297  0.00059691726981216412
267     iwf   8     090043100      BILL  2021-08-27   0.29641637539365129  0.00064744353233153404
268     iwf   8     60937P106       MDB  2021-09-03   0.26331385876450963   0.0009102988756901876
269     iwf   9     644393100       NFE  2021-10-07   0.25509428226395547  3.4304118265963011e-05
270     iwf   9     163092109      CHGG  2021-11-02  -0.48820905368214029  0.00034863261269332037
271     iwf   9     70614W100      PTON  2021-11-05   -0.3534743089927922   0.0010712421042724293
272     iwf   9     88339J105       TTD  2021-11-08   0.29467536176461495   0.0014047048076050934
273     iwf   9  KYG851581069      STNE  2021-11-17  -0.34617808817664297  0.00034262343295877003
274     iwf   9     256163106      DOCU  2021-12-03  -0.42224791674660855    0.002302963940087653
275     iwf   9     670002401      NVAX  2021-12-07   0.28894688648530154  0.00071519597392196669
276     iwf  10     30303M102      META  2022-02-03  -0.26390083075996218    0.033507359305189929
277     iwf  10     090043100      BILL  2022-02-04   0.36052384208210597  0.00096312280092266354
278     iwf  10     70614W100      PTON  2022-02-08   0.25277312463071167  0.00040536849617743445
279     iwf  10     88076W103       TDC  2022-02-08   0.26340618003704841  0.00015636290039816299
280     iwf  10     91680M107      UPST  2022-02-16   0.35652088423500405  0.00029675643289668954
281     iwf  10     92537N108       VRT  2022-02-23  -0.36739927442907383  0.00033440126787360309
282     iwf  10     852234103       XYZ  2022-02-25   0.26139596156918321   0.0026974017141823772
283     iwf  10     29414B104      EPAM  2022-02-28  -0.45676331883276866   0.0015188099107638522
284     iwf  10     632307104      NTRA  2022-03-09  -0.32785389521350594  0.00029738280902228824
285     iwf  10     29414B104      EPAM  2022-03-16   0.25186637764649711   0.0015188099107638522
286     iwf  10  KYG851581069      STNE  2022-03-18   0.42039541231096611  0.00013948650036512439
287     iwf  10     36467W109       GME  2022-03-22   0.30721871952190427  0.00040099287895090796
288     iwf  11     64110L106      NFLX  2022-04-20  -0.35116607551133094   0.0075244063246431197
289     iwf  11     163092109      CHGG  2022-05-03  -0.30264209785752361  0.00017247635129444746
290     iwf  11     55087P104      LYFT  2022-05-04    -0.299089749495554  0.00053220978156565807
291     iwf  11     94419L101         W  2022-05-05  -0.25683125428974807  0.00022089184304937065
292     iwf  11     91680M107      UPST  2022-05-10  -0.56424216508237779  0.00024527878215834258
293     iwf  11     91332U101         U  2022-05-11  -0.37045504748319147  0.00070369480761929104
294     iwf  11     36467W109       GME  2022-05-25   0.29186759616053615  0.00049575741299415894
295     iwf  11     462260100      IOVA  2022-05-27  -0.53571428346165362  3.1990343737438229e-05
296     iwf  12     146869102      CVNA  2022-07-05   0.26108818075071438  0.00013269990221102327
297     iwf  12     670002401      NVAX  2022-07-14  -0.26204430044393368  0.00022394859094221779
298     iwf  12     72919P202      PLUG  2022-07-28   0.25902204752872904  0.00024191188716300946
299     iwf  12     02043Q107      ALNY  2022-08-03    0.4933436126217281  0.00099263661522721171
300     iwf  12     146869102      CVNA  2022-08-05   0.40071551162322527  0.00013269990221102327
301     iwf  12     18915M107       NET  2022-08-05   0.27058013821699878  0.00068900962498313499
302     iwf  12     670002401      NVAX  2022-08-09  -0.29641923529612446  0.00022394859094221779
303     iwf  12     88339J105       TTD  2022-08-10   0.36220179566549593   0.0010365503890523151
304     iwf  12     60937P106       MDB  2022-09-01  -0.25320568806999511  0.00092563826197051679
305     iwf  12     67059N108      NTNX  2022-09-01     0.291329545537234  9.0763275371477626e-05
306     iwf  12     679295105      OKTA  2022-09-01  -0.33698033410904404  8.7891408750514626e-05
307     iwf  12     83601L102       SHC  2022-09-19   -0.3326544311478199  0.00010489522691944988
308     iwf  13     338307101      FIVN  2022-10-10  -0.25555413371036573   0.0003127711720065378
309     iwf  13     368736104      GNRC  2022-10-19  -0.25341817415282686  0.00065037095890467154
310     iwf  13     23918K108       DVA  2022-10-28  -0.27090438330204292  0.00027320638083480105
311     iwf  13     98980F104       GTM  2022-11-02  -0.29172415020822107  0.00067030562483739423
312     iwf  13     00790R104       WMS  2022-11-03  -0.25015421943975646  0.00047057768260601757
313     iwf  13     534187109       LNC  2022-11-03  -0.33147802279964556  8.1393773476350146e-05
314     iwf  13     875372203      TNDM  2022-11-03  -0.28379430563928021  0.00016586874442836856
315     iwf  13     146869102      CVNA  2022-11-04  -0.38954702295763322  0.00013033866064723391
316     iwf  13     26142V105      DKNG  2022-11-04  -0.27823864935860376   0.0002897356755205708
317     iwf  13     90138F102      TWLO  2022-11-04  -0.34608321176028667  0.00027252115563447857
318     iwf  13     146869102      CVNA  2022-11-10   0.31620554477113738  0.00013033866064723391
319     iwf  13     303250104      FICO  2022-11-10   0.31099453252786602  0.00059747257143591046
320     iwf  13     683712103      OPEN  2022-11-10   0.26490064813538505  2.3064723749447263e-05
321     iwf  13     76680R206       RNG  2022-11-10   0.30112843147085688  0.00019949774652029041
322     iwf  13     91332U101         U  2022-11-10   0.29395347417787066  0.00027134748671752535
323     iwf  13     91680M107      UPST  2022-11-10   0.27198132721282353  2.7225814700367378e-08
324     iwf  13     94419L101         W  2022-11-10   0.27999997346297545  0.00010055656806437946
325     iwf  13     98585X104      YETI  2022-11-10    0.3157547122009583  0.00013693654931803669
326     iwf  13     26622P107      DOCS  2022-11-11   0.32700336984243483    9.04415027507147e-05
327     iwf  13     83601L102       SHC  2022-11-21    0.3289036586954861  4.2950731413959401e-05
328     iwf  13     679295105      OKTA  2022-12-01   0.26462867012584068  6.8125866859959075e-05
329     iwf  13     146869102      CVNA  2022-12-07  -0.42921015762630321  0.00013033866064723391
330     iwf  13     146869102      CVNA  2022-12-08   0.29503918927720174  0.00013033866064723391
331     iwf  13     670002401      NVAX  2022-12-15  -0.34300638447057297  8.8630874396518052e-05
332     iwf  13     40131M109        GH  2022-12-16  -0.27144932891928031    0.000307571198728211
333     iwf  14     644393100       NFE  2023-01-03     -1.33621494476062  0.00014300540295479809
334     iwf  14     G6674U108      NVCR  2023-01-05    0.6845313996158584  0.00043444812562378995
335     iwf  14     83601L102       SHC  2023-01-10   0.99652769844289502  5.1490661018155289e-05
336     iwf  14     146869102      CVNA  2023-01-12   0.45999991980466159  2.9864175056412221e-05
337     iwf  14     94419L101         W  2023-01-23    0.2680059985073846  9.9665044507295136e-05
338     iwf  14     549498103      LCID  2023-01-27   0.42999996609157987  0.00020011626157124198
339     iwf  14     146869102      CVNA  2023-01-30   0.28700127041506995  2.9864175056412221e-05
340     iwf  14     146869102      CVNA  2023-02-01   0.33333333333333326  2.9864175056412221e-05
341     iwf  14     016255101      ALGN  2023-02-02   0.27377625893786561  0.00072445749655600754
342     iwf  14     03831W108       APP  2023-02-09   0.27050474941831881  0.00013146987978420883
343     iwf  14     55087P104      LYFT  2023-02-10  -0.36436492872548298  0.00016268057468281919
344     iwf  14     771049103      RBLX  2023-02-15   0.26380723703826336  0.00074314890106106203
345     iwf  14     88339J105       TTD  2023-02-15   0.32812510984830778   0.0011483306139663991
346     iwf  14     91680M107      UPST  2023-02-15   0.28130561803018317  1.0261959703342699e-05
347     iwf  14     670002401      NVAX  2023-03-01  -0.25917926955140436  4.9134601901757542e-05
348     iwf  14     957638109       WAL  2023-03-13  -0.47061201220115045   0.0002304303566517897
349     iwf  14     31946M103     FCNCA  2023-03-27   0.53739574226328291  0.00012034937428611688
350     iwf  15     29355A107      ENPH  2023-04-26  -0.25734362058821458    0.001411283964857003
351     iwf  15     957638109       WAL  2023-05-04  -0.38451129909313897  0.00012060659736922637
352     iwf  15     683712103      OPEN  2023-05-05   0.32592587425221553  1.1231522508443327e-05
353     iwf  15     957638109       WAL  2023-05-05   0.49230729992398614  0.00012060659736922637
354     iwf  15     146869102      CVNA  2023-05-08   0.26116067003601429  5.5539180355829939e-05
355     iwf  15     670002401      NVAX  2023-05-09   0.27785244315364865  2.9040173857097196e-05
356     iwf  15     91680M107      UPST  2023-05-10   0.34634486216597371  1.0838717424657407e-05
357     iwf  15     803607100      SRPT  2023-05-15   0.30773715833863013  0.00059306483287717687
358     iwf  15     00751Y106       AAP  2023-05-31  -0.35035651440482307  2.9507653432672825e-05
359     iwf  15     60937P106       MDB  2023-06-02   0.28010613257373662  0.00079127606394146296
360     iwf  15     81730H109         S  2023-06-02  -0.35135135010738505   0.0001128251274450361
361     iwf  15     G6674U108      NVCR  2023-06-06  -0.43037209085997452  0.00031923316362825188
362     iwf  15     146869102      CVNA  2023-06-08   0.56020614226450682  5.5539180355829939e-05
363     iwf  16     77543R102      ROKU  2023-07-28   0.31412226722459669  4.4998595760760012e-05
364     iwf  16     98980F104       GTM  2023-08-01  -0.26984746581467289  0.00018853633726637807
365     iwf  16     92537N108       VRT  2023-08-02   0.29249931815001307  2.6909826689654902e-05
366     iwf  16     34959E109      FTNT  2023-08-04  -0.25065999396778349   0.0022912740086624651
367     iwf  16     03831W108       APP  2023-08-10   0.26487592505760627  6.9353626611812132e-05
368     iwf  16     G6674U108      NVCR  2023-08-28  -0.37504201356556044  0.00020048375821402832
369     iwf  17     803607100      SRPT  2023-10-31  -0.37473296233616382  0.00051646477650258999
370     iwf  17     70432V102      PAYC  2023-11-01   -0.3848634889963235   0.0006403970687973024
371     iwf  17     77543R102      ROKU  2023-11-02   0.30737021866521763  5.1376623386334405e-05
372     iwf  17     23804L103      DDOG  2023-11-07   0.28472649940374684   0.0011881276809626829
373     iwf  17     56600D107      MRVI  2023-11-08  -0.31686050420261258   3.029198547497758e-05
374     iwf  17     15961R105      CHPT  2023-11-17  -0.35463254775349062  7.0928736185517721e-05
375     iwf  17     90364P105      PATH  2023-12-01   0.26720650938698332  0.00023479669789515969
376     iwf  17     N14506104      ESTC  2023-12-01   0.37132897102102302  0.00030090076723613291
377     iwf  18     00857U107       AGL  2024-01-05  -0.28559602649006621  0.00013633179229654386
378     iwf  18     69608A108      PLTR  2024-02-06   0.30801445797701255   0.0013787722041501923
379     iwf  18     55087P104      LYFT  2024-02-14   0.35119532028164913  0.00021676438203228334
380     iwf  18     705573103      PEGA  2024-02-15   0.35673460354502717  8.5806745868394918e-05
381     iwf  18     697435105      PANW  2024-02-21  -0.28441092670854551   0.0037486245228740421
382     iwf  18     56600D107      MRVI  2024-02-23   0.63600771785648735  1.7406747644938014e-05
383     iwf  18     74624M102         P  2024-02-29   0.25000006792552276  0.00033467646293158185
384     iwf  18     926400102      VSXY  2024-03-07  -0.29703358161869864  3.8677759173783844e-05
385     iwf  19     25862V105        DV  2024-05-08  -0.38567219908003025  0.00018801967093012904
386     iwf  19     457730109      INSP  2024-05-08  -0.33473109793703515  0.00023794649370842934
387     iwf  19     29414B104      EPAM  2024-05-09  -0.26994384067521737  0.00058276369272067881
388     iwf  19     90364P105      PATH  2024-05-30  -0.34043714764859345   0.0002508420152017043
389     iwf  19     644393100       NFE  2024-06-14   0.31799168111217635  7.4491394901306346e-05
390     iwf  19     803607100      SRPT  2024-06-21   0.30137652810285931  0.00043799897220163104
391     iwf  19     02043Q107      ALNY  2024-06-24   0.34520216054143371   0.0005722034371773917
392     iwf  20     33829M101      FIVE  2024-07-17  -0.25051435065420924  0.00020895805865020167
393     iwf  20     513272104        LW  2024-07-24   -0.2823709610068863    0.000404301161304404
394     iwf  20     28176E108        EW  2024-07-25  -0.31339847201516924   0.0019581598823229427
395     iwf  20     252131107      DXCM  2024-07-26  -0.40658320903586309   0.0015436913941196172
396     iwf  20     34959E109      FTNT  2024-08-07   0.25300122889160459   0.0013653573239150365
397     iwf  20     457730109      INSP  2024-08-07   0.28140950902527151  0.00013703510585990787
398     iwf  20     26622P107      DOCS  2024-08-09   0.38737329251042318  5.0174852749078142e-05
399     iwf  20     338307101      FIVN  2024-08-09  -0.26489290284890599  0.00011194913031831824
400     iwf  20     70614W100      PTON  2024-08-22   0.35416676571208638  3.9762028534238669e-05
401     iwf  20     256677105        DG  2024-08-29  -0.32146316291090937   0.0010185563017001493
402     iwf  20     N14506104      ESTC  2024-08-30  -0.26485909986394585   0.0003213896316698217
403     iwf  20     644393100       NFE  2024-09-13   0.99153973130429307   4.946804250718158e-05
404     iwf  20     74967X103        RH  2024-09-13   0.25490275399468687  2.4373247425733895e-05
405     iwf  21     04626A103      ALAB  2024-11-05   0.37702801953957454  2.0779916405341991e-06
406     iwf  21     150870103        CE  2024-11-05  -0.26315786861700208  0.00013672679188648381
407     iwf  21     19260Q107      COIN  2024-11-06   0.31114657019864822   0.0010704625246917077
408     iwf  21     03831W108       APP  2024-11-07   0.46265199831288761   0.0012411875271749623
409     iwf  21     26701L100      BROS  2024-11-07   0.28133950250188033   5.020561211523692e-05
410     iwf  21     05464C101      AXON  2024-11-08   0.28678398437499997   0.0010422393984063959
411     iwf  21     26622P107      DOCS  2024-11-08   0.34154773045709952  1.4127422846846632e-05
412     iwf  21     34965K107      FTRE  2024-11-08   0.30193911320225575  7.2119849994281102e-07
413     iwf  21     594972408      MSTR  2024-11-11   0.25730339145501091  5.9682194324235735e-05
414     iwf  21     969904101       WSM  2024-11-20   0.27542977446614025  0.00042358295211892595
415     iwf  21     833445109      SNOW  2024-11-21   0.32706019658690932   0.0013166897978311202
416     iwf  21     256163106      DOCU  2024-12-06   0.27856115527705105  0.00045772643999661769
417     iwf  22     21037T109       CEG  2025-01-10   0.25159957676666411  0.00038043204662973842
418     iwf  22     04626A103      ALAB  2025-01-27  -0.28031154075469933  2.4325436851907172e-05
419     iwf  22     199908104       FIX  2025-01-27  -0.25713015657448135  0.00050580068084877009
420     iwf  22     92537N108       VRT  2025-01-27  -0.29879717411473716   0.0013827007069634716
421     iwf  22     92840M102       VST  2025-01-27  -0.28271675428516507    0.001590254886015706
422     iwf  22     090043100      BILL  2025-02-07  -0.35516344523032972  7.2932856365022324e-05
423     iwf  22     26622P107      DOCS  2025-02-07   0.35993830483255884  1.6190539511408861e-05
424     iwf  22     26701L100      BROS  2025-02-13   0.29099060574045033  7.6786806476999108e-05
425     iwf  22     88339J105       TTD  2025-02-13  -0.32978813778050731   0.0017838938813231865
426     iwf  22     955306105       WST  2025-02-13  -0.38218315769840527  0.00048923384212562493
427     iwf  22     91332U101         U  2025-02-20   0.30414536075852605  0.00010018607133777823
428     iwf  22     15118V207      CELH  2025-02-21   0.27771241890126408  0.00015747807405687048
429     iwf  22     L44385109      GLOB  2025-02-21  -0.27810818602785115  0.00022896167862198759
430     iwf  22     25862V105        DV  2025-02-28  -0.36033134324218374  5.3008958591285937e-05
431     iwf  22     34965K107      FTRE  2025-03-03  -0.25054152862489532  6.2961142167362371e-07
432     iwf  22     60937P106       MDB  2025-03-06   -0.2693749586944536  0.00056660330180948392
433     iwf  22     803607100      SRPT  2025-03-18  -0.27439563865109295  0.00037321948596875443
434     iwf  23     33829M101      FIVE  2025-04-03  -0.27807088755354459  0.00012561828679263047
435     iwf  23     74967X103        RH  2025-04-03  -0.40088231107710337   2.585189235673046e-05
436     iwf  23     146869102      CVNA  2025-04-09   0.25022689789951502  0.00030681760393946178
437     iwf  23     683344105      ONTO  2025-04-09   0.26297345685920503  5.9673983218220087e-05
438     iwf  23     74967X103        RH  2025-04-09   0.28568557843182019   2.585189235673046e-05
439     iwf  23     705573103      PEGA  2025-04-23   0.28781253749243452  0.00012008560313976436
440     iwf  23     78709Y105      SAIA  2025-04-25  -0.30656088296445938  0.00020944170240458717
441     iwf  23     803607100      SRPT  2025-05-06   -0.2656299071307574  0.00022638200414921465
442     iwf  23     55087P104      LYFT  2025-05-09   0.28076920142540573  0.00011779961065541034
443     iwf  23     683344105      ONTO  2025-05-09   -0.3021054987473859  5.9673983218220087e-05
444     iwf  23     629377508       NRG  2025-05-12   0.26213023415488568  0.00030595692850103986
445     iwf  23     644393100       NFE  2025-05-15  -0.62979352318719073  1.3287789062325713e-05
446     iwf  23     803607100      SRPT  2025-06-16  -0.42122718746738053  0.00022638200414921465
447     iwf  23     644393100       NFE  2025-06-30   0.32799997329711905  1.3287789062325713e-05
448     iwf  24     90400D108      RARE  2025-07-10  -0.25108588619958661  0.00010762184762102823
449     iwf  24     803607100      SRPT  2025-07-18   -0.3591260644624823  5.1661516359905143e-05
450     iwf  24     58506Q109      MEDP  2025-07-22   0.54665243277102538  0.00024342578698005431
451     iwf  24     974155103      WING  2025-07-30   0.26854974655702257  0.00031763479003477145
452     iwf  24     G3730V105      FTAI  2025-07-30   0.26563871471396716  0.00039796200039594767
453     iwf  24     45168D104      IDXX  2025-08-04   0.27493755333054404   0.0014699522450130574
454     iwf  24     366651107        IT  2025-08-05  -0.27554869511995173   0.0010285207633397243
455     iwf  24     457730109      INSP  2025-08-05  -0.32350899787151921  0.00012547576802592725
456     iwf  24     04626A103      ALAB  2025-08-06   0.28663131199586966  0.00043973786160106528
457     iwf  24     76680R206       RNG  2025-08-06   0.26968664276645393  7.4519331403104756e-05
458     iwf  24     88339J105       TTD  2025-08-08  -0.38605232176990201   0.0010910303215395086
459     iwf  24     92686J106      VKTX  2025-08-19  -0.42124018716940315  7.7400890459508654e-06
460     iwf  24     90353W103        UI  2025-08-22   0.30637276058482943  5.8865802167171947e-05
461     iwf  24     60937P106       MDB  2025-08-27   0.37958391928346757  5.3615307593662008e-05
462     iwf  24     74624M102         P  2025-08-28   0.32336510200146873  0.00052065164995158356
463     iwf  24     462222100      IONS  2025-09-02   0.34826459900052065  0.00018974442520851981
464     iwf  24     86627T108      SMMT  2025-09-08  -0.25153964444025478  8.4417203220881883e-05
465     iwf  24     21874C102       CNM  2025-09-09  -0.25364163543797236  0.00022583262333112936
466     iwf  24     68389X105      ORCL  2025-09-10   0.35948826632664566    0.012295230230868212
467     iwf  24     871607107      SNPS  2025-09-10   -0.3583731788271417   0.0023581583640783239
468     iwf  25     337738108      FISV  2025-10-29  -0.44043750892676059  0.00061771417581508331
469     iwf  25     85208M102       SFM  2025-10-30  -0.26111910334658583   0.0003414635720174477
470     iwf  25     803607100      SRPT  2025-11-04  -0.33742330235445606  5.2619757835152378e-05
471     iwf  25     88076W103       TDC  2025-11-05    0.3259295170640939  1.4305577065168229e-05
472     iwf  25     26603R106      DUOL  2025-11-06  -0.25490341635628178  0.00038778626807900755
473     iwf  25     457730109      INSP  2025-11-24   0.30510734762371161  6.8054163259243034e-05
474     iwf  25     74624M102         P  2025-12-03  -0.27312080250403947  0.00071541859172287361
475     iwf  25     25400Q105       DJT  2025-12-18   0.41929314973114495  4.5798264781577507e-05
476     iwf  25     90400D108      RARE  2025-12-29  -0.42322316158417839  8.6619300690274809e-05
477     iwf  25     218352102      CORT  2025-12-31  -0.50427349359119966  0.00025041466561901164
478     iwf  26     29355A107      ENPH  2026-02-04   0.38599785034434597  0.00013561752450111131
479     iwf  26     594972408      MSTR  2026-02-06   0.26114585820992109  7.4940288181797515e-05
480     iwf  26     60855R100       MOH  2026-02-06  -0.25514587226622709  0.00016212687907458137
481     iwf  26     50155Q100        KD  2026-02-09  -0.54916984862602281  1.4094421064895686e-05
482     iwf  26     88076W103       TDC  2026-02-11   0.29592889706959991    2.20934387584476e-05
483     iwf  26     91332U101         U  2026-02-11  -0.26324844319064378  2.7566475406978612e-05
484     iwf  26     76680R206       RNG  2026-02-20   0.34399466652782307  7.6870233287023408e-05
485     iwf  26     148929102      CAVA  2026-02-25   0.26356923765247808  0.00019469410726310912
486     iwf  26     172573107      CRCL  2026-02-25     0.354733596817012  1.8409601686107882e-05
487     iwf  26     349381103      FIGR  2026-02-27  -0.25734430062503211  8.3882910790146242e-06
488     iwf  26     86800U302      SMCI  2026-03-20  -0.33322507060101236  0.00022904509015507117
489     iwf  26     803607100      SRPT  2026-03-25   0.34980122850144135  5.8208768536349715e-05
490     iwf  27     053774105       CAR  2026-04-22  -0.37820913951855772  3.2764459235977351e-05
491     iwf  27     053774105       CAR  2026-04-23  -0.48384917301996988  3.2764459235977351e-05
492     iwf  27     049468101      TEAM  2026-05-01    0.2958157457185735  0.00040898725617426543
493     iwf  27     000360206      AAON  2026-05-07   0.31485243252201189  0.00020091108334196055
494     iwf  27     23804L103      DDOG  2026-05-07   0.31326968833359392   0.0013315065244533829
495     iwf  27     72703H101      PLNT  2026-05-07  -0.31191371245317367  0.00022268097337521846
496     iwf  27     773121108      RKLB  2026-05-08   0.34219901709166867   0.0011360063274834643
497     iwf  27     98980G102        ZS  2026-05-27   -0.3152221046448711  0.00050637403088861456
498     iwf  27     833445109      SNOW  2026-05-28   0.36482942169048349   0.0018072724739102881
499     iwf  27     24703L202      DELL  2026-05-29   0.32758240852375464  0.00025345646763776108
500     iwf  27     679295105      OKTA  2026-05-29   0.30141464373337712  0.00018748604930019308
501     iwf  27     573874104      MRVL  2026-06-02   0.32520633452683545  0.00021143006192551208
502     iwf  27     86800U302      SMCI  2026-06-10  -0.27977359996665896   0.0001936512832948782
503     iwf  27     95058W100       WEN  2026-06-24   0.25559103271515804  1.9758510840998598e-05
504     iwf  27     46269C102      IRDM  2026-06-29   0.25436580207449366  7.1869422089224235e-06
505     iwf  28     76680R206       RNG  2026-07-24    0.2509064012699862  8.9323106210682923e-06
506     iwf  28     02043Q107      ALNY  2026-07-30   -0.2830925991624329   0.0011903763082800824
507     iwf  28     093712107        BE  2026-07-30   0.26485493201335886   0.0024103734779220504
508     iwf  28     218352102      CORT  2026-07-30   0.27294248068355431  0.00024457830293480567
509     iwf  28     346375108      FORM  2026-07-30   0.26279210433976807  0.00036809152735256095
510     iwf  28     80004C200      SNDK  2026-07-30    0.2599395037665051   0.0098150095038093965
511     iwf  28     Q4982L109      IREN  2026-07-30   0.30535650012517168  5.2807490077308146e-05
512     iwf  28     44951W106      IESC  2026-07-31   0.30269098689667384  0.00018979545889762019
513     iwf  28     771049103      RBLX  2026-07-31  -0.26854325429508119   0.0010246113208403026
514     iwf  28     69608A108      PLTR  2026-08-04   0.29454836201182122   0.0076865657020768604
515     iwf  28     457669307      INSM  2026-08-06   0.33861853711786871  0.00067851857918046999
516     iwf  28     82982T106      SITM  2026-08-06   0.26583444944180346  0.00049151356581419395
517     iwf  28     91823B109      UWMC  2026-08-06  -0.34782607287224865  2.3357319653645293e-06
518     iwf  28     049468101      TEAM  2026-08-07   0.35309076701281605  0.00038964349912582716
519     iwf  28     G63755105       NIQ  2026-08-11   0.41952050432386789  6.9629301425457248e-06
520     iwf  28     92686J106      VKTX  2026-09-22   0.35669205068289545  1.0238939888122166e-05
521     iwf  28     303250104      FICO  2026-09-29  -0.26521901276766979  0.00065745382068915434
522  jensen   2     682189105        ON  2020-03-18  -0.26839829699366358  0.00016395273479707849
523  jensen   4     600544100      MLKN  2020-09-17    0.3344919278572549  4.4322218507962877e-05
524  jensen   6     88076W103       TDC  2021-02-05    0.3707949307537235  7.2744759187505661e-05
525  jensen   6     88076W103       TDC  2021-02-08   0.30124049669248887  7.2744759187505661e-05
526  jensen  23     595017104      MCHP  2025-04-09   0.27051483349876881  0.00015095774293982133
527  jensen  24     45168D104      IDXX  2025-08-04   0.27493755333054404  0.00065436973745051864
528  jensen  24     68389X105      ORCL  2025-09-10   0.35948826632664566    0.003720793897498605
529  jensen  28     303250104      FICO  2026-09-29  -0.26521901276766979  0.00021433200000158347
530   polen   1     58470H101       MED  2019-11-08  -0.27098040801085788  2.3214266714513849e-05
531   polen   2     33829M101      FIVE  2020-03-16  -0.25326541285230142  2.9299894382544698e-05
532   polen   2     339750101       FND  2020-03-16  -0.25511734574020883  5.3125749357597848e-05
533   polen   2     90337L108      USPH  2020-03-16  -0.29055681675780531  4.6627788909856081e-05
534   polen   2     03783C100      APPF  2020-03-17   0.29356400993948828  6.0135670325464725e-05
535   polen   3     76156B107      RVLV  2020-05-08   0.25650914915788348  6.3252583182569778e-05
536   polen   4     79466L302       CRM  2020-08-26   0.26044878376843572    0.038015035686952914
537   polen   5     016255101      ALGN  2020-10-22   0.34966205378458493    0.022745110331781001
538   polen   6     88034P109       TME  2021-03-24    -0.270839931470652  7.9694049201200758e-06
539   polen   8     647581107       EDU  2021-07-23  -0.54218751151458244    0.001153450291313607
540   polen   8     874080104       TAL  2021-07-23  -0.70760234570414349  8.3686043515746814e-06
541   polen   8     647581107       EDU  2021-07-26  -0.33788390456039341    0.001153450291313607
542   polen   8     874080104       TAL  2021-07-26  -0.26666665077209473  8.3686043515746814e-06
543   polen   8     874080104       TAL  2021-07-27   0.25227275214904532  8.3686043515746814e-06
544   polen   8     647581107       EDU  2021-08-24   0.26470590595571042    0.001153450291313607
545   polen   9     88339J105       TTD  2021-11-08   0.29467536176461495   6.646921651292066e-05
546   polen   9     898202106      TRUP  2021-12-07   0.39032031990765548  0.00023596388346856266
547   polen  10     30303M102      META  2022-02-03  -0.26390083075996218    0.059000483704974502
548   polen  10     30744W107     FTCHQ  2022-02-25   0.39373749215807785  5.1484780762853611e-05
549   polen  10     29414B104      EPAM  2022-02-28  -0.45676331883276866  3.7929081553841258e-05
550   polen  10     01609W102      BABA  2022-03-16   0.36763941233274866  4.4849711137624516e-06
551   polen  10     29414B104      EPAM  2022-03-16   0.25186637764649711  3.7929081553841258e-05
552   polen  10     874080104       TAL  2022-03-16   0.36649211555362315  1.1422398342166542e-06
553   polen  10     88034P109       TME  2022-03-16   0.29329622191497129   1.358929449825402e-05
554   polen  11     64110L106      NFLX  2022-04-20  -0.35116607551133094    0.036608521466322971
555   polen  11     12047B105      BMBL  2022-05-12   0.26829277792088613  0.00014432381860206333
556   polen  11     30744W107     FTCHQ  2022-05-27   0.26692705204671485  0.00018470012499668817
557   polen  12     74340E103      PGNY  2022-08-05   0.38226405418638354  0.00023735516747413628
558   polen  12     88339J105       TTD  2022-08-10   0.36220179566549593  4.2824258247280204e-05
559   polen  12     30744W107     FTCHQ  2022-08-26    0.2610062663600381  0.00010220265331394677
560   polen  13     303250104      FICO  2022-11-10   0.31099453252786602  8.6689245830730443e-05
561   polen  13     98585X104      YETI  2022-11-10    0.3157547122009583  0.00022491587852044117
562   polen  13     26622P107      DOCS  2022-11-11   0.32700336984243483  0.00017931649492999556
563   polen  13     88034P109       TME  2022-11-15   0.30561798182313482  2.4564287106155281e-05
564   polen  13     30744W107     FTCHQ  2022-12-01  -0.35058823753805723   0.0001220931898468995
565   polen  14     016255101      ALGN  2023-02-02   0.27377625893786561    0.010315560234813184
566   polen  14     88339J105       TTD  2023-02-15   0.32812510984830778  5.2823611511755274e-05
567   polen  16     527064109      LESL  2023-07-14  -0.29621846483434033  6.1081027249926592e-05
568   polen  16     30744W107     FTCHQ  2023-08-18  -0.45168072067321385  7.2882223022635662e-05
569   polen  17     70432V102      PAYC  2023-11-01   -0.3848634889963235  0.00011826288054454648
570   polen  17     35138V102      FOXF  2023-11-03  -0.27186333719254241  0.00023562193219592664
571   polen  18     03783C100      APPF  2024-01-26   0.28260120082238904  0.00011311601913719949
572   polen  18     35138V102      FOXF  2024-02-23    -0.268236429969547  0.00015577771953170064
573   polen  18     29260V105      DAVA  2024-02-29  -0.41758072161257331  0.00012484394010700231
574   polen  19     83066P309      SKIL  2024-04-16  -0.40760870410273808  1.6254133578198474e-05
575   polen  19     83066P309      SKIL  2024-04-24   0.50612965394315923  1.6254133578198474e-05
576   polen  19     98379L100      XPEL  2024-05-02  -0.38910578079454916  6.2999105557879818e-05
577   polen  19     29414B104      EPAM  2024-05-09  -0.26994384067521737  0.00022775080578956583
578   polen  19     82982T106      SITM  2024-05-09   0.28291372974593298  0.00013257091329565214
579   polen  19     83066P309      SKIL  2024-06-24   0.28197673773881604  1.6254133578198474e-05
580   polen  20     33829M101      FIVE  2024-07-17  -0.25051435065420924  5.6825995006955388e-05
581   polen  20     38267D109      GSHD  2024-07-25   0.29208528987345028   0.0001859910517052341
582   polen  20     76156B107      RVLV  2024-08-07   0.32669321973915899  0.00020438273789919611
583   polen  20     26622P107      DOCS  2024-08-09   0.38737329251042318  7.4037896072827521e-05
584   polen  20     722304102       PDD  2024-08-26  -0.28505037898788199  0.00018305176312352923
585   polen  20     83066P309      SKIL  2024-08-29   0.28977779812282978   2.537008474153397e-05
586   polen  20     74967X103        RH  2024-09-13   0.25490275399468687  5.0803422887034562e-05
587   polen  20     74340E103      PGNY  2024-09-19  -0.32651396379736874  0.00025001882687638769
588   polen  21     76156B107      RVLV  2024-11-06   0.27901607201421141  0.00025766626127754282
589   polen  21     26701L100      BROS  2024-11-07   0.28133950250188033  3.6578539405391719e-05
590   polen  21     001744101       AMN  2024-11-08  -0.29007818824618259  4.9034914663337378e-05
591   polen  21     83066P309      SKIL  2024-12-11   0.25271740486046057  2.4049654364935115e-05
592   polen  22     26701L100      BROS  2025-02-13   0.29099060574045033   0.0001486372627291757
593   polen  22     L44385109      GLOB  2025-02-21  -0.27810818602785115   0.0036761222780331798
594   polen  23     78709Y105      SAIA  2025-04-25  -0.30656088296445938  2.7037001278340354e-05
595   polen  24     75134P600      METC  2025-07-10   0.30944877248221525  2.5083265299499309e-05
596   polen  24     58506Q109      MEDP  2025-07-22   0.54665243277102538   4.438249669662965e-05
597   polen  24     G3730V105      FTAI  2025-07-30   0.26563871471396716  5.1761304999804588e-05
598   polen  24     030111207      AMSC  2025-07-31    0.2938097462653253  5.3167473268618693e-05
599   polen  24     02081G201      ATEC  2025-08-01   0.30151233998687932  1.1646904308657079e-05
600   polen  24     45168D104      IDXX  2025-08-04   0.27493755333054404    0.019675500845267486
601   polen  24     366651107        IT  2025-08-05  -0.27554869511995173   0.0096658207582934978
602   polen  24     98423F109      XMTR  2025-08-05   0.42977073816734035  7.9864846171519951e-06
603   polen  24     65487K100      LASR  2025-08-08   0.27747926212533813  1.8374643998695094e-05
604   polen  24     00760J108      AEHR  2025-08-25   0.35856351570922862  8.3326103188663301e-06
605   polen  24     21874C102       CNM  2025-09-09  -0.25364163543797236  6.2992023763054291e-05
606   polen  24     68389X105      ORCL  2025-09-10   0.35948826632664566    0.080398133999117966
607   polen  25     74366E102      PTGX  2025-10-10   0.29773267917497392  4.3833920678711443e-05
608   polen  25     00218A105      ASPI  2025-10-13   0.31490617417030098  7.2741829559466801e-05
609   polen  25     093712107        BE  2025-10-13    0.2652238999317158  0.00036073980134458515
610   polen  25     109504100      BRLT  2025-10-13   0.25943406623808296  2.9962924041803862e-06
611   polen  25     50015M109       KOD  2025-10-20   0.25531916908320507  1.1461833788918918e-05
612   polen  25     829401108      SION  2025-10-21   0.31987574512468075  2.9845011155539647e-05
613   polen  25     450047303       IRS  2025-10-27   0.30279895728372197  3.6634254641223535e-05
614   polen  25     86333M108       LRN  2025-10-29  -0.54373735681157398   5.431534388054528e-05
615   polen  25     40131M109        GH  2025-10-30   0.27867729285380016  3.5032723641140946e-05
616   polen  25     80517M109       SVV  2025-10-31  -0.30385484831315701  5.6015763275881399e-06
617   polen  25     76134H101      RHLD  2025-11-03   0.96809657905672264  4.8990239507644928e-05
618   polen  25     45174J509      IHRT  2025-11-04   0.37113398345407878  1.3203678526455786e-05
619   polen  25     98423F109      XMTR  2025-11-04   0.28927320002758328  1.4659766318811594e-05
620   polen  25     030111207      AMSC  2025-11-06  -0.38488723723719864  9.1181593424093725e-05
621   polen  25     26856L103       ELF  2025-11-06  -0.35042009907399629  2.7861626805170796e-05
622   polen  25     733245104      PRCH  2025-11-06  -0.33395989417083305  0.00011844394876242776
623   polen  25     88339P101      REAL  2025-11-11   0.38090985633887575  2.4877768496650979e-05
624   polen  25     87151X101       SYM  2025-11-25    0.3936170607901528  1.4672622459494587e-05
625   polen  25     74624M102         P  2025-12-03  -0.27312080250403947   1.622467679694869e-05
626   polen  25     93403J106      WRBY  2025-12-10   0.27347117007956401  5.9749011219213126e-05
627   polen  25     218352102      CORT  2025-12-31  -0.50427349359119966   7.652809285061501e-05
628   polen  26     80004C200      SNDK  2026-01-06   0.27564952572933255  1.8855988870519047e-05
629   polen  26     05614L209        BW  2026-01-08   0.28885135407252749  3.3108280245181481e-05
630   polen  26     765504105        RR  2026-01-27   0.44619430751541689  8.8693745492257708e-06
631   polen  26     70614W100      PTON  2026-02-05  -0.25719120476662893  9.6796840723788936e-06
632   polen  26     743713109      PRLB  2026-02-06   0.27991613481029765  8.9617910037479258e-06
633   polen  26     00760J108      AEHR  2026-02-11   0.26164735633161196  2.5962916718416356e-05
634   polen  26     91332U101         U  2026-02-11  -0.26324844319064378  1.0278640068068917e-05
635   polen  26     G4705A100      ICLR  2026-02-12  -0.39852784889466608  0.00081870507119452714
636   polen  26     21676P103       CPS  2026-02-13   0.32357243757915644  1.0704635508853801e-05
637   polen  26     384747101      GRAL  2026-02-20   -0.5054663676927863  4.9440667853859889e-05
638   polen  26     18467V109       YOU  2026-02-25   0.38960270349263548  5.8914251274887615e-05
639   polen  26     124155102      BFLY  2026-02-26   0.50645168385818495  7.6755623635916203e-05
640   polen  26     29415C101      EOSE  2026-02-26  -0.39442949669217253  1.0316862215387462e-05
641   polen  26     349381103      FIGR  2026-02-27  -0.25734430062503211   2.233006176445075e-05
642   polen  26     05614L209        BW  2026-03-04   0.45679007839673469  3.3108280245181481e-05
643   polen  26     78397Q109       SES  2026-03-05  -0.36842104162425793  2.5994519387707666e-05
644   polen  26     68062P106      OLMA  2026-03-09  -0.25754057696280341  1.6234803690664025e-05
645   polen  26     76134H101      RHLD  2026-03-12  -0.25071572739588222  0.00018438376678358328
646   polen  26     05614L209        BW  2026-03-17   0.26916523926909219  3.3108280245181481e-05
647   polen  26     136635109      CSIQ  2026-03-19  -0.26943847740028803  2.2559223823122598e-05
648   polen  26     72703X106        PL  2026-03-20   0.25482206898659499  9.3933767004925823e-05
649   polen  26     50015M109       KOD  2026-03-26   0.74769223391354744  4.9362771544687791e-05
650   polen  26     74017N105      PGEN  2026-03-26   0.25483878212094413  7.5144741628256478e-06
651   polen  26     04010E109       AGX  2026-03-27   0.37914086055305596  0.00033299314110416461
652   polen  27     00760J108      AEHR  2026-04-08   0.25691541984899713  0.00020365042789490469
653   polen  27     877619106      TSHA  2026-04-15   0.27388534000108944  9.8869519769355613e-05
654   polen  27     00246W103      AXTI  2026-04-16   0.29953914480707144  0.00019458751194416179
655   polen  27     92259N302      VELO  2026-04-21   0.31105399234870457  3.9903808294330828e-05
656   polen  27     093712107        BE  2026-04-29   0.27212089690432006  0.00063012068426179357
657   polen  27     25402D102      DOCN  2026-05-05   0.40400705541965376  0.00057086727544341772
658   polen  27     81663L200       WGS  2026-05-05  -0.49197706217434256  0.00034392581417295158
659   polen  27     859241101      STRL  2026-05-05   0.52221952230528434   7.192502758420372e-05
660   polen  27     922417100      VECO  2026-05-06   0.25171572821060217  2.8172618810267256e-05
661   polen  27     03214Q108      AMPX  2026-05-07  -0.27399728604667495  0.00049234118830484555
662   polen  27     08774B508      BETR  2026-05-07  -0.28507843898901319    3.93230179854163e-05
663   polen  27     20459V105      GPGI  2026-05-07  -0.25887738875257527  3.9515531018969075e-05
664   polen  27     31188V100      FSLY  2026-05-07  -0.38232498611024845  0.00047947249097897741
665   polen  27     71742Q106      PAHC  2026-05-07  -0.26222224849801024   2.592146837875158e-05
666   polen  27     819047101      SHAK  2026-05-07  -0.28263572034900764  0.00011529856683432827
667   polen  27     82982T106      SITM  2026-05-07   0.27911375306617603  0.00016963905410438018
668   polen  27     98423F109      XMTR  2026-05-07   0.39184393397543804  6.9395587560886808e-05
669   polen  27     773121108      RKLB  2026-05-08   0.34219901709166867  0.00010464062194802661
670   polen  27     05614L209        BW  2026-05-11   0.30055019924512805  0.00027588349016772161
671   polen  27     92835K103       VPG  2026-05-12    0.2848348596895891  7.2875418014667852e-05
672   polen  27     92259N302      VELO  2026-05-13    0.4943100712549342  3.9903808294330828e-05
673   polen  27     15102K100      CELC  2026-06-02  -0.25650619022743804  0.00013565417420241142
674   polen  27     72703X106        PL  2026-06-05   -0.2598207644327537  0.00041358800081084607
675   polen  27     92259N302      VELO  2026-06-11   0.34964727506489868  3.9903808294330828e-05
676   polen  27     124155102      BFLY  2026-06-18    0.5586689245309584  0.00011353565103839129
677   polen  28     706915105      PENG  2026-07-08   0.25131561738664954  0.00018522009523581976
678   polen  28     65487K100      LASR  2026-07-09    0.2731765285604979   0.0008001740380965942
679   polen  28     750102105       RXT  2026-07-09  -0.33586627108989897  0.00039885359701651447
680   polen  28     00760J108      AEHR  2026-07-21    0.2785677725146527  0.00054733940243571961
681   polen  28     76680R206       RNG  2026-07-24    0.2509064012699862  0.00013473540198088427
682   polen  28     00246W103      AXTI  2026-07-30   0.26967803832320891  0.00032720616875972844
683   polen  28     093712107        BE  2026-07-30   0.26485493201335886   0.0010646705882041902
684   polen  28     346375108      FORM  2026-07-30   0.26279210433976807  4.9463401553735952e-05
685   polen  28     740444104      PLPC  2026-07-30    0.2996366824210186  0.00024310153110185476
686   polen  28     80004C200      SNDK  2026-07-30    0.2599395037665051  3.7795027596339161e-05
687   polen  28     00246W103      AXTI  2026-07-31   0.28738819925723114  0.00032720616875972844
688   polen  28     44951W106      IESC  2026-07-31   0.30269098689667384  0.00046031782201041245
689   polen  28     05637B105      BLZE  2026-08-04   0.26940351005976515  1.8123664419245837e-05
690   polen  28     94419L101         W  2026-08-04    0.2997425260805533  1.9119548711788437e-05
691   polen  28     343389409       FTK  2026-08-05   0.27862463188373021  0.00039603294402155038
692   polen  28     92835K103       VPG  2026-08-05  -0.27168319248917083   0.0004227666194103708
693   polen  28     090168105      BLLN  2026-08-06  -0.38887777035487037  0.00017541111295806512
694   polen  28     82982T106      SITM  2026-08-06   0.26583444944180346  0.00035670158640615254
695   polen  28     88556E102      TDUP  2026-08-06  -0.50477710331306902   4.441929885745904e-05
696   polen  28     65487K100      LASR  2026-08-07  -0.25563365638923341   0.0008001740380965942
697   polen  28     567908108       HZO  2026-08-10   0.46076228940850594  2.1289255284281147e-05
698   polen  28     14154A102      CDNL  2026-08-11  -0.36216665903727219  0.00024977937323817669
699   polen  28     29772L108      ETON  2026-08-14   0.44264710075990088  0.00014148223169122045
700   polen  28     44916Y106      PURR  2026-08-19   0.30416674889900275  0.00023066895396814296
701   polen  28     50015M109       KOD  2026-09-28    1.7795982197921361  0.00011901622581548297
```

### MANIFEST.json pull times, libraries and Section 2 row counts

```
{
 "edgar": "2026-10-05T09:49:30Z",
 "figi": "2026-10-02T21:10:16Z",
 "figi2": "2026-10-05T09:55:29Z",
 "french": "2026-10-02T21:15:47Z",
 "navret": "2026-10-05T10:05:37Z",
 "prices": "2026-10-05T10:04:43Z",
 "sec": "2026-10-05T10:00:41Z"
}
{
 "lxml": "6.1.3",
 "numpy": "2.5.3",
 "pandas": "3.0.6",
 "pyarrow": "25.0.1",
 "python": "3.12.13",
 "requests": "2.34.2",
 "yfinance": "1.7.0"
}
{
 "edgar/nport/filings_ivv.csv": 29,
 "edgar/nport/filings_iwf.csv": 28,
 "edgar/nport/holdings_ivv.csv": 14710,
 "edgar/nport/holdings_iwf.csv": 12862,
 "edgar/nport_returns/akre_monthly.csv": 216,
 "edgar/nport_returns/jensen_monthly.csv": 312,
 "edgar/nport_returns/polen_monthly.csv": 168,
 "edgar/nport_returns/series_resolved.csv": 3,
 "french/ff5_monthly.csv": 758,
 "french/mom_monthly.csv": 1196,
 "openfigi/fallback.csv": 2519,
 "openfigi/mapping.csv": 1622,
 "prices/missing.csv": 33,
 "prices/nav_adjclose.csv": 2723,
 "sec/series_resolved.csv": 2,
 "sec/sic.csv": 1258
}
{
 "edgar/nport_returns/class_pages/C000013260.html": {
  "form": "class page (HTML)",
  "sha256": "8cdba0908348afd9e558fc9325f7085489e29de3ffb51109d1febc084e773439",
  "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=C000013260&type=NPORT-P&dateb=&owner=include&count=1"
 },
 "edgar/nport_returns/class_pages/C000080287.html": {
  "form": "class page (HTML)",
  "sha256": "a5c5ff9788ccd2e022a36f9ebef993232dd395c1015b0ad2b849394ef56a86ef",
  "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=C000080287&type=NPORT-P&dateb=&owner=include&count=1"
 },
 "edgar/nport_returns/class_pages/C000089998.html": {
  "form": "class page (HTML)",
  "sha256": "786738c70fcc93456fa57a7186e2d83cb05964d8c91067b65ce62be458d48644",
  "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=C000089998&type=NPORT-P&dateb=&owner=include&count=1"
 }
}
```

## Tests run

`pytest -p socket --disable-socket -q`:

```
...........................................                              [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\Utkarsh\10. Quant Projects\6) Attribution Engine On Real Holdings\repo-clone\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
43 passed, 1 warning in 4.03s
```

That is 26 Section 1 tests, plus 17 for Section 2:

- `test_mapping.py`, 9;
- `test_data_loaders.py`, 2;
- `test_nav_returns.py`, 3;
- `test_returns_calendar.py`, 3.

## Fresh-clone check

Per 02c Section E: the 6 step commits were pushed first (`5f3b220..8f996a0`); `git ls-remote origin refs/heads/main` returned `8f996a07cd0e03d103931272412af0c16aa2a5b8`, equal to local `HEAD`. Then GitHub was cloned into `C:\t\s2c`. Install output is trimmed to its last lines:

```
$ git clone -q https://github.com/uty101/Attribution-Engine-On-Real-Holdings.git /c/t/s2c
$ git log --oneline -1
8f996a0 step 2.5: coverage mapping columns and review lists
$ uv venv --python 3.12
Using CPython 3.12.13
Creating virtual environment at: .venv
Activate with: .venv\Scripts\activate
$ uv pip install -r requirements-lock.txt
 + wrapt==2.5.0
 + yfinance==1.7.0
$ uv pip install -e . --no-deps
 + attrib==0.0.0 (from file:///C:/t/s2c)
$ .venv/Scripts/python.exe -m pytest -p socket --disable-socket -q
...........................................                              [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\t\s2c\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
43 passed, 1 warning in 23.64s
$ .venv/Scripts/python.exe scripts/run_all.py --section 2
section 1: all checks passed
section 2: all checks passed
exit 0
$ sha256sum outputs/tables/*.csv data/processed/security_map.csv
7facd20083ecad24bddf7fb6dec37fb3db4e23b346adce746b26a79ea1a2ec1c *outputs/tables/coverage.csv
95d7a7ce41a8dec4d1351e7cdcdf8f34e8840544dfb1dbd5c9706721d5a14e99 *outputs/tables/large_moves.csv
26395b50cd2cd8eb1eca71b9e7eb89b4bdeebe8bc3d09a4ffbc6f277f1ac3076 *outputs/tables/nav_monthly.csv
eca60976a01ce84b273c06ee1360cd69d26f808f9634bc7bb8604551ff5bb5e3 *outputs/tables/nocik_top.csv
ffa48bd0ea8fc4be79a98af7755f859ce58a205f052c2e3159e4176eee1ca323 *outputs/tables/unmapped_top.csv
efc75aeddc362978b9230838330d9ad3c0f4a41233253ed52390c3cc74e494e5 *outputs/tables/unpriced_top.csv
de9dd41707200a3497cce7db6e8b5652cd4f7d65b1913a7b6f101a6d894111c0 *data/processed/security_map.csv
$ git status --short
```

Every hash matches the local run (see "Section 2 run"), and `git status --short` in the clone printed nothing.

## Runtime per step

- 2.1: `--stage figi` 7 min 48 s (a first run was cut off by the 30-minute background limit before writing anything); `--stage sec` 4 min 47 s.
- 2.2: `--stage french`, seconds.
- 2.3: `--stage prices`, 3 min 46 s (session 2, stopped at the NAV call).
- 2.1b: `--stage navret`, 27 s, run 3 times: twice in session 2b (the second added class names) and once in session 2c (class-page hashes for the manifest). The return CSVs did not change between runs.
- 2.1c: `--stage edgar` 1 min 58 s; `--stage figi2` 3 min 31 s, with 1 HTTP 429 retried; `--stage sec` 4 min 25 s. A first `--stage sec` attempt was killed after 6 s by my own `Select-Object -First 2` on its output pipe. It had re-downloaded `company_tickers.json` but not written `sic.csv`, and the rerun wrote both.
- 2.3b: `--stage prices`, 3 min 30 s.
- 2.5: `run_all.py --section 2`, about 20 s.

## Deviations from PLAN.md

Accepted in 02b and 02c, not repeated: the OpenFIGI client in `pull_data.py`; `exchCode: "US"` on pass-1 ISIN jobs; blank `ff12` for `no_match`; `cik` overrides only on rows with a ticker; French blocks as filed and its own User-Agent; ETFs in Other; `attrs["class_ids"]`; class names from the HTML page; no full-text search fallback; the `etf_successor` reading of "ETF class"; `series_resolved.csv` under `nport_returns/`.

New in session 2c:

- **2.0c is a commit the instructions do not name.** It applies 02c C items 3 and 4 (`CLAUDE.md` amendment 11, `decisions/OPEN.md`, `decisions/section_2_review.md`), in the way step 1.0 applied the session 0 decisions.
- **Commit contents follow the 02c order, not file boundaries.**
  - `scripts/pull_data.py` in `e21e4c1` (2.1c) already carries the 2.3b NAV ticker list and the class-page manifest entries of 2.1b-2.
  - `monthly_returns` and `month_end_closes` are in `da938d2` (2.1b-2), which needs them, not in 2.4.
- **2 expected values in existing tests changed.** In `test_overrides_beat_openfigi` and `test_cik_override`, the expected `source` became `openfigi;override_ticker` and `openfigi;override_cik`. 02b step 2.1c defines `source` as the pass name with `;override_ticker` / `;override_cik` appended. No tolerance or assertion was loosened.
- **2.1c, pass 2 for ISIN `sec_id`s.** A `sec_id` that is itself an ISIN is its own pass-2 ISIN, so pass 2 repeats the pass-1 query and pass 4 searches Yahoo for it. 02b's (i) and (ii) only cover CUSIPs.
- **2.1c, pass 2 acceptance.** Pass 2 accepts the first `marketSector` Equity result, the pass-1 rule, plus the name check. 02b names an exchange list only for passes 3 and 4.
- **2.1c, multiple pass-2 ISINs.** A `sec_id` with more than 1 N-PORT ISIN has each queried in sorted order until 1 is accepted.
- **2.1c, pass 4 fields.** The Yahoo result name is `longname`, else `shortname`. `quoteType` goes in `security_type`, and `market_sector` is blank.
- **2.1c, empty queries.** A query with no result is logged in `fallback.csv` as 1 row with a blank `rank` and the API's warning, or "no result", as `reject_reason`. Rows after an accepted one carry "an earlier result was accepted".
- **2.1c, fallback mappings in SECURITY_MAP.** A fallback mapping has a blank `figi`, since `fallback.csv` has no FIGI column. `figi_name` is the result's name.
- **2.1c, `--stage sec`.** The stage adds accepted fallback tickers to its ticker set. It re-downloads `company_tickers.json` and rebuilds `sic.csv` for all reachable CIKs (1258), not only the new ones.
- **2.1b-2, `nav_monthly.csv`.** It has no rows for missing months (02c: "Akre months 2025-08 to 2025-10 absent"). The source labels are `nport_b5`, `yfinance_etf` and `yfinance`.
- **2.1b-2, the cross-check is evidence only.** It is computed in the review script, not written to a table: 02b says "report only".
- **2.5, list order and ties.** `large_moves.csv` is sorted by entity alphabetically, then t, date and sec_id. `entity_of_max` ties go to the alphabetically first entity, then the earliest period.
- **2.4 and 2.5, gaps in a price series.** `daily_returns` takes each return from that ticker's previous available close, so a gap does not erase the move across it. `monthly_returns` gives no return for a month after one with no close, which keeps returns to calendar months.

## Not verified

- That the Akre Focus Fund converted into the AKRE ETF around 2025-10-27. This rests on yfinance metadata and the series' last filings; no reorganisation filing was read.
- That each fallback ticker is the right security beyond the first-token name check. The 20 largest are printed for the reviewer.
- The 33 tickers in `missing.csv`: yfinance returned no rows and recorded no error. Most look like acquired or delisted companies (CELG, ALXN, MXIM, HES, WBA, FLIR); that was not checked one by one.
- The one-off shell probes from sessions 2 and 2b (OpenFIGI without `exchCode`, yfinance AKRE, the EDGAR feed) are not committed.

## Open questions

1. **Unmatched weight after the fallbacks.** 254 `sec_id`s remain unmatched. 52 books have `unmapped_weight` above 2%:

   | entity | books | last book above 2% | max |
   |---|---|---|---|
   | Akre | 13 | 2022-09 | 7.0% |
   | IVV | 21 | 2024-09 | 6.9% |
   | IWF | 14 | 2022-12 | 4.2% |
   | Jensen | 4 | — | 7.0% |

   The causes:
   - Akre's is mostly Brookfield `112585104` (5.1% at its largest).
   - Jensen's 7.0% is Alphabet's pre-2015 CUSIP `38259P508` in 2021-06-30, and most of its 5.9% to 6.0% at 2019-09-30 and 2019-12-31 is United Technologies `913017109`.
   - OpenFIGI returns only non-US lines for Exxon `30231G102`, Ansys and United Technologies.

   `unmapped_top.csv` lists the 60 largest, for instruction 03's ticker overrides.
2. **Name-check rejections of the right company.** Of the 12 pass-4 rejections, 6 are the holding under a renamed or reworded company name:

   | sec_id | holding name | Yahoo result |
   |---|---|---|
   | `30231G102` | Exxon Mobil Corp. | ExxonMobil, `XOM` |
   | `369604103` | General Electric Co | GE Aerospace, `GE` |
   | `637071101` | National Oilwell Varco Inc | NOV Inc., `NOV` |
   | `74838J101` | Quidel Corp | QuidelOrtho, `QDEL` |
   | `531229854` | Liberty Media Formula One Group | Formula One Group, `FWONK` |
   | `531229870` | Liberty Formula One | Formula One Group, `FWONA` |

   The other 6 are correct rejections; the ticker now belongs to another company (BBT, LB, PS, SERV, STI, AMTD). These are candidates for `ticker` overrides; whether to accept them is the reviewer's call.
3. **Unpriced fallback mappings.** Some fallback mappings are tickers yfinance cannot price, so their weight moves from Unmapped to Unpriced:
   - DigitalBridge `25401T603` (pass 4, ticker DBRG; Akre up to 0.72%);
   - Celgene `151020104` (pass 3, CELG);
   - Hess, Walgreens, Maxim and others, listed in `missing.csv`.
4. **OPEN-32 overlap.** Under (a), the rows above with `no_cik` and no price count in both `unpriced_weight` and `other_nosic_weight`. There are 317 such rows across the 140 books. The largest is Celgene in IWF at 2019-09-30, at 0.50%.

## Files changed

- 2.1: `scripts/pull_data.py`, `data/raw/openfigi/mapping.csv`, `data/raw/sec/company_tickers.json`, `data/raw/sec/sic.csv`, `data/raw/MANIFEST.json`
- 2.2: `attrib/mapping.py`, `tests/test_mapping.py`, `scripts/pull_data.py`, `scripts/run_all.py`, `data/manual/overrides.csv`, `data/raw/french/` (3 files), `data/raw/MANIFEST.json`
- 2.3: `scripts/pull_data.py`, `attrib/returns.py`, `attrib/factors.py`, `tests/test_data_loaders.py`, `data/raw/prices/adjclose.parquet`, `data/raw/prices/missing.csv`, `data/raw/MANIFEST.json`
- 2.1b: `attrib/edgar.py`, `attrib/returns.py`, `attrib/config.py`, `config.toml`, `scripts/pull_data.py`, `tests/test_edgar_nport.py`, `tests/test_config.py`, `tests/test_nav_returns.py`, `data/raw/edgar/nport_returns/` (4 files), `data/raw/MANIFEST.json`
- 2.0c: `CLAUDE.md`, `decisions/OPEN.md`, `decisions/section_2_review.md`
- 2.1c: `attrib/edgar.py`, `attrib/mapping.py`, `tests/test_mapping.py`, `scripts/pull_data.py`, `data/raw/openfigi/fallback.csv`, `data/raw/edgar/nport/holdings_ivv.csv`, `data/raw/edgar/nport/holdings_iwf.csv`, `data/raw/sec/company_tickers.json`, `data/raw/sec/sic.csv`, `data/raw/MANIFEST.json`
- 2.3b: `data/raw/prices/adjclose.parquet`, `data/raw/prices/missing.csv`, `data/raw/prices/nav_adjclose.csv`, `data/raw/MANIFEST.json`
- 2.1b-2: `attrib/returns.py`, `scripts/run_all.py`, `tests/test_nav_returns.py`, `data/raw/MANIFEST.json`, `outputs/tables/nav_monthly.csv`
- 2.4: `attrib/returns.py`, `tests/test_returns_calendar.py`
- 2.5: `scripts/run_all.py`, `outputs/tables/coverage.csv`, `outputs/tables/unmapped_top.csv`, `outputs/tables/unpriced_top.csv`, `outputs/tables/nocik_top.csv`, `outputs/tables/large_moves.csv`
- Review: `review/section_2.md`, `instructions/02c_section_2_completion.status.md`

## Reviewer reads

1. `instructions/02c_section_2_completion.status.md`
2. This file: Section, Open questions, then "02b D item 4" and "every book whose remaining unmapped_weight exceeds 2%"
3. `outputs/tables/unmapped_top.csv` (for the overrides)
4. This file: "the 20 largest accepted fallback mappings" and "every name-check rejection"
5. `attrib/mapping.py` (`judge_results`, `build_security_map`) and `scripts/pull_data.py` (`stage_figi2`)
6. `scripts/run_all.py` (`nav_monthly`, `mapping_coverage`)
