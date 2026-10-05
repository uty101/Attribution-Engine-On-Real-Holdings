# Review — Section 3

## Section

Section 3, Book returns and reconstruction, run from `instructions/03_section_3.md`. Precedence (rule 13): that file over `CLAUDE.md` amendments and `PLAN.md`, over the kickoff. 28 quarters throughout (amendment 7).

Outcome: **completed.** No rule 4 stop.

- Step 3.0 applied the 91 override rows: 62 `ticker`, 29 `cik`. All 29 `cik` rows passed the name check, and every Section 1 and 2 check still passes.
- The benchmark check found no |gap| above `benchmark_gap_stop` (0.03). 1 quarter is above `benchmark_gap_max` (0.01): IWF t = 27, gap −1.16%. It is listed under 3.3 below.
- All 3 funds pass the NAV gate:

  | fund | corr | quarters |
  |---|---|---|
  | Akre | 0.990 | 26 |
  | Jensen | 0.9996 | 28 |
  | Polen | 0.998 | 28 |

## Steps completed

- 3.0 `data/manual/overrides.csv` (91 rows); the 2 override rule changes in `build_security_map`, with `cik_override_check`; `--stage sec --overrides-only` writing `data/raw/sec/cik_override_check.csv`; `--stage prices --new-only`; refreshed Section 2 outputs; 2 new tests in `tests/test_mapping.py` — `86df1a2`
- 3.1 `apply_return_overrides` and `return_overrides_with_t` in `attrib/returns.py`; `tests/test_overrides.py` — `92f1eb1`
- 3.2 `book_quarter`, `bucket_table`, `book_monthly`, `book_return` in `attrib/returns.py`; `tests/test_returns_book.py`; `run_all.py --section 3` writing `data/processed/position_returns.csv`, `outputs/tables/buckets.csv`, `book_quarterly.csv` and `book_monthly.csv` — `3f1bbfe`
- 3.3 `[gates] benchmark_gap_stop = 0.03` and its key in `tests/test_config.py`; `attrib/reconstruction.py` with `reconstruction_table`; the benchmark check; the 56 benchmark rows in `reconstruction.csv` — `ac2c391`
- 3.4 `gate` in `attrib/reconstruction.py`; `attrib/bootstrap.py` with `bootstrap_mean` (D-20); the fund rows of `reconstruction.csv`; `gate.csv`; the `gap` rows of `bootstrap.csv` — `2596b35`

## Evidence

### Section 3 run

```
$ python scripts/run_all.py --section 3
section 1: all checks passed
section 2: all checks passed
benchmark quarters with |gap| > benchmark_gap_max (0.01):
  entity   t     q_start       q_end  book_return  nav_return       gap  unmapped_weight  unpriced_weight  delisted_weight
0    iwf  27  2026-03-31  2026-06-30      0.15426    0.165848 -0.011588         0.000852              0.0              0.0
section 3: all checks passed
```

Running it a second time left every CSV under `outputs/tables/` and `data/processed/` byte-identical (sha256 of each file compared). The fresh clone (below) regenerated every committed output with `git status` clean.

### 3.0 the 2 pulls

`--stage sec --overrides-only` fetched the submissions JSON of 37 CIKs:
- the 25 distinct override CIKs (29 rows; DigitalBridge, Primo Water, Seagen and Horizon each have 2 CUSIPs on 1 CIK);
- 12 CIKs that override tickers reach in the committed `company_tickers.json` but `sic.csv` lacked.

It printed no "row changed" line, so no existing `sic.csv` row differs from its submissions JSON. `sic.csv` gained 36 rows: 1 of the 37 CIKs was already present. `company_tickers.json` was not downloaded again.

`--stage prices --new-only` requested the 68 `yf_ticker`s of SECURITY_MAP that were not columns of `adjclose.parquet`. That includes the 33 already in `missing.csv`, which are not columns either.
- 13 returned rows and were merged in as new columns.
- No date was added to the index.
- The script checks that every existing column is unchanged after the merge (`DataFrame.equals` on the old index and columns) and would stop under rule 4 otherwise.
- yfinance recorded no error text for any empty ticker. A single retry of `AVB` printed `possibly delisted; no price data found`.
- `nav_adjclose.csv` was not touched.

### 3.1 every override row (data/manual/overrides.csv, 91 rows)

```
      kind        sec_id period_date    value                                                            source_note
0   ticker     38259P508                GOOGL                   Alphabet Class A filed under Google's pre-2015 CUSIP
1   ticker     913017109                  RTX  United Technologies; became Raytheon Technologies (RTX) on 2020-04-03
2   ticker     112585104                   BN     Brookfield Asset Management Inc; renamed Brookfield Corp (BN) 2022
3   ticker     03662Q105                 ANSS                                                                  ANSYS
4      cik     03662Q105              1013462                                                                  ANSYS
5   ticker     30231G102                  XOM                                                            Exxon Mobil
6   ticker     25401T108                 DBRG                                                    DigitalBridge Group
7   ticker     19626G108                 DBRG                      Colony Capital; renamed DigitalBridge (DBRG) 2021
8      cik     25401T108              1679688                                                          DigitalBridge
9      cik     19626G108              1679688                                                          DigitalBridge
10  ticker  IE00BZ12WP82                  LIN                                                                  Linde
11  ticker     G5494J103                  LIN                                                                  Linde
12  ticker     512807108                 LRCX                                                           Lam Research
13  ticker     H82027105                 SOPH                                                        SOPHiA Genetics
14  ticker     74165N105                 PRMW                                                            Primo Water
15  ticker     74167P108                 PRMW                                                            Primo Water
16     cik     74165N105               884713                                                            Primo Water
17     cik     74167P108               884713                                                            Primo Water
18  ticker     369604103                   GE                                                       General Electric
19  ticker     040413106                 ANET                                                        Arista Networks
20  ticker     09247X101                  BLK                                                              BlackRock
21  ticker  IE00BY9D5467                  AGN                                                               Allergan
22     cik  IE00BY9D5467              1578845                                                               Allergan
23  ticker     N07059210                 ASML                                                           ASML Holding
24  ticker  GB00BZ09BD16                 TEAM                                                              Atlassian
25  ticker     G06242104                 TEAM                                                              Atlassian
26  ticker     755111507                  RTN                                                               Raytheon
27     cik     755111507              1047122                                                               Raytheon
28  ticker     G5960L103                  MDT                                                              Medtronic
29  ticker     00507V109                 ATVI                                                    Activision Blizzard
30     cik     00507V109               718877                                                    Activision Blizzard
31  ticker     90184L102                 TWTR                                                                Twitter
32     cik     90184L102              1418091                                                                Twitter
33  ticker     983919101                 XLNX                                                                 Xilinx
34     cik     983919101               743988                                                                 Xilinx
35  ticker     848637104                 SPLK                                                                 Splunk
36     cik     848637104              1353283                                                                 Splunk
37  ticker     26614N102                   DD                                                      DuPont de Nemours
38  ticker     285512109                   EA                                                        Electronic Arts
39     cik     285512109               712515                                                        Electronic Arts
40  ticker     G4388N106                 HELE                                                          Helen of Troy
41  ticker     Y4600W108                 KARO                                                               Karooooo
42  ticker     339041105                 CPAY                      FleetCor Technologies; renamed Corpay (CPAY) 2024
43  ticker     723787107                  PXD                                              Pioneer Natural Resources
44     cik     723787107              1038357                                              Pioneer Natural Resources
45  ticker     928563402                  VMW                                                                 VMware
46     cik     928563402              1124610                                                                 VMware
47  ticker     44919P508                 MTCH                                                            Match Group
48  ticker     054937107                  TFC                              BB&T; renamed Truist Financial (TFC) 2019
49  ticker     156782104                 CERN                                                                 Cerner
50     cik     156782104               804753                                                                 Cerner
51  ticker     812578102                 SGEN                                                       Seattle Genetics
52  ticker     81181C104                 SGEN                                                                 Seagen
53     cik     812578102              1060736                                                                 Seagen
54     cik     81181C104              1060736                                                                 Seagen
55  ticker     G46188101                 HZNP                                                   Horizon Therapeutics
56  ticker  IE00BQPVQZ61                 HZNP                                                   Horizon Therapeutics
57     cik     G46188101              1492426                                                   Horizon Therapeutics
58     cik  IE00BQPVQZ61              1492426                                                   Horizon Therapeutics
59  ticker  BMG475671050                 INFO                                                             IHS Markit
60     cik  BMG475671050              1598014                                                             IHS Markit
61  ticker  CH0102993182                  TEL                                                        TE Connectivity
62  ticker     682680103                  OKE                                                                  ONEOK
63  ticker     22266L106                 COUP                                                         Coupa Software
64     cik     22266L106              1385867                                                         Coupa Software
65  ticker     867914103                  STI                                                         SunTrust Banks
66     cik     867914103               750556                                                         SunTrust Banks
67  ticker     904767704                   UL                                                               Unilever
68  ticker     053484101                  AVB                                                  AvalonBay Communities
69     cik     053484101               915912                                                  AvalonBay Communities
70  ticker  JE00B783TY65                 APTV                                                                  Aptiv
71  ticker     86800U104                 SMCI                                                   Super Micro Computer
72  ticker     177376100                 CTXS                                                         Citrix Systems
73     cik     177376100               877890                                                         Citrix Systems
74  ticker     254709108                  DFS                                            Discover Financial Services
75     cik     254709108              1393612                                            Discover Financial Services
76  ticker     M22465104                 CHKP                                                   Check Point Software
77  ticker     78486Q101                 SIVB                                                    SVB Financial Group
78     cik     78486Q101               719739                                                    SVB Financial Group
79  ticker     94946T106                  WCG                                                  WellCare Health Plans
80     cik     94946T106              1279363                                                  WellCare Health Plans
81  ticker     G29018101                  DLO                                                                 dLocal
82  ticker     M7S64H106                 MNDY                                                             monday.com
83  ticker     30063P105                 EXAS                                                         Exact Sciences
84     cik     30063P105              1124140                                                         Exact Sciences
85  ticker     98936J101                  ZEN                                                                Zendesk
86     cik     98936J101              1463172                                                                Zendesk
87  ticker     531229854                FWONK                                     Liberty Media Formula One Series C
88  ticker     531229870                FWONA                                     Liberty Media Formula One Series A
89  ticker     637071101                  NOV                                National Oilwell Varco; renamed NOV Inc
90  ticker     74838J101                 QDEL                                            Quidel; renamed QuidelOrtho
```

### 3.1 the rows the overrides name, before (pre-3.0 map) and after (62 sec_ids)

```
             ticker        yf_ticker           cik             sic         ff12        map_status            source                                       
             before  after    before  after before    after before after before  after     before   after    before                                  after
sec_id                                                                                                                                                    
00507V109             ATVI             ATVI          718877         7372         BusEq   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
03662Q105             ANSS             ANSS         1013462         7372         BusEq   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
040413106             ANET             ANET         1596532         3576         BusEq   no_match  mapped  openfigi               openfigi;override_ticker
053484101              AVB              AVB          915912         6798         Money   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
054937107              TFC              TFC           92230         6021         Money   no_match  mapped  openfigi               openfigi;override_ticker
09247X101              BLK              BLK         2012383         6211         Money   no_match  mapped  openfigi               openfigi;override_ticker
112585104               BN               BN         1001085         6512         Money   no_match  mapped  openfigi               openfigi;override_ticker
156782104             CERN             CERN          804753         7373         BusEq   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
177376100             CTXS             CTXS          877890         7372         BusEq   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
19626G108             DBRG             DBRG         1679688         6282         Money   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
22266L106             COUP             COUP         1385867         7372         BusEq   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
25401T108             DBRG             DBRG         1679688         6282         Money   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
254709108              DFS              DFS         1393612         6141         Money   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
26614N102               DD               DD         1666700         2821         Chems   no_match  mapped  openfigi               openfigi;override_ticker
285512109               EA               EA          712515         7372         BusEq   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
30063P105             EXAS             EXAS         1124140         8071          Hlth   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
30231G102              XOM              XOM         2115436         2911         Enrgy   no_match  mapped  openfigi               openfigi;override_ticker
339041105             CPAY             CPAY         1175454         7389         Other   no_match  mapped  openfigi               openfigi;override_ticker
369604103               GE               GE           40545         3600         Manuf   no_match  mapped  openfigi               openfigi;override_ticker
38259P508            GOOGL            GOOGL         1652044         7370         BusEq   no_match  mapped  openfigi               openfigi;override_ticker
44919P508             MTCH             MTCH          891103         7370         BusEq   no_match  mapped  openfigi               openfigi;override_ticker
512807108             LRCX             LRCX          707549         3559         Manuf   no_match  mapped  openfigi               openfigi;override_ticker
531229854            FWONK            FWONK         1560385         4833         Telcm   no_match  mapped  openfigi               openfigi;override_ticker
531229870            FWONA            FWONA         1560385         4833         Telcm   no_match  mapped  openfigi               openfigi;override_ticker
637071101              NOV              NOV         1021860         3533         Manuf   no_match  mapped  openfigi               openfigi;override_ticker
682680103              OKE              OKE         1039684         4923         Utils   no_match  mapped  openfigi               openfigi;override_ticker
723787107              PXD              PXD         1038357         1311         Enrgy   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
74165N105             PRMW             PRMW          884713         2086         NoDur   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
74167P108             PRMW             PRMW          884713         2086         NoDur   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
74838J101             QDEL             QDEL         1906324         2835          Hlth   no_match  mapped  openfigi               openfigi;override_ticker
755111507              RTN              RTN         1047122         3812         BusEq   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
78486Q101             SIVB             SIVB          719739         6022         Money   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
81181C104             SGEN             SGEN         1060736         2836          Hlth   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
812578102             SGEN             SGEN         1060736         2836          Hlth   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
848637104             SPLK             SPLK         1353283         7372         BusEq   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
867914103              STI              STI          750556         6021         Money   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
86800U104             SMCI             SMCI         1375365         3571         BusEq   no_match  mapped  openfigi               openfigi;override_ticker
90184L102             TWTR             TWTR         1418091         7370         BusEq   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
904767704               UL               UL          217410         2840         Chems   no_match  mapped  openfigi               openfigi;override_ticker
913017109              RTX              RTX          101829         3724         Manuf   no_match  mapped  openfigi               openfigi;override_ticker
928563402              VMW              VMW         1124610         7372         BusEq   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
94946T106              WCG              WCG         1279363         6324         Money   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
983919101             XLNX             XLNX          743988         3674         BusEq   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
98936J101              ZEN              ZEN         1463172         7374         BusEq   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
BMG475671050          INFO             INFO         1598014         7370         BusEq   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
CH0102993182           TEL              TEL         1385157         5065         Shops   no_match  mapped  openfigi               openfigi;override_ticker
G06242104             TEAM             TEAM         1650372         7372         BusEq   no_match  mapped  openfigi               openfigi;override_ticker
G29018101              DLO              DLO         1846832         7389         Other   no_match  mapped  openfigi               openfigi;override_ticker
G4388N106             HELE             HELE          916789         3634         Durbl   no_match  mapped  openfigi               openfigi;override_ticker
G46188101             HZNP             HZNP         1492426         2834          Hlth   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
G5494J103              LIN              LIN         1707925         2810         Chems   no_match  mapped  openfigi               openfigi;override_ticker
G5960L103              MDT              MDT         1613103         3845          Hlth   no_match  mapped  openfigi               openfigi;override_ticker
GB00BZ09BD16          TEAM             TEAM         1650372         7372         BusEq   no_match  mapped  openfigi               openfigi;override_ticker
H82027105             SOPH             SOPH         1840706         7374         BusEq   no_match  mapped  openfigi               openfigi;override_ticker
IE00BQPVQZ61          HZNP             HZNP         1492426         2834          Hlth   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
IE00BY9D5467           AGN              AGN         1578845         2834          Hlth   no_match  mapped  openfigi  openfigi;override_ticker;override_cik
IE00BZ12WP82           LIN              LIN         1707925         2810         Chems   no_match  mapped  openfigi               openfigi;override_ticker
JE00B783TY65          APTV             APTV         1521332         3714         Durbl   no_match  mapped  openfigi               openfigi;override_ticker
M22465104             CHKP             CHKP         1015922         7372         BusEq   no_match  mapped  openfigi               openfigi;override_ticker
M7S64H106             MNDY             MNDY         1845338         7372         BusEq   no_match  mapped  openfigi               openfigi;override_ticker
N07059210             ASML             ASML          937966         3559         Manuf   no_match  mapped  openfigi               openfigi;override_ticker
Y4600W108             KARO             KARO         1828102         7372         BusEq   no_match  mapped  openfigi               openfigi;override_ticker
```

### 3.1 SECURITY_MAP rows changed by step 3.0, against the sec_ids the overrides name

```
   n_rows_before  n_rows_after  n_changed  n_named changed_not_named named_not_changed
0           1622          1622         62       62                                    
```

### D.1 data/raw/sec/cik_override_check.csv in full

```
          sec_id      cik                    submissions_name                    note_name match
0      03662Q105  1013462                           ANSYS INC                        ANSYS  True
1      25401T108  1679688           DigitalBridge Group, Inc.                DigitalBridge  True
2      19626G108  1679688           DigitalBridge Group, Inc.                DigitalBridge  True
3      74165N105   884713               Primo Water Corp /CN/                  Primo Water  True
4      74167P108   884713               Primo Water Corp /CN/                  Primo Water  True
5   IE00BY9D5467  1578845                        Allergan plc                     Allergan  True
6      755111507  1047122                        RAYTHEON CO/                     Raytheon  True
7      00507V109   718877           Activision Blizzard, Inc.          Activision Blizzard  True
8      90184L102  1418091                       TWITTER, INC.                      Twitter  True
9      983919101   743988                          XILINX INC                       Xilinx  True
10     848637104  1353283                          SPLUNK INC                       Splunk  True
11     285512109   712515                ELECTRONIC ARTS INC.              Electronic Arts  True
12     723787107  1038357        PIONEER NATURAL RESOURCES CO    Pioneer Natural Resources  True
13     928563402  1124610                          VMWARE LLC                       VMware  True
14     156782104   804753                         CERNER Corp                       Cerner  True
15     812578102  1060736                         Seagen Inc.                       Seagen  True
16     81181C104  1060736                         Seagen Inc.                       Seagen  True
17     G46188101  1492426  Horizon Therapeutics Public Ltd Co         Horizon Therapeutics  True
18  IE00BQPVQZ61  1492426  Horizon Therapeutics Public Ltd Co         Horizon Therapeutics  True
19  BMG475671050  1598014                     IHS Markit Ltd.                   IHS Markit  True
20     22266L106  1385867                  Coupa Software Inc               Coupa Software  True
21     867914103   750556                  SUNTRUST BANKS INC               SunTrust Banks  True
22     053484101   915912           AVALONBAY COMMUNITIES INC        AvalonBay Communities  True
23     177376100   877890                  CITRIX SYSTEMS INC               Citrix Systems  True
24     254709108  1393612         Discover Financial Services  Discover Financial Services  True
25     78486Q101   719739                 SVB FINANCIAL GROUP          SVB Financial Group  True
26     94946T106  1279363         WELLCARE HEALTH PLANS, INC.        WellCare Health Plans  True
27     30063P105  1124140                 EXACT SCIENCES CORP               Exact Sciences  True
28     98936J101  1463172                       Zendesk, Inc.                      Zendesk  True
```

### D.2 the 62 ticker overrides: map_status, ff12, and whether yf_ticker is priced at the first q_start held

```
          sec_id ticker yf_ticker      cik map_status   ff12 first_period_held  entity first_q_start  priced_at_first_q_start first_price_date
0      38259P508  GOOGL     GOOGL  1652044     mapped  BusEq        2021-06-30  jensen    2021-06-30                     True       2015-12-01
1      913017109    RTX       RTX   101829     mapped  Manuf        2019-09-30     ivv    2019-09-30                     True       2015-12-01
2      112585104     BN        BN  1001085     mapped  Money        2019-09-30    akre    2019-09-30                     True       2015-12-01
3      03662Q105   ANSS      ANSS  1013462     mapped  BusEq        2019-09-30     ivv    2019-09-30                    False                 
4      30231G102    XOM       XOM  2115436     mapped  Enrgy        2019-09-30     ivv    2019-09-30                     True       2015-12-01
5      25401T108   DBRG      DBRG  1679688     mapped  Money        2021-06-30    akre    2021-06-30                    False                 
6      19626G108   DBRG      DBRG  1679688     mapped  Money        2019-09-30    akre    2019-09-30                    False                 
7   IE00BZ12WP82    LIN       LIN  1707925     mapped  Chems        2019-09-30     ivv    2019-09-30                     True       2015-12-01
8      G5494J103    LIN       LIN  1707925     mapped  Chems        2019-09-30  jensen    2019-09-30                     True       2015-12-01
9      512807108   LRCX      LRCX   707549     mapped  Manuf        2019-09-30     ivv    2019-09-30                     True       2015-12-01
10     H82027105   SOPH      SOPH  1840706     mapped  BusEq        2024-03-31    akre    2024-03-28                     True       2021-07-23
11     74165N105   PRMW      PRMW   884713     mapped  NoDur        2019-09-30    akre    2019-09-30                    False                 
12     74167P108   PRMW      PRMW   884713     mapped  NoDur        2020-03-31    akre    2020-03-31                    False                 
13     369604103     GE        GE    40545     mapped  Manuf        2019-09-30     ivv    2019-09-30                     True       2015-12-01
14     040413106   ANET      ANET  1596532     mapped  BusEq        2019-09-30     ivv    2019-09-30                     True       2015-12-01
15     09247X101    BLK       BLK  2012383     mapped  Money        2019-09-30     ivv    2019-09-30                     True       2015-12-01
16  IE00BY9D5467    AGN       AGN  1578845     mapped   Hlth        2019-09-30     ivv    2019-09-30                    False                 
17     N07059210   ASML      ASML   937966     mapped  Manuf        2021-06-30   polen    2021-06-30                     True       2015-12-01
18  GB00BZ09BD16   TEAM      TEAM  1650372     mapped  BusEq        2019-09-30     iwf    2019-09-30                     True       2015-12-09
19     G06242104   TEAM      TEAM  1650372     mapped  BusEq        2022-09-30     iwf    2022-09-30                     True       2015-12-09
20     755111507    RTN       RTN  1047122     mapped  BusEq        2019-09-30     ivv    2019-09-30                    False                 
21     G5960L103    MDT       MDT  1613103     mapped   Hlth        2019-09-30  jensen    2019-09-30                     True       2015-12-01
22     00507V109   ATVI      ATVI   718877     mapped  BusEq        2019-09-30     ivv    2019-09-30                    False                 
23     90184L102   TWTR      TWTR  1418091     mapped  BusEq        2019-09-30     ivv    2019-09-30                    False                 
24     983919101   XLNX      XLNX   743988     mapped  BusEq        2019-09-30     ivv    2019-09-30                    False                 
25     848637104   SPLK      SPLK  1353283     mapped  BusEq        2019-09-30     iwf    2019-09-30                    False                 
26     26614N102     DD        DD  1666700     mapped  Chems        2019-09-30     ivv    2019-09-30                     True       2015-12-01
27     285512109     EA        EA   712515     mapped  BusEq        2019-09-30     ivv    2019-09-30                    False                 
28     G4388N106   HELE      HELE   916789     mapped  Durbl        2020-03-31   polen    2020-03-31                     True       2015-12-01
29     Y4600W108   KARO      KARO  1828102     mapped  BusEq        2021-06-30   polen    2021-06-30                     True       2021-04-01
30     339041105   CPAY      CPAY  1175454     mapped  Other        2019-09-30     ivv    2019-09-30                     True       2015-12-01
31     723787107    PXD       PXD  1038357     mapped  Enrgy        2019-09-30     ivv    2019-09-30                    False                 
32     928563402    VMW       VMW  1124610     mapped  BusEq        2019-09-30     iwf    2019-09-30                    False                 
33     44919P508   MTCH      MTCH   891103     mapped  BusEq        2019-09-30     iwf    2019-09-30                     True       2015-12-01
34     054937107    TFC       TFC    92230     mapped  Money        2019-09-30     ivv    2019-09-30                     True       2015-12-01
35     156782104   CERN      CERN   804753     mapped  BusEq        2019-09-30     ivv    2019-09-30                    False                 
36     812578102   SGEN      SGEN  1060736     mapped   Hlth        2019-09-30     iwf    2019-09-30                    False                 
37     81181C104   SGEN      SGEN  1060736     mapped   Hlth        2020-12-31     iwf    2020-12-31                    False                 
38     G46188101   HZNP      HZNP  1492426     mapped   Hlth        2022-09-30     iwf    2022-09-30                    False                 
39  IE00BQPVQZ61   HZNP      HZNP  1492426     mapped   Hlth        2019-09-30     iwf    2019-09-30                    False                 
40  BMG475671050   INFO      INFO  1598014     mapped  BusEq        2019-09-30     ivv    2019-09-30                    False       2024-10-10
41  CH0102993182    TEL       TEL  1385157     mapped  Shops        2019-09-30     ivv    2019-09-30                     True       2015-12-01
42     682680103    OKE       OKE  1039684     mapped  Utils        2019-09-30     ivv    2019-09-30                     True       2015-12-01
43     22266L106   COUP      COUP  1385867     mapped  BusEq        2019-09-30     iwf    2019-09-30                    False                 
44     867914103    STI       STI   750556     mapped  Money        2019-09-30     ivv    2019-09-30                    False       2022-05-02
45     904767704     UL        UL   217410     mapped  Chems        2019-09-30   polen    2019-09-30                     True       2015-12-01
46     053484101    AVB       AVB   915912     mapped  Money        2019-09-30     ivv    2019-09-30                    False                 
47  JE00B783TY65   APTV      APTV  1521332     mapped  Durbl        2019-09-30     ivv    2019-09-30                     True       2015-12-01
48     86800U104   SMCI      SMCI  1375365     mapped  BusEq        2024-03-31     ivv    2024-03-28                     True       2015-12-01
49     177376100   CTXS      CTXS   877890     mapped  BusEq        2019-09-30     ivv    2019-09-30                    False                 
50     254709108    DFS       DFS  1393612     mapped  Money        2019-09-30     ivv    2019-09-30                    False                 
51     M22465104   CHKP      CHKP  1015922     mapped  BusEq        2019-09-30   polen    2019-09-30                     True       2015-12-01
52     78486Q101   SIVB      SIVB   719739     mapped  Money        2019-09-30     ivv    2019-09-30                    False                 
53     94946T106    WCG       WCG  1279363     mapped  Money        2019-09-30     ivv    2019-09-30                    False                 
54     G29018101    DLO       DLO  1846832     mapped  Other        2022-12-31   polen    2022-12-30                     True       2021-06-03
55     M7S64H106   MNDY      MNDY  1845338     mapped  BusEq        2024-12-31   polen    2024-12-31                     True       2021-06-10
56     30063P105   EXAS      EXAS  1124140     mapped   Hlth        2019-09-30     iwf    2019-09-30                    False                 
57     98936J101    ZEN       ZEN  1463172     mapped  BusEq        2019-09-30     iwf    2019-09-30                    False                 
58     531229854  FWONK     FWONK  1560385     mapped  Telcm        2022-06-30     iwf    2022-06-30                     True       2015-12-01
59     531229870  FWONA     FWONA  1560385     mapped  Telcm        2022-06-30     iwf    2022-06-30                     True       2015-12-01
60     637071101    NOV       NOV  1021860     mapped  Manuf        2019-09-30     ivv    2019-09-30                     True       2015-12-01
61     74838J101   QDEL      QDEL  1906324     mapped   Hlth        2020-06-30     iwf    2020-06-30                     True       2015-12-01
```

### D.2 counts

```
  map_status  priced_at_first_q_start   n
0     mapped                    False  29
1     mapped                     True  33
```

### 3.0 price columns added to adjclose.parquet

```
   yf_ticker       first        last     n
0       ASML  2015-12-01  2026-09-30  2723
1       CHKP  2015-12-01  2026-09-30  2723
2        DLO  2021-06-03  2026-09-30  1338
3       HELE  2015-12-01  2026-09-30  2723
4       INFO  2024-10-10  2026-09-30   494
5       KARO  2021-04-01  2026-09-30  1381
6       MNDY  2021-06-10  2026-09-30  1333
7        OKE  2015-12-01  2026-09-30  2723
8       QDEL  2015-12-01  2026-09-30  2723
9       SOPH  2021-07-23  2026-09-30  1303
10       STI  2022-05-02  2026-09-30  1108
11        UL  2015-12-01  2026-09-30  2723
12       XOM  2015-12-01  2026-09-30  2723
```

### 3.0 missing.csv in full after the pull (rows new since session 2c marked)

```
   yf_ticker                        sec_ids    new
0   9990302D                      037411105  False
1        AGN                   IE00BY9D5467   True
2       ALXN                      015351109  False
3       AMED                      023436108  False
4       ANSS                      03662Q105   True
5        ATH                   BMG0684D1074  False
6       ATVI                      00507V109   True
7        AVB                      053484101   True
8       AZEK                      05478C105  False
9        CDK                      12508E101  False
10      CELG                      151020104  False
11      CERN                      156782104   True
12      CIVI                      17888H103  False
13      CLGX                      21871D103  False
14       CMA                      200340107  False
15       CMD                      138098108  False
16      COUP                      22266L106   True
17      CTRA                      127097103  False
18      CTXS                      177376100   True
19      CVAC                   NL0015436031  False
20      DBRG  19626G108;25401T108;25401T603  False
21       DFS                      254709108   True
22       DNB                      26484T106  False
23      DNKN                      265504100  False
24        EA                      285512109   True
25      EXAS                      30063P105   True
26      FLIR                      302445101  False
27       HES                      42809H107  False
28       HRC                      431475102  False
29      HZNP         G46188101;IE00BQPVQZ61   True
30      IMMU                      452907108  False
31      IPHI                      45772F107  False
32      LVGO                      539183103  False
33      MDLA                      584021109  False
34      MXIM                      57772K101  False
35       MYL                   NL0011031208  False
36      PFPT                      743424103  False
37      PRAH                      69354M108  False
38      PRMW            74165N105;74167P108   True
39       PXD                      723787107   True
40        RP                      75606N109  False
41       RTN                      755111507   True
42      SGEN            81181C104;812578102   True
43      SIVB                      78486Q101   True
44      SPLK                      848637104   True
45       STL                      85917A100  False
46      TWTR                      90184L102   True
47      VIAB                      92553P201  False
48       VMW                      928563402   True
49       WBA                      931427108  False
50       WCG                      94946T106   True
51      WORK                      83088V102  False
52      XLNX                      983919101   True
53      XLRN                      00434H108  False
54       ZEN                      98936J101   True
```

### D.3 unmapped_weight and unpriced_weight per entity, mean and max over 28 books, before and after the overrides

```
   entity unmapped before, mean unmapped before, max unmapped after, mean unmapped after, max unpriced before, mean unpriced before, max unpriced after, mean unpriced after, max
0    akre                 2.47%                7.00%                0.00%               0.03%                 0.17%                0.72%                0.78%               1.93%
1  jensen                 0.89%                6.99%                0.07%               0.10%                 0.01%                0.04%                0.01%               0.04%
2   polen                 0.43%                0.80%                0.06%               0.29%                 0.00%                0.00%                0.00%               0.00%
3     ivv                 3.52%                6.94%                0.62%               1.48%                 0.27%                0.88%                1.03%               2.69%
4     iwf                 1.87%                4.25%                0.57%               1.48%                 0.22%                1.01%                0.94%               3.04%
```

### D.3 books with unmapped_weight + unpriced_weight above 2% after the overrides

```
    entity period_date  unmapped_weight  unpriced_weight      both
84     ivv  2019-09-30         0.014817         0.026867  0.041684
85     ivv  2019-12-31         0.014029         0.022275  0.036303
86     ivv  2020-03-31         0.010862         0.020541  0.031404
87     ivv  2020-06-30         0.010609         0.016311  0.026920
88     ivv  2020-09-30         0.010964         0.015456  0.026419
89     ivv  2020-12-31         0.010840         0.016123  0.026963
90     ivv  2021-03-31         0.010804         0.016440  0.027243
91     ivv  2021-06-30         0.009317         0.016482  0.025799
92     ivv  2021-09-30         0.009166         0.014084  0.023250
93     ivv  2021-12-31         0.007557         0.013846  0.021403
112    iwf  2019-09-30         0.014844         0.030367  0.045211
113    iwf  2019-12-31         0.012891         0.024860  0.037752
114    iwf  2020-03-31         0.010131         0.022357  0.032489
115    iwf  2020-06-30         0.010380         0.020878  0.031257
116    iwf  2020-09-30         0.010594         0.020505  0.031099
117    iwf  2020-12-31         0.011139         0.019401  0.030540
118    iwf  2021-03-31         0.010991         0.018545  0.029535
119    iwf  2021-06-30         0.010782         0.013996  0.024779
```

### 3.0 outputs/tables/unmapped_top.csv after the overrides (all rows)

```
          sec_id id_type                                   name              max_weight entity_of_max                                                                                                                                                                                                                                                                                                   periods
0      44891N109   cusip                    IAC/InterActiveCorp  0.00087413096564512808           iwf                                                                                                                                                                                                                                                                          2020-09-30;2020-12-31;2021-03-31
1      124857202   cusip                               CBS Corp  0.00086512604766223844           iwf                                                                                                                                                                                                                                                                                                2019-09-30
2      92556H206   cusip                          ViacomCBS Inc  0.00083799230434387635           ivv                                              2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30
3      92220P105   cusip             Varian Medical Systems Inc  0.00083503610077559245           iwf                                                                                                                                                                                                                              2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31
4      87236Y108   cusip             TD Ameritrade Holding Corp  0.00080049024847442295           iwf                                                                                                                                                                                                                                                                          2019-09-30;2019-12-31;2020-03-31
5      09215C105   cusip                       Black Knight Inc  0.00079346334934550305           iwf                                                                                                                                                                                  2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31
6      436440101   cusip                            Hologic Inc  0.00077929717108874059           iwf  2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31
7      003654100   cusip                            ABIOMED Inc  0.00076895565238113911           iwf                                                                                                                                                            2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30
8   PA1436583006    isin                          Carnival Corp  0.00076018117931299985           ivv                                                                                                                                                                                                        2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31
9      574795100   cusip                            Masimo Corp   0.0007490598045958222           iwf  2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31
10     50540R409   cusip    Laboratory Corp of America Holdings  0.00074436290499907745           ivv                                                                                          2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31
11     05338G106   cusip                            Avalara Inc    0.000730682243525342           iwf                                                                                                                                                            2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30
12     M6191J100   cusip                              JFROG LTD  0.00072884579579398647         polen                                                                                                                                                                                                                                                                          2025-12-31;2026-03-31;2026-06-30
13     03768E105   cusip           Apollo Global Management Inc  0.00072013065293996743           iwf                                                                                                                                                                                                                              2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31
14     485170302   cusip                   Kansas City Southern  0.00071523480622831678           ivv                                                                                                                                                                                                        2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30
15     40414L109   cusip                                HCP Inc  0.00070813002494115804           ivv                                                                                                                                                                                                                                                                                                2019-09-30
16     143658300   cusip                          Carnival Corp  0.00070800814844034659           ivv                                                                                                     2019-09-30;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31
17     487836108   cusip                             Kellogg Co  0.00069426553788875373           ivv                        2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30
18     264411505   cusip                       Duke Realty Corp  0.00066209863883629383           ivv                                                                                                                                                            2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30
19     20605P101   cusip                   Concho Resources Inc  0.00065784990603483012           ivv                                                                                                                                                                                                                                         2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31
20     886547108   cusip                           Tiffany & Co  0.00065511015924078753           ivv                                                                                                                                                                                                                                         2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31
21     216648402   cusip                     Cooper Cos Inc/The  0.00063612856851676179           ivv                                                                                                     2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31
22     148806102   cusip                           Catalent Inc  0.00062276101533503933           ivv                                                                                                                2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30
23     045327103   cusip                   Aspen Technology Inc  0.00061257450341759977           iwf                                                                                                                                                                                  2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31
24     02156B103   cusip                            Alteryx Inc  0.00059068361802498887           iwf                                                                                                     2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31
25     98919V105   cusip                Zayo Group Holdings Inc  0.00055451029970810103           iwf                                                                                                                                                                                                                                                                                     2019-09-30;2019-12-31
26     848574109   cusip        Spirit AeroSystems Holdings Inc   0.0005529233590755194           iwf                                                                    2019-09-30;2019-12-31;2020-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30
27     871503108   cusip                          Symantec Corp  0.00054299300891190319           ivv                                                                                                                                                                                                                                                                                                2019-09-30
28     565849106   cusip                     Marathon Oil Corp.  0.00053507983019642641           ivv                                                                    2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30
29  IE00B58JVZ52    isin                 Seagate Technology PLC  0.00052860413631396804           ivv                                                                                                                                                                                                                              2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31
30     46116X101   cusip           Intra-Cellular Therapies Inc  0.00052617685617513681           iwf                                                                                                                                                                                                                                                                          2024-09-30;2024-12-31;2025-03-31
31     03272L108   cusip                            Anaplan Inc  0.00051938746549230644           iwf                                                                                                                                                                                  2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31
32     78667J108   cusip                  Sage Therapeutics Inc  0.00051146011805132928           iwf                                                                                                                                                                                                                              2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31
33     156700106   cusip                        CenturyLink Inc  0.00049821722526088874           ivv                                                                                                                                                                                                                                         2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31
34     82489T104   cusip                SHOCKWAVE MEDICAL, INC.  0.00047650073448085936           iwf                                                                                                                                                                                                                                                               2023-06-30;2023-09-30;2023-12-31;2024-03-31
35     98986T108   cusip                              Zynga Inc  0.00047548663313303532           iwf                                                                                                                                                                                  2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31
36     81211K100   cusip                        Sealed Air Corp  0.00047360452586572778           iwf                                              2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31
37     15677J108   cusip               Ceridian HCM Holding Inc  0.00047204214375174639           iwf                        2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31
38     501797104   cusip                           L Brands Inc  0.00046472946090434463           ivv                                                                                                                                                                                                                   2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30
39     03965L100   cusip                            Arconic Inc  0.00045389815336984628           ivv                                                                                                                                                                                                                                                                          2019-09-30;2019-12-31;2020-03-31
40  BMG169621056    isin                             Bunge Ltd.  0.00045379172128911485           ivv                                                                                                                                                                                                                                                                          2023-03-31;2023-06-30;2023-09-30
41     655044105   cusip                       Noble Energy Inc  0.00044929678299075092           ivv                                                                                                                                                                                                                                                    2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30
42     92927K102   cusip                     WABCO Holdings Inc   0.0004376764405585269           iwf                                                                                                                                                                                                                                                                          2019-09-30;2019-12-31;2020-03-31
43     269246401   cusip                 E*TRADE Financial Corp  0.00042903274074102677           ivv                                                                                                                                                                                                                                                    2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30
44     83200N103   cusip                         Smartsheet Inc  0.00042564309952330476           iwf                                                         2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31
45     48576A100   cusip                Karuna Therapeutics Inc  0.00042421393290915525           iwf                                                                                                                                                                                                                                                                          2023-06-30;2023-09-30;2023-12-31
46     460690100   cusip  Interpublic Group of Cos., Inc. (The)   0.0004213068431310186           ivv                        2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30
47     92532W103   cusip                   Versum Materials Inc  0.00042095676719620598           iwf                                                                                                                                                                                                                                                                                                2019-09-30
48     96145D105   cusip                            WestRock Co   0.0004186220768394467           ivv                                                                               2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30
49     03753U106   cusip          APELLIS PHARMACEUTICALS, INC.  0.00041826203042764529           iwf                                                                                                                                                                       2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31
50     58471A105   cusip                 Medidata Solutions Inc  0.00041326110065290924           iwf                                                                                                                                                                                                                                                                                                2019-09-30
51     08862E109   cusip                        Beyond Meat Inc   0.0004127291874929441           iwf                                                                                                                                                                                                                   2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31
52     G6095L109   cusip                              APTIV PLC   0.0003949565312449891           iwf                                                                                                                                                                                                                                                                          2022-09-30;2022-12-31;2023-03-31
53     530307305   cusip                 Liberty Broadband Corp  0.00038966184471417195           iwf                                                                                                                           2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31
54     313747206   cusip        Federal Realty Investment Trust  0.00038588224285382601           ivv                                                                                                                                                                                             2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31
55     25470F302   cusip                          Discovery Inc  0.00038211176706713266           ivv                                                                                                                                                                                  2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31
56     29109X106   cusip                 ASPEN TECHNOLOGY, INC.  0.00037932515839728961           iwf                                                                                                                                                                                             2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30
57     449253103   cusip                                IAA Inc   0.0003781277772444336           iwf                                                                                                                                                 2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31
58     400110102   cusip                            GrubHub Inc  0.00037299274391984488           iwf                                                                                                                                                                                                                              2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31
59     487836116   cusip                              Kellanova  0.00037140685303776408        jensen                                                                                                                                                                                                                                                                                                2023-12-31
```

### 3.0 outputs/tables/unpriced_top.csv after the overrides (all rows)

```
          sec_id yf_ticker                               name             max_weight entity_of_max                                                                                                                                                                                                                                                                                                              periods
0      03662Q105      ANSS                          ANSYS INC   0.014990865878743822          akre                                              2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30
1      25401T603      DBRG            DIGITALBRIDGE GROUP INC  0.0071786368817792993          akre                                                                                                                                                                                             2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31
2      25401T108      DBRG            DIGITALBRIDGE GROUP INC  0.0064097319194375939          akre                                                                                                                                                                                                                                                               2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30
3      151020104      CELG                       Celgene Corp  0.0050111311371948261           iwf                                                                                                                                                                                                                                                                                                           2019-09-30
4      19626G108      DBRG                 COLONY CAP INC NEW  0.0046349892355709733          akre                                                                                                                                                                                                                                         2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31
5      74165N105      PRMW                     PRIMO WTR CORP  0.0037007831867074247          akre                                                                                                                                                                                                                                                                                                2019-09-30;2019-12-31
6   IE00BY9D5467       AGN                       Allergan PLC  0.0027137046650727898           ivv                                                                                                                                                                                                                                                                                     2019-09-30;2019-12-31;2020-03-31
7      755111507       RTN                        Raytheon Co  0.0024940986451726758           iwf                                                                                                                                                                                                                                                                                     2019-09-30;2019-12-31;2020-03-31
8      00507V109      ATVI            Activision Blizzard Inc  0.0022824099847269549           ivv                                                                                                                           2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30
9      90184L102      TWTR                        Twitter Inc  0.0022354721179680139           iwf                                                                                                                                                                       2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30
10     983919101      XLNX                         Xilinx Inc  0.0021865392745658726           iwf                                                                                                                                                                                                        2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31
11     848637104      SPLK                         Splunk Inc  0.0021575729902274235           iwf                                                                                                                2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31
12     285512109        EA                Electronic Arts Inc  0.0019811053373857751           iwf  2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30;2025-09-30;2025-12-31;2026-03-31;2026-06-30
13     42809H107       HES                   HESS CORPORATION   0.001825407708934378           iwf                                              2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30
14     723787107       PXD  PIONEER NATURAL RESOURCES COMPANY  0.0017437215595318715           iwf                                                                                                     2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31
15     928563402       VMW                       VMWARE, INC.  0.0017104344832561313           iwf                                                                                                                           2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30
16     931427108       WBA       Walgreens Boots Alliance Inc  0.0016961745832553099           ivv                                              2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30;2023-12-31;2024-03-31;2024-06-30;2024-09-30;2024-12-31;2025-03-31;2025-06-30
17     156782104      CERN                        Cerner Corp  0.0015447921569672095           iwf                                                                                                                                                                                             2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30;2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31
18     812578102      SGEN               Seattle Genetics Inc    0.00145059621221608           iwf                                                                                                                                                                                                                                                               2019-09-30;2019-12-31;2020-03-31;2020-06-30;2020-09-30
19     81181C104      SGEN                        SEAGEN INC.  0.0014198585738567793           iwf                                                                                                                                                                                  2020-12-31;2021-03-31;2021-06-30;2021-09-30;2021-12-31;2022-03-31;2022-06-30;2022-09-30;2022-12-31;2023-03-31;2023-06-30;2023-09-30
```

### D.4 large_moves.csv: fund position-quarters with daily |return| > 25% and weight > 0.5% (file has 727 rows)

```
    entity   t     sec_id yf_ticker        date  daily_return    weight
3     akre  26  12510Q100       CCC  2026-02-25      0.252964  0.021649
4     akre  28  303250104      FICO  2026-09-29     -0.265219  0.084651
554  polen   4  79466L302       CRM  2020-08-26      0.260449  0.038015
555  polen   5  016255101      ALGN  2020-10-22      0.349662  0.022745
565  polen  10  30303M102      META  2022-02-03     -0.263901  0.059000
572  polen  11  64110L106      NFLX  2022-04-20     -0.351166  0.036609
583  polen  14  016255101      ALGN  2023-02-02      0.273776  0.010316
623  polen  24  45168D104      IDXX  2025-08-04      0.274938  0.019676
624  polen  24  366651107        IT  2025-08-05     -0.275549  0.009666
631  polen  24  68389X105      ORCL  2025-09-10      0.359488  0.080398
```

### D.4 large_moves.csv: IVV and IWF position-quarters with weight > 1%

```
    entity   t     sec_id yf_ticker        date  daily_return    weight
93     ivv  10  30303M102      META  2022-02-03     -0.263901  0.019720
244    iwf   4  79466L302       CRM  2020-08-26      0.260449  0.010287
290    iwf  10  30303M102      META  2022-02-03     -0.263901  0.033507
484    iwf  24  68389X105      ORCL  2025-09-10      0.359488  0.012295
```

### 3.2 outputs/tables/book_quarterly.csv in full

```
     entity   t  book_return  unmapped_weight  unpriced_weight  delisted_weight
0      akre   1     0.047890         0.000054         0.003707                0
1      akre   2    -0.147049         0.000000         0.007186                0
2      akre   3     0.245653         0.000000         0.012230                0
3      akre   4     0.063595         0.000000         0.014800                0
4      akre   5     0.054601         0.000000         0.016689                0
5      akre   6     0.034662         0.000000         0.018502                0
6      akre   7     0.104614         0.000000         0.018733                0
7      akre   8     0.004667         0.000288         0.018144                0
8      akre   9     0.077700         0.000000         0.016687                0
9      akre  10    -0.102094         0.000000         0.019270                0
10     akre  11    -0.126510         0.000000         0.018643                0
11     akre  12    -0.085915         0.000000         0.006410                0
12     akre  13     0.105203         0.000000         0.005108                0
13     akre  14     0.040498         0.000000         0.004941                0
14     akre  15     0.089714         0.000000         0.005423                0
15     akre  16    -0.038365         0.000000         0.006156                0
16     akre  17     0.175433         0.000000         0.007179                0
17     akre  18     0.076993         0.000000         0.006497                0
18     akre  19    -0.027053         0.000000         0.006550                0
19     akre  20     0.128128         0.000000         0.004391                0
20     akre  21     0.013124         0.000000         0.001546                0
21     akre  22     0.020716         0.000000         0.000746                0
22     akre  23     0.042588         0.000000         0.000140                0
23     akre  24     0.005621         0.000000         0.000000                0
24     akre  25    -0.018694         0.000000         0.000000                0
25     akre  26    -0.170979         0.000000         0.000000                0
26     akre  27     0.001572         0.000000         0.000000                0
27     akre  28    -0.008899         0.000000         0.000000                0
28   jensen   1     0.085234         0.000357         0.000073                0
29   jensen   2    -0.178632         0.000433         0.000077                0
30   jensen   3     0.178151         0.000395         0.000187                0
31   jensen   4     0.100136         0.000419         0.000202                0
32   jensen   5     0.118022         0.000330         0.000251                0
33   jensen   6     0.028329         0.000457         0.000249                0
34   jensen   7     0.080501         0.000564         0.000358                0
35   jensen   8     0.021901         0.000608         0.000420                0
36   jensen   9     0.152094         0.000783         0.000000                0
37   jensen  10    -0.075548         0.000786         0.000000                0
38   jensen  11    -0.125448         0.000895         0.000000                0
39   jensen  12    -0.051749         0.000999         0.000000                0
40   jensen  13     0.096507         0.000942         0.000000                0
41   jensen  14     0.047807         0.000969         0.000000                0
42   jensen  15     0.061948         0.001034         0.000000                0
43   jensen  16    -0.037225         0.001008         0.000000                0
44   jensen  17     0.100828         0.000926         0.000000                0
45   jensen  18     0.050739         0.000935         0.000000                0
46   jensen  19     0.012415         0.000979         0.000000                0
47   jensen  20     0.069949         0.000474         0.000000                0
48   jensen  21    -0.022663         0.000095         0.000000                0
49   jensen  22    -0.014160         0.000415         0.000000                0
50   jensen  23     0.047604         0.000455         0.000000                0
51   jensen  24     0.032337         0.000551         0.000000                0
52   jensen  25    -0.004894         0.000576         0.000000                0
53   jensen  26    -0.100097         0.000762         0.000000                0
54   jensen  27     0.112393         0.000570         0.000000                0
55   jensen  28     0.026403         0.000507         0.000000                0
56    polen   1     0.108928         0.000135         0.000042                0
57    polen   2    -0.132374         0.000113         0.000000                0
58    polen   3     0.288204         0.000177         0.000000                0
59    polen   4     0.105408         0.000271         0.000000                0
60    polen   5     0.102433         0.000303         0.000000                0
61    polen   6     0.020711         0.000292         0.000000                0
62    polen   7     0.133445         0.000654         0.000000                0
63    polen   8     0.021064         0.000598         0.000000                0
64    polen   9     0.054932         0.000795         0.000000                0
65    polen  10    -0.137879         0.000812         0.000000                0
66    polen  11    -0.233761         0.000889         0.000000                0
67    polen  12    -0.057588         0.000761         0.000000                0
68    polen  13     0.016889         0.000697         0.000000                0
69    polen  14     0.141916         0.000712         0.000000                0
70    polen  15     0.105697         0.000433         0.000000                0
71    polen  16    -0.032339         0.000324         0.000000                0
72    polen  17     0.151653         0.000237         0.000000                0
73    polen  18     0.085048         0.000200         0.000000                0
74    polen  19     0.002588         0.000313         0.000000                0
75    polen  20     0.034493         0.000341         0.000000                0
76    polen  21     0.048948         0.000432         0.000000                0
77    polen  22    -0.063893         0.000171         0.000000                0
78    polen  23     0.091665         0.000161         0.000000                0
79    polen  24     0.036568         0.000833         0.000000                0
80    polen  25    -0.015879         0.000743         0.000000                0
81    polen  26    -0.157609         0.000698         0.000000                0
82    polen  27     0.065859         0.001295         0.000000                0
83    polen  28     0.039180         0.002927         0.000000                0
84      ivv   1     0.090926         0.014817         0.026867                0
85      ivv   2    -0.192722         0.014029         0.022275                0
86      ivv   3     0.204703         0.010862         0.020541                0
87      ivv   4     0.090227         0.010609         0.016311                0
88      ivv   5     0.119313         0.010964         0.015456                0
89      ivv   6     0.060469         0.010840         0.016123                0
90      ivv   7     0.085887         0.010804         0.016440                0
91      ivv   8     0.005668         0.009317         0.016482                0
92      ivv   9     0.112323         0.009166         0.014084                0
93      ivv  10    -0.047220         0.007557         0.013846                0
94      ivv  11    -0.160697         0.007645         0.012178                0
95      ivv  12    -0.048632         0.006882         0.011995                0
96      ivv  13     0.075578         0.006476         0.011962                0
97      ivv  14     0.076199         0.005256         0.010155                0
98      ivv  15     0.088410         0.005597         0.008918                0
99      ivv  16    -0.032534         0.005096         0.008353                0
100     ivv  17     0.117148         0.004770         0.008521                0
101     ivv  18     0.106294         0.004030         0.006426                0
102     ivv  19     0.043352         0.003366         0.006095                0
103     ivv  20     0.059053         0.002761         0.004218                0
104     ivv  21     0.024138         0.002583         0.003926                0
105     ivv  22    -0.042805         0.002106         0.004044                0
106     ivv  23     0.109352         0.001998         0.004390                0
107     ivv  24     0.081040         0.001987         0.003091                0
108     ivv  25     0.026677         0.001572         0.001594                0
109     ivv  26    -0.043559         0.001040         0.001567                0
110     ivv  27     0.152265         0.000834         0.001712                0
111     ivv  28     0.022748         0.000000         0.001123                0
112     iwf   1     0.108057         0.014844         0.030367                0
113     iwf   2    -0.137663         0.012891         0.024860                0
114     iwf   3     0.278522         0.010131         0.022357                0
115     iwf   4     0.133703         0.010380         0.020878                0
116     iwf   5     0.112985         0.010594         0.020505                0
117     iwf   6     0.011434         0.011139         0.019401                0
118     iwf   7     0.120900         0.010991         0.018545                0
119     iwf   8     0.012649         0.010782         0.013996                0
120     iwf   9     0.118978         0.009633         0.010177                0
121     iwf  10    -0.091157         0.007952         0.008944                0
122     iwf  11    -0.213718         0.006447         0.007589                0
123     iwf  12    -0.035736         0.006973         0.011360                0
124     iwf  13     0.020515         0.006913         0.010881                0
125     iwf  14     0.144842         0.005386         0.009270                0
126     iwf  15     0.132159         0.005079         0.008053                0
127     iwf  16    -0.031545         0.003429         0.006735                0
128     iwf  17     0.142129         0.002635         0.007646                0
129     iwf  18     0.114430         0.002258         0.003228                0
130     iwf  19     0.083869         0.001789         0.002004                0
131     iwf  20     0.039906         0.001129         0.001705                0
132     iwf  21     0.070769         0.001296         0.001289                0
133     iwf  22    -0.100570         0.001348         0.001158                0
134     iwf  23     0.177335         0.001215         0.001464                0
135     iwf  24     0.105209         0.001038         0.000185                0
136     iwf  25     0.011417         0.000911         0.000017                0
137     iwf  26    -0.097926         0.001022         0.000035                0
138     iwf  27     0.154260         0.000852         0.000000                0
139     iwf  28     0.009191         0.000022         0.000209                0
```

### 3.2 delisted_in_quarter over all POSITION_RETURNS rows, and price columns ending before 2026-09-30

```
   position_rows  delisted_rows  price_columns  columns_ending_before_2026_09_30
0          32921              0           1314                                 0
```

### 3.2 book_monthly.csv: months per entity, first and last month

```
        count      min      max
entity                         
akre       84  2019-10  2026-09
ivv        84  2019-10  2026-09
iwf        84  2019-10  2026-09
jensen     84  2019-10  2026-09
polen      84  2019-10  2026-09
```

### 3.2 buckets.csv: Akre t = 12

```
    entity   t    bucket    weight         r
154   akre  12     NoDur  0.000000       NaN
155   akre  12     Durbl  0.000000       NaN
156   akre  12     Manuf  0.000000       NaN
157   akre  12     Enrgy  0.000000       NaN
158   akre  12     Chems  0.000000       NaN
159   akre  12     BusEq  0.221661 -0.086251
160   akre  12     Telcm  0.000000       NaN
161   akre  12     Utils  0.000000       NaN
162   akre  12     Shops  0.133260 -0.040829
163   akre  12      Hlth  0.000000       NaN
164   akre  12     Money  0.248947 -0.123483
165   akre  12     Other  0.389722 -0.077142
166   akre  12  Unmapped  0.000000       NaN
167   akre  12  Unpriced  0.006410 -0.085915
```

### D.5 Akre t = 12 (holdings 2022-06-30, 2022-06-30 to 2022-09-30): every position

```
        sec_id ticker    bucket    weight         r  delisted_in_quarter last_price_date
289  57636Q104     MA     Other  0.148233 -0.097325                False      2022-09-30
279  03027X100    AMT     Money  0.142828 -0.159983                False      2022-09-30
290  615369105    MCO     Other  0.124308 -0.104165                False      2022-09-30
297  92826C839      V     Other  0.082753 -0.096121                False      2022-09-30
291  67103H107   ORLY     Shops  0.079564  0.113318                False      2022-09-30
288  48251W104    KKR     Money  0.057038 -0.068525                False      2022-09-30
282  143130102    KMX     Shops  0.053281 -0.270336                False      2022-09-30
292  776696106    ROP     BusEq  0.052362 -0.087313                False      2022-09-30
277  00724F101   ADBE     BusEq  0.048708 -0.248211                False      2022-09-30
281  112585104     BN     Money  0.047432 -0.077881                False      2022-09-30
293  79466L302    CRM     BusEq  0.040604 -0.128454                False      2022-09-30
283  22160N109   CSGP     Other  0.034427  0.152955                False      2022-09-30
296  92345Y106   VRSK     BusEq  0.033905 -0.013147                False      2022-09-30
284  235851102    DHR     BusEq  0.033630  0.019773                False      2022-09-30
294  833445109   SNOW     BusEq  0.011144  0.222206                False      2022-09-30
285  25401T108   DBRG  Unpriced  0.006410 -0.085915                False             NaN
278  011642105   ALRM     BusEq  0.001308  0.048497                False      2022-09-30
287  38267D109   GSHD     Money  0.001275 -0.219619                False      2022-09-30
286  256746108   DLTR     Shops  0.000411 -0.126724                False      2022-09-30
280  084670702  BRK/B     Money  0.000374 -0.021976                False      2022-09-30
295  88556E102   TDUP     Shops  0.000004 -0.264000                False      2022-09-30

sum of weight = np.float64(0.9999999999999992); sum of weight x r = np.float64(-0.08591489312968865); book_quarterly book_return = np.float64(-0.0859148931296887)
```

### 3.3 the 56 benchmark rows (outputs/tables/reconstruction.csv)

```
    entity   t     q_start       q_end  book_return  nav_return       gap
84     ivv   1  2019-09-30  2019-12-31     0.090926    0.089773  0.001153
85     ivv   2  2019-12-31  2020-03-31    -0.192722   -0.195585  0.002863
86     ivv   3  2020-03-31  2020-06-30     0.204703    0.203460  0.001243
87     ivv   4  2020-06-30  2020-09-30     0.090227    0.090080  0.000147
88     ivv   5  2020-09-30  2020-12-31     0.119313    0.121946 -0.002633
89     ivv   6  2020-12-31  2021-03-31     0.060469    0.063324 -0.002855
90     ivv   7  2021-03-31  2021-06-30     0.085887    0.083827  0.002060
91     ivv   8  2021-06-30  2021-09-30     0.005668    0.005907 -0.000239
92     ivv   9  2021-09-30  2021-12-31     0.112323    0.110687  0.001636
93     ivv  10  2021-12-31  2022-03-31    -0.047220   -0.045689 -0.001531
94     ivv  11  2022-03-31  2022-06-30    -0.160697   -0.161692  0.000995
95     ivv  12  2022-06-30  2022-09-30    -0.048632   -0.049189  0.000557
96     ivv  13  2022-09-30  2022-12-30     0.075578    0.075898 -0.000320
97     ivv  14  2022-12-30  2023-03-31     0.076199    0.074413  0.001786
98     ivv  15  2023-03-31  2023-06-30     0.088410    0.087629  0.000781
99     ivv  16  2023-06-30  2023-09-29    -0.032534   -0.032116 -0.000418
100    ivv  17  2023-09-29  2023-12-29     0.117148    0.116731  0.000418
101    ivv  18  2023-12-29  2024-03-28     0.106294    0.104210  0.002084
102    ivv  19  2024-03-28  2024-06-28     0.043352    0.044020 -0.000667
103    ivv  20  2024-06-28  2024-09-30     0.059053    0.058177  0.000876
104    ivv  21  2024-09-30  2024-12-31     0.024138    0.024145 -0.000007
105    ivv  22  2024-12-31  2025-03-31    -0.042805   -0.042525 -0.000281
106    ivv  23  2025-03-31  2025-06-30     0.109352    0.108451  0.000901
107    ivv  24  2025-06-30  2025-09-30     0.081040    0.081199 -0.000159
108    ivv  25  2025-09-30  2025-12-31     0.026677    0.026991 -0.000314
109    ivv  26  2025-12-31  2026-03-31    -0.043559   -0.043786  0.000228
110    ivv  27  2026-03-31  2026-06-30     0.152265    0.149556  0.002709
111    ivv  28  2026-06-30  2026-09-30     0.022748    0.025602 -0.002854
112    iwf   1  2019-09-30  2019-12-31     0.108057    0.104933  0.003124
113    iwf   2  2019-12-31  2020-03-31    -0.137663   -0.141104  0.003441
114    iwf   3  2020-03-31  2020-06-30     0.278522    0.276648  0.001874
115    iwf   4  2020-06-30  2020-09-30     0.133703    0.132229  0.001474
116    iwf   5  2020-09-30  2020-12-31     0.112985    0.113600 -0.000615
117    iwf   6  2020-12-31  2021-03-31     0.011434    0.009372  0.002062
118    iwf   7  2021-03-31  2021-06-30     0.120900    0.118326  0.002574
119    iwf   8  2021-06-30  2021-09-30     0.012649    0.011042  0.001607
120    iwf   9  2021-09-30  2021-12-31     0.118978    0.116596  0.002382
121    iwf  10  2021-12-31  2022-03-31    -0.091157   -0.090145 -0.001012
122    iwf  11  2022-03-31  2022-06-30    -0.213718   -0.210968 -0.002750
123    iwf  12  2022-06-30  2022-09-30    -0.035736   -0.035362 -0.000373
124    iwf  13  2022-09-30  2022-12-30     0.020515    0.020819 -0.000304
125    iwf  14  2022-12-30  2023-03-31     0.144842    0.142975  0.001868
126    iwf  15  2023-03-31  2023-06-30     0.132159    0.127931  0.004228
127    iwf  16  2023-06-30  2023-09-29    -0.031545   -0.031543 -0.000002
128    iwf  17  2023-09-29  2023-12-29     0.142129    0.142049  0.000081
129    iwf  18  2023-12-29  2024-03-28     0.114430    0.113211  0.001219
130    iwf  19  2024-03-28  2024-06-28     0.083869    0.082734  0.001135
131    iwf  20  2024-06-28  2024-09-30     0.039906    0.031356  0.008550
132    iwf  21  2024-09-30  2024-12-31     0.070769    0.070885 -0.000116
133    iwf  22  2024-12-31  2025-03-31    -0.100570   -0.099864 -0.000705
134    iwf  23  2025-03-31  2025-06-30     0.177335    0.176972  0.000363
135    iwf  24  2025-06-30  2025-09-30     0.105209    0.104256  0.000953
136    iwf  25  2025-09-30  2025-12-31     0.011417    0.011461 -0.000045
137    iwf  26  2025-12-31  2026-03-31    -0.097926   -0.098299  0.000373
138    iwf  27  2026-03-31  2026-06-30     0.154260    0.165848 -0.011588
139    iwf  28  2026-06-30  2026-09-30     0.009191    0.009686 -0.000495
```

### 3.3 benchmark quarters with |gap| > benchmark_gap_max (0.01), with that book's weights

```
  entity   t     q_start       q_end  book_return  nav_return       gap  unmapped_weight  unpriced_weight  delisted_weight
0    iwf  27  2026-03-31  2026-06-30      0.15426    0.165848 -0.011588         0.000852              0.0                0
```

### 3.3 benchmark nav_return (compounded month-end returns) against Convention 4.14 (close at q_end / close at q_start - 1)

```
   rows  max_abs_difference
0    56        4.857226e-16
```

### 3.3 benchmark |gap| summary per entity

```
            mean       max
entity                    
ivv     0.001168  0.002863
iwf     0.001975  0.011588
```

### 3.4 Table 4 in full (outputs/tables/reconstruction.csv, 140 rows)

```
     entity   t     q_start       q_end  book_return  nav_return       gap
0      akre   1  2019-09-30  2019-12-31     0.047890    0.034484  0.013407
1      akre   2  2019-12-31  2020-03-31    -0.147049   -0.111290 -0.035759
2      akre   3  2020-03-31  2020-06-30     0.245653    0.216651  0.029002
3      akre   4  2020-06-30  2020-09-30     0.063595    0.055704  0.007890
4      akre   5  2020-09-30  2020-12-31     0.054601    0.057464 -0.002863
5      akre   6  2020-12-31  2021-03-31     0.034662    0.039743 -0.005081
6      akre   7  2021-03-31  2021-06-30     0.104614    0.097951  0.006663
7      akre   8  2021-06-30  2021-09-30     0.004667    0.019602 -0.014935
8      akre   9  2021-09-30  2021-12-31     0.077700    0.069753  0.007948
9      akre  10  2021-12-31  2022-03-31    -0.102094   -0.111861  0.009767
10     akre  11  2022-03-31  2022-06-30    -0.126510   -0.130204  0.003694
11     akre  12  2022-06-30  2022-09-30    -0.085915   -0.085039 -0.000875
12     akre  13  2022-09-30  2022-12-30     0.105203    0.093295  0.011908
13     akre  14  2022-12-30  2023-03-31     0.040498    0.059146 -0.018648
14     akre  15  2023-03-31  2023-06-30     0.089714    0.086178  0.003536
15     akre  16  2023-06-30  2023-09-29    -0.038365   -0.041110  0.002745
16     akre  17  2023-09-29  2023-12-29     0.175433    0.167045  0.008388
17     akre  18  2023-12-29  2024-03-28     0.076993    0.081464 -0.004471
18     akre  19  2024-03-28  2024-06-28    -0.027053   -0.018584 -0.008469
19     akre  20  2024-06-28  2024-09-30     0.128128    0.118847  0.009282
20     akre  21  2024-09-30  2024-12-31     0.013124   -0.004100  0.017224
21     akre  22  2024-12-31  2025-03-31     0.020716    0.015352  0.005363
22     akre  23  2025-03-31  2025-06-30     0.042588    0.064556 -0.021968
23     akre  24  2025-06-30  2025-09-30     0.005621         NaN       NaN
24     akre  25  2025-09-30  2025-12-31    -0.018694         NaN       NaN
25     akre  26  2025-12-31  2026-03-31    -0.170979   -0.193253  0.022274
26     akre  27  2026-03-31  2026-06-30     0.001572    0.006433 -0.004861
27     akre  28  2026-06-30  2026-09-30    -0.008899   -0.009776  0.000877
28   jensen   1  2019-09-30  2019-12-31     0.085234    0.082745  0.002488
29   jensen   2  2019-12-31  2020-03-31    -0.178632   -0.171907 -0.006724
30   jensen   3  2020-03-31  2020-06-30     0.178151    0.173390  0.004761
31   jensen   4  2020-06-30  2020-09-30     0.100136    0.095853  0.004282
32   jensen   5  2020-09-30  2020-12-31     0.118022    0.115434  0.002588
33   jensen   6  2020-12-31  2021-03-31     0.028329    0.028081  0.000248
34   jensen   7  2021-03-31  2021-06-30     0.080501    0.078602  0.001899
35   jensen   8  2021-06-30  2021-09-30     0.021901    0.021630  0.000271
36   jensen   9  2021-09-30  2021-12-31     0.152094    0.151437  0.000658
37   jensen  10  2021-12-31  2022-03-31    -0.075548   -0.075534 -0.000014
38   jensen  11  2022-03-31  2022-06-30    -0.125448   -0.124458 -0.000990
39   jensen  12  2022-06-30  2022-09-30    -0.051749   -0.052821  0.001073
40   jensen  13  2022-09-30  2022-12-30     0.096507    0.090349  0.006158
41   jensen  14  2022-12-30  2023-03-31     0.047807    0.046000  0.001807
42   jensen  15  2023-03-31  2023-06-30     0.061948    0.058806  0.003142
43   jensen  16  2023-06-30  2023-09-29    -0.037225   -0.037548  0.000323
44   jensen  17  2023-09-29  2023-12-29     0.100828    0.096206  0.004623
45   jensen  18  2023-12-29  2024-03-28     0.050739    0.043018  0.007721
46   jensen  19  2024-03-28  2024-06-28     0.012415    0.013066 -0.000651
47   jensen  20  2024-06-28  2024-09-30     0.069949    0.068437  0.001512
48   jensen  21  2024-09-30  2024-12-31    -0.022663   -0.023040  0.000377
49   jensen  22  2024-12-31  2025-03-31    -0.014160   -0.014021 -0.000139
50   jensen  23  2025-03-31  2025-06-30     0.047604    0.039673  0.007931
51   jensen  24  2025-06-30  2025-09-30     0.032337    0.029757  0.002580
52   jensen  25  2025-09-30  2025-12-31    -0.004894   -0.008226  0.003332
53   jensen  26  2025-12-31  2026-03-31    -0.100097   -0.103267  0.003170
54   jensen  27  2026-03-31  2026-06-30     0.112393    0.107906  0.004488
55   jensen  28  2026-06-30  2026-09-30     0.026403    0.023377  0.003027
56    polen   1  2019-09-30  2019-12-31     0.108928    0.103100  0.005829
57    polen   2  2019-12-31  2020-03-31    -0.132374   -0.131843 -0.000531
58    polen   3  2020-03-31  2020-06-30     0.288204    0.270386  0.017818
59    polen   4  2020-06-30  2020-09-30     0.105408    0.099532  0.005876
60    polen   5  2020-09-30  2020-12-31     0.102433    0.098803  0.003630
61    polen   6  2020-12-31  2021-03-31     0.020711    0.015686  0.005025
62    polen   7  2021-03-31  2021-06-30     0.133445    0.129344  0.004101
63    polen   8  2021-06-30  2021-09-30     0.021064    0.025451 -0.004387
64    polen   9  2021-09-30  2021-12-31     0.054932    0.049984  0.004948
65    polen  10  2021-12-31  2022-03-31    -0.137879   -0.136097 -0.001782
66    polen  11  2022-03-31  2022-06-30    -0.233761   -0.240552  0.006791
67    polen  12  2022-06-30  2022-09-30    -0.057588   -0.054795 -0.002794
68    polen  13  2022-09-30  2022-12-30     0.016889   -0.005945  0.022833
69    polen  14  2022-12-30  2023-03-31     0.141916    0.140512  0.001404
70    polen  15  2023-03-31  2023-06-30     0.105697    0.104778  0.000919
71    polen  16  2023-06-30  2023-09-29    -0.032339   -0.038822  0.006483
72    polen  17  2023-09-29  2023-12-29     0.151653    0.152887 -0.001234
73    polen  18  2023-12-29  2024-03-28     0.085048    0.078298  0.006750
74    polen  19  2024-03-28  2024-06-28     0.002588   -0.002399  0.004986
75    polen  20  2024-06-28  2024-09-30     0.034493    0.028852  0.005641
76    polen  21  2024-09-30  2024-12-31     0.048948    0.047494  0.001454
77    polen  22  2024-12-31  2025-03-31    -0.063893   -0.063100 -0.000793
78    polen  23  2025-03-31  2025-06-30     0.091665    0.090785  0.000880
79    polen  24  2025-06-30  2025-09-30     0.036568    0.031081  0.005487
80    polen  25  2025-09-30  2025-12-31    -0.015879   -0.014207 -0.001673
81    polen  26  2025-12-31  2026-03-31    -0.157609   -0.175385  0.017776
82    polen  27  2026-03-31  2026-06-30     0.065859    0.069539 -0.003680
83    polen  28  2026-06-30  2026-09-30     0.039180    0.041865 -0.002685
84      ivv   1  2019-09-30  2019-12-31     0.090926    0.089773  0.001153
85      ivv   2  2019-12-31  2020-03-31    -0.192722   -0.195585  0.002863
86      ivv   3  2020-03-31  2020-06-30     0.204703    0.203460  0.001243
87      ivv   4  2020-06-30  2020-09-30     0.090227    0.090080  0.000147
88      ivv   5  2020-09-30  2020-12-31     0.119313    0.121946 -0.002633
89      ivv   6  2020-12-31  2021-03-31     0.060469    0.063324 -0.002855
90      ivv   7  2021-03-31  2021-06-30     0.085887    0.083827  0.002060
91      ivv   8  2021-06-30  2021-09-30     0.005668    0.005907 -0.000239
92      ivv   9  2021-09-30  2021-12-31     0.112323    0.110687  0.001636
93      ivv  10  2021-12-31  2022-03-31    -0.047220   -0.045689 -0.001531
94      ivv  11  2022-03-31  2022-06-30    -0.160697   -0.161692  0.000995
95      ivv  12  2022-06-30  2022-09-30    -0.048632   -0.049189  0.000557
96      ivv  13  2022-09-30  2022-12-30     0.075578    0.075898 -0.000320
97      ivv  14  2022-12-30  2023-03-31     0.076199    0.074413  0.001786
98      ivv  15  2023-03-31  2023-06-30     0.088410    0.087629  0.000781
99      ivv  16  2023-06-30  2023-09-29    -0.032534   -0.032116 -0.000418
100     ivv  17  2023-09-29  2023-12-29     0.117148    0.116731  0.000418
101     ivv  18  2023-12-29  2024-03-28     0.106294    0.104210  0.002084
102     ivv  19  2024-03-28  2024-06-28     0.043352    0.044020 -0.000667
103     ivv  20  2024-06-28  2024-09-30     0.059053    0.058177  0.000876
104     ivv  21  2024-09-30  2024-12-31     0.024138    0.024145 -0.000007
105     ivv  22  2024-12-31  2025-03-31    -0.042805   -0.042525 -0.000281
106     ivv  23  2025-03-31  2025-06-30     0.109352    0.108451  0.000901
107     ivv  24  2025-06-30  2025-09-30     0.081040    0.081199 -0.000159
108     ivv  25  2025-09-30  2025-12-31     0.026677    0.026991 -0.000314
109     ivv  26  2025-12-31  2026-03-31    -0.043559   -0.043786  0.000228
110     ivv  27  2026-03-31  2026-06-30     0.152265    0.149556  0.002709
111     ivv  28  2026-06-30  2026-09-30     0.022748    0.025602 -0.002854
112     iwf   1  2019-09-30  2019-12-31     0.108057    0.104933  0.003124
113     iwf   2  2019-12-31  2020-03-31    -0.137663   -0.141104  0.003441
114     iwf   3  2020-03-31  2020-06-30     0.278522    0.276648  0.001874
115     iwf   4  2020-06-30  2020-09-30     0.133703    0.132229  0.001474
116     iwf   5  2020-09-30  2020-12-31     0.112985    0.113600 -0.000615
117     iwf   6  2020-12-31  2021-03-31     0.011434    0.009372  0.002062
118     iwf   7  2021-03-31  2021-06-30     0.120900    0.118326  0.002574
119     iwf   8  2021-06-30  2021-09-30     0.012649    0.011042  0.001607
120     iwf   9  2021-09-30  2021-12-31     0.118978    0.116596  0.002382
121     iwf  10  2021-12-31  2022-03-31    -0.091157   -0.090145 -0.001012
122     iwf  11  2022-03-31  2022-06-30    -0.213718   -0.210968 -0.002750
123     iwf  12  2022-06-30  2022-09-30    -0.035736   -0.035362 -0.000373
124     iwf  13  2022-09-30  2022-12-30     0.020515    0.020819 -0.000304
125     iwf  14  2022-12-30  2023-03-31     0.144842    0.142975  0.001868
126     iwf  15  2023-03-31  2023-06-30     0.132159    0.127931  0.004228
127     iwf  16  2023-06-30  2023-09-29    -0.031545   -0.031543 -0.000002
128     iwf  17  2023-09-29  2023-12-29     0.142129    0.142049  0.000081
129     iwf  18  2023-12-29  2024-03-28     0.114430    0.113211  0.001219
130     iwf  19  2024-03-28  2024-06-28     0.083869    0.082734  0.001135
131     iwf  20  2024-06-28  2024-09-30     0.039906    0.031356  0.008550
132     iwf  21  2024-09-30  2024-12-31     0.070769    0.070885 -0.000116
133     iwf  22  2024-12-31  2025-03-31    -0.100570   -0.099864 -0.000705
134     iwf  23  2025-03-31  2025-06-30     0.177335    0.176972  0.000363
135     iwf  24  2025-06-30  2025-09-30     0.105209    0.104256  0.000953
136     iwf  25  2025-09-30  2025-12-31     0.011417    0.011461 -0.000045
137     iwf  26  2025-12-31  2026-03-31    -0.097926   -0.098299  0.000373
138     iwf  27  2026-03-31  2026-06-30     0.154260    0.165848 -0.011588
139     iwf  28  2026-06-30  2026-09-30     0.009191    0.009686 -0.000495
```

### 3.4 outputs/tables/gate.csv

```
     fund      corr  pass  n_quarters  mean_gap   std_gap  mean_abs_gap  te_gap_ann
0    akre  0.990028  True          26  0.001617  0.013935      0.010688    0.027870
1  jensen  0.999606  True          28  0.002141  0.002932      0.002749    0.005864
2   polen  0.998184  True          28  0.003895  0.006556      0.005292    0.013112
```

### 3.4 the gap rows of outputs/tables/bootstrap.csv

```
     fund series      mean       p05       p95
0    akre    gap  0.001617 -0.000686  0.003859
1  jensen    gap  0.002141  0.001390  0.002864
2   polen    gap  0.003895  0.002680  0.005220
```

### 3.4 std_gap and te_gap_ann with ddof 1 (as in gate.csv) and ddof 0, for the reviewer

```
        std_ddof1  std_ddof0  te_ann_ddof1  te_ann_ddof0
entity                                                  
akre     0.013935   0.013665      0.027870      0.027329
jensen   0.002932   0.002879      0.005864      0.005758
polen    0.006556   0.006438      0.013112      0.012876
```

### 3.4 blank NAV quarters (amendment 11)

```
   entity   t     q_start       q_end  book_return  nav_return  gap
23   akre  24  2025-06-30  2025-09-30     0.005621         NaN  NaN
24   akre  25  2025-09-30  2025-12-31    -0.018694         NaN  NaN
```

### 3.4 fund quarters with |gap| > 1%

```
   entity   t     q_start       q_end  book_return  nav_return       gap  unmapped_weight  unpriced_weight  delisted_weight
0    akre   1  2019-09-30  2019-12-31     0.047890    0.034484  0.013407         0.000054         0.003707                0
1    akre   2  2019-12-31  2020-03-31    -0.147049   -0.111290 -0.035759         0.000000         0.007186                0
2    akre   3  2020-03-31  2020-06-30     0.245653    0.216651  0.029002         0.000000         0.012230                0
3    akre   8  2021-06-30  2021-09-30     0.004667    0.019602 -0.014935         0.000288         0.018144                0
4    akre  13  2022-09-30  2022-12-30     0.105203    0.093295  0.011908         0.000000         0.005108                0
5    akre  14  2022-12-30  2023-03-31     0.040498    0.059146 -0.018648         0.000000         0.004941                0
6    akre  21  2024-09-30  2024-12-31     0.013124   -0.004100  0.017224         0.000000         0.001546                0
7    akre  23  2025-03-31  2025-06-30     0.042588    0.064556 -0.021968         0.000000         0.000140                0
8    akre  26  2025-12-31  2026-03-31    -0.170979   -0.193253  0.022274         0.000000         0.000000                0
9   polen   3  2020-03-31  2020-06-30     0.288204    0.270386  0.017818         0.000177         0.000000                0
10  polen  13  2022-09-30  2022-12-30     0.016889   -0.005945  0.022833         0.000697         0.000000                0
11  polen  26  2025-12-31  2026-03-31    -0.157609   -0.175385  0.017776         0.000698         0.000000                0
```

### 3.0 reused tickers in the new price columns

2 of the 13 new columns belong to a different, later company. `INFO` starts 2024-10-10, while IHS Markit merged into S&P Global in 2022. `STI` starts 2022-05-02, while SunTrust merged into Truist in 2019. No position is ever priced from them:

```
ticker  bucket    entity
INFO    Unpriced  ivv       10
                  iwf        7
STI     Unpriced  ivv        1
```

### 3.2 test prints: the hand-built and delisted cases, and the real-book identities

```
  entity  t cusip sec_id issuer6 ticker bucket  weight     r  delisted_in_quarter last_price_date
0   fund  1   AAA    AAA     AAA    AAA  BusEq     0.5  0.10                False      2020-03-31
1   fund  1   BBB    BBB     BBB    BBB  BusEq     0.3 -0.10                False      2020-03-31
2   fund  1   CCC    CCC     CCC    CCC   Hlth     0.2  0.25                False      2020-03-31
   entity  t    bucket  weight      r
0    fund  1     NoDur     0.0    NaN
1    fund  1     Durbl     0.0    NaN
2    fund  1     Manuf     0.0    NaN
3    fund  1     Enrgy     0.0    NaN
4    fund  1     Chems     0.0    NaN
5    fund  1     BusEq     0.8  0.025
6    fund  1     Telcm     0.0    NaN
7    fund  1     Utils     0.0    NaN
8    fund  1     Shops     0.0    NaN
9    fund  1      Hlth     0.2  0.250
10   fund  1     Money     0.0    NaN
11   fund  1     Other     0.0    NaN
12   fund  1  Unmapped     0.0    NaN
13   fund  1  Unpriced     0.0    NaN
.       entity  t cusip issuer6 ticker    bucket  weight      r  delisted_in_quarter last_price_date
sec_id                                                                                             
AAA      fund  1   AAA     AAA    AAA     BusEq     0.4  0.100                False      2020-03-31
DDD      fund  1   DDD     DDD    DDD     Enrgy     0.4 -0.250                 True      2020-02-28
EEE      fund  1   EEE     EEE    EEE  Unpriced     0.1 -0.075                False                
FFF      fund  1   FFF     FFF         Unmapped     0.1 -0.075                False                
month
2020-01   -0.052500
2020-02   -0.060686
2020-03    0.039326
Freq: M
.140 books, max |sum w_s r_s - priced, mapped return| = 8.327e-17
.140 books, max |compounded monthly - quarterly| = 7.910e-16
.      sec_id id_type ticker yf_ticker figi           figi_name     cik   sic   ff12 map_status                 source
0  867914103   cusip    STI       STI   F3  SUNTRUST BANKS INC     999  3571  BusEq     mapped               openfigi
0  867914103   cusip    STI       STI   F3  SUNTRUST BANKS INC  750556  6021  Money     mapped  openfigi;override_cik
.      sec_id     cik       submissions_name       note_name  match
0  867914103  750556  TRUIST FINANCIAL CORP  SunTrust Banks  False
.
```

## Tests run

`pytest -p socket --disable-socket -q`:

```
..................................................                       [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\Utkarsh\10. Quant Projects\6) Attribution Engine On Real Holdings\repo-clone\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
50 passed, 1 warning in 83.61s (0:01:23)
```

That is the 43 tests of Sections 1 and 2, plus 7 new:

- `test_mapping.py`: `test_cik_override_beats_ticker_lookup` and `test_cik_override_name_mismatch_not_applied`;
- `test_overrides.py`: `test_each_override_changes_only_named_rows`;
- `test_returns_book.py`: `test_hand_built_three_stock_quarter`, `test_delisted_mid_quarter`, `test_bucket_identity_every_real_book` and `test_monthly_compounds_to_quarterly`.

`test_config.py::test_keys_match_spec_both_ways` now includes `gates.benchmark_gap_stop`.

## Fresh-clone check

Per E: the 5 step commits were pushed first (`cd105b1..2596b35`). `git ls-remote` then returned `2596b354f7b91e6a43d5ba62c67917249e6a8217` for `refs/heads/main`, equal to local `HEAD`, and GitHub was cloned into `C:\t\s3`. The install output is trimmed to its last lines:

```
$ git clone -q https://github.com/uty101/Attribution-Engine-On-Real-Holdings.git /c/t/s3
$ git log --oneline -1
2596b35 step 3.4: reconstruction table, fund gate and gap bootstrap
$ uv venv --python 3.12
Using CPython 3.12.13
Creating virtual environment at: .venv
Activate with: .venv\Scripts\activate
$ uv pip install -r requirements-lock.txt
 + wrapt==2.5.0
 + yfinance==1.7.0
$ uv pip install -e . --no-deps
 + attrib==0.0.0 (from file:///C:/t/s3)
$ .venv/Scripts/python.exe -m pytest -p socket --disable-socket -q
..................................................                       [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\t\s3\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
50 passed, 1 warning in 104.50s (0:01:44)
$ .venv/Scripts/python.exe scripts/run_all.py --section 3
section 1: all checks passed
section 2: all checks passed
benchmark quarters with |gap| > benchmark_gap_max (0.01):
  entity   t     q_start       q_end  book_return  nav_return       gap  unmapped_weight  unpriced_weight  delisted_weight
0    iwf  27  2026-03-31  2026-06-30      0.15426    0.165848 -0.011588         0.000852              0.0              0.0
section 3: all checks passed
$ git status --short
$
```

## Runtime per step

These are wall-clock times on this machine, and they varied by a factor of up to 5 between identical runs. The Section 1 XML rebuild alone took between 16 s and 94 s.

- 3.0: `--stage sec --overrides-only` 12 s; `--stage prices --new-only` 29 s; `run_all.py --section 2` 17 s.
- 3.2: `run_all.py --section 3`, 1 to 3.5 min, mostly the Section 1 and 2 rebuild. Over the 140 books, `book_quarter` takes 5 s and `book_monthly` 3 s.
- 3.3 and 3.4: under 1 s on top of 3.2. The bootstrap is 3 × 10000 replications.
- Suite: 1.5 to 3.5 min. The 2 real-book tests rebuild every book from `data/raw/` once (rule 7).

## Deviations from PLAN.md

Accepted in earlier sessions, not repeated here.

New in session 3. Each is a choice the instructions do not make, listed for confirmation:

1. **An existing test's input changed.** `test_cik_override` (Section 2) used `source_note = "reviewer"`. Under Section B's new name check, "REVIEWER" does not match the synthetic CIK name "GONE CO", so the override is no longer applied and the test failed. The only change is that input, now `"Gone Co"`. Every assertion is unchanged: `cik`, `sic`, `ff12`, `map_status` and `source`. It is the same kind of change as the 2 accepted in 02c, a test updated to a format the instructions changed. It is not a loosened test. If the reviewer reads rule 5 as forbidding it, the alternative was a rule 4 stop at step 3.0.
2. **POSITION_RETURNS has a `sec_id` column after `cusip`.** It is the kickoff 6.2 schema plus 1 column, with nothing renamed or dropped. The IVV books have 745 ISIN-only rows (amendment 8) whose `cusip` is blank, so `cusip` alone cannot identify a position or carry a `quarter_return` override keyed by `sec_id`. `cusip` is the HOLDINGS value, blank for ISIN rows. `issuer6` is its first 6 characters, so it too is blank for ISIN rows; amendment 10 makes the CIK the issuer key anyway.
3. **`--stage sec` and `--stage prices` gained the flags `--overrides-only` and `--new-only`.** `--new-only` is what step 3.0's "only for `yf_ticker`s not already columns" requires. `--overrides-only` reads "`--stage sec` for the override CIKs" the same way:
   - it fetches only the override CIKs and the CIKs override tickers reach that `sic.csv` lacks;
   - it rewrites only those rows of `sic.csv`;
   - it keeps the committed `company_tickers.json`, since a new download would also move every other ticker → CIK match to a new date.

   Without the flags, both stages behave as in Section 2.
4. **Where the `cik` name check reads the submissions name.** `build_security_map` keeps its 6-argument signature. It reads the `name` column of `sic.csv`, which is the submissions JSON `name`. `--stage sec --overrides-only` writes that name for every override CIK in the same run that writes `cik_override_check.csv`, and both use `cik_override_check`, so the two cannot disagree. A `cik` row whose CIK has no `sic.csv` row has no name and counts as a mismatch. No such row exists.
5. **`period_date` of a `quarter_return` row is the holdings date h_t.** `return_overrides_with_t` maps it to `t` with QUARTERS before `apply_return_overrides(pos, overrides)`, which keeps the D-16 signature. A `period_date` that is not a holdings date raises.
6. **A `quarter_return` override recomputes its book's neutral return.** Convention 4.9 defines the Unmapped and Unpriced return as the book's priced, mapped return, which an override changes. So the Unmapped and Unpriced rows of the changed book take the new value. `test_each_override_changes_only_named_rows` asserts this 1 consequence explicitly, and asserts that every other row is unchanged. An override naming an Unmapped or Unpriced row raises, since that row has no return of its own.
7. **Empty buckets in `buckets.csv`.** All 14 rows are present for every (entity, t). `r` is blank where `weight` is 0 (Convention 4.10 defines r_s only for positive weight). Section 4's empty-bucket rules (Convention 4.11) fill them.
8. **`delisted_in_quarter` is "last close before q_end".** P(end) is the last close on or before q_end. The same rule covers a gap in a series that resumes later, but no such case occurs: every price column runs to 2026-09-30.
9. **Month-end dates for `book_monthly`** are the last date of the price panel's index in each calendar month after q_start. The function raises if the last of them is not q_end. On the real data it never raised.
10. **Benchmark NAV returns go through the same path as the funds'.** They are compounded calendar-month returns from `nav_adjclose.csv` (amendment 11's rule), not the direct q-close ratio of Convention 4.14. Over the 56 benchmark rows the 2 differ by at most 4.9e-16 (printed under 3.3).
11. **`reconstruction.csv` holds all 5 entities, 140 rows.** Under D-18 A, the benchmark rows are written in 3.3 and the fund rows added in 3.4. `gate.csv` and `bootstrap.csv` have the 3 funds only.
12. **`std_gap` uses ddof 1** and `te_gap_ann` = 2 × `std_gap` (kickoff 5.4). The kickoff does not say which ddof. Both versions are printed under 3.4; the gate does not depend on it.
13. **Bootstrap details.** The same seed `run.bootstrap_seed` is used for each fund. The interval is `numpy.quantile` (linear) of the 10000 resampled means at `bootstrap.lo` and `bootstrap.hi`. `mean` is the sample mean of the gap series. For Akre, the 26 non-blank quarters are concatenated in `t` order, so blocks run across the gap at t = 24 and 25.
14. **Commit 3.1 holds only the 3.1 code.** `attrib/returns.py` was written for 3.1 and 3.2 together. The 3.1 commit carries only `POSITION_RETURNS`, `_neutral`, `return_overrides_with_t` and `apply_return_overrides`; 3.2 adds the rest.

## Not verified

- **Whether each override ticker is the security held** beyond the evidence above (the map rows, the `cik` name check and the first price date). In particular, a ticker reused by a later company would show up only if that company's history overlapped the holding. INFO and STI are the 2 such columns found, and neither prices any position.
- **That the 29 tickers unpriced at their first `q_start`** (D.2) have no other yfinance symbol that would price them. Every one of them has a reviewer `cik` override, which marks it as an expected delisting, and Section B expects such names in Unpriced.
- **Spin-offs that adjusted closes miss.** None was searched for beyond the large-move lists. Examples are Brookfield's December 2022 split into BN and BAM, and United Technologies' April 2020 separation. Jensen held UTX only at 2019-09-30 and 2019-12-31 (t = 1, 2), which end before the separation.
- **Why IWF t = 27 has a −1.16% gap.** Its book has 0.09% unmapped and 0% unpriced weight. The quarter runs to 2026-06-30 and so spans the June Russell reconstitution, which a 2026-03-31 book cannot reflect. That is a plausible cause, not a checked one.

## Open questions

1. **Deviation 1:** is the `source_note` input change in `test_cik_override` acceptable, or should it have been a rule 4 stop?
2. **Deviation 2:** should POSITION_RETURNS keep `cusip` and add `sec_id`, as built, or should `sec_id` replace `cusip`?
3. **Deviation 12:** should the gap standard deviation be ddof 1 or ddof 0?
4. **The IWF t = 27 benchmark gap of −1.16%**, the only benchmark quarter above `benchmark_gap_max` (0.01). Its weights are under 3.3.
5. **Candidates for `quarter_return` overrides** are the 2 large-move lists under D.4:
   - 10 fund position-quarters with a daily |return| > 25% and weight > 0.5%. They include Akre's FICO at t = 28 (8.5%, −26.5% on 2026-09-29), Polen's ORCL at t = 24 (8.0%, +35.9%) and META at t = 10 (5.9%, −26.4%).
   - 4 IVV and IWF position-quarters with weight > 1%.

   Nothing was adjusted.
6. **Remaining unpriced weight.** It is largest in the early IVV and IWF books (2.7% and 3.0% at 2019-09-30) and for Akre (1.9% at its maximum), mostly the delisted names in D.2. It earns the neutral return under Convention 4.9.

## Files changed

- 3.0: `data/manual/overrides.csv`, `attrib/mapping.py`, `scripts/pull_data.py`, `tests/test_mapping.py`, `data/raw/sec/sic.csv`, `data/raw/sec/cik_override_check.csv` (new), `data/raw/prices/adjclose.parquet`, `data/raw/prices/missing.csv`, `data/raw/MANIFEST.json`, `outputs/tables/coverage.csv`, `large_moves.csv`, `unmapped_top.csv`, `unpriced_top.csv`
- 3.1: `attrib/returns.py`, `tests/test_overrides.py` (new)
- 3.2: `attrib/returns.py`, `scripts/run_all.py`, `tests/test_returns_book.py` (new), `outputs/tables/buckets.csv`, `book_quarterly.csv`, `book_monthly.csv` (new)
- 3.3: `attrib/reconstruction.py` (new), `attrib/config.py`, `config.toml`, `tests/test_config.py`, `scripts/run_all.py`, `outputs/tables/reconstruction.csv` (new)
- 3.4: `attrib/reconstruction.py`, `attrib/bootstrap.py` (new), `scripts/run_all.py`, `outputs/tables/reconstruction.csv`, `gate.csv` (new), `bootstrap.csv` (new)
- Session end: `review/section_3.md`, `instructions/03_section_3.status.md`

`data/processed/position_returns.csv` is written but gitignored (D-17). `CLAUDE.md`, `PLAN.md` and `decisions/OPEN.md` are unchanged.

## Reviewer reads

1. `instructions/03_section_3.status.md`
2. This file: Deviations 1, 2 and 12, then Open questions.
3. Evidence D.1, D.2 and 3.4 (gate and bootstrap).
4. `attrib/returns.py` from `BUCKETS_ORDER` down, and `attrib/reconstruction.py`.
5. `tests/test_returns_book.py`, `tests/test_overrides.py`, and the 2 new tests at the end of `tests/test_mapping.py`.
6. `build_security_map` and `cik_override_check` in `attrib/mapping.py`.
7. `stage_sec_overrides` and `stage_prices_new` in `scripts/pull_data.py`.
