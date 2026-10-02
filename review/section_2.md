# Review — Section 2

## Section

Section 2, Mapping, sectors, prices and factors. **Stopped under rule 4 at step 2.3.**

Instruction 02, Section D: "yfinance returns no data for IVV, IWF or any NAV ticker: stop under rule 4." The `--stage prices` run returned 0 rows for AKRIX, the Akre NAV ticker. Before that, the run had written the full stock price panel. Steps 2.1 and 2.2 are complete. Step 2.3 is committed with everything except `nav_adjclose.csv`. Steps 2.4 and 2.5 were not started.

A second Section D condition is also met, and Section D says to report it rather than stop. OpenFIGI's `no_match` holds more than 5% of the value of 59 books. It is Open question 1, with the 10 largest offenders.

## Steps completed

- 2.1 `--stage figi` (OpenFIGI, `sec_id` keyed, `ID_CUSIP` or `ID_ISIN`) and `--stage sec` (`company_tickers.json`, `sic.csv`), `data/raw/openfigi/mapping.csv` — `0b64589`
- 2.2 `attrib/mapping.py`, `tests/test_mapping.py` (6 tests), `--stage french` and its 3 files, `data/manual/overrides.csv` header, `run_all.py --section 2` writing `data/processed/security_map.csv` — `097028f`
- 2.3 (stopped) `--stage prices`, `attrib/returns.py` (`load_prices`, `load_nav`), `attrib/factors.py` (`load_french`), `tests/test_data_loaders.py` (2 tests), `data/raw/prices/adjclose.parquet` and `missing.csv`; no `nav_adjclose.csv` — `c233354`
- 2.4 not started
- 2.5 not started

## Evidence

### The stop: yfinance has no AKRIX data

The tail of `python scripts/pull_data.py --stage prices`. The stock panel was written first, then the NAV call stopped:

```
  1250 / 1267
  1267 / 1267
panel (2723, 1265), 2015-12-01 to 2026-09-30, 2 missing
$AKRIX: possibly delisted; no price data found  (1d 2015-12-01 -> 2026-10-01)

1 Failed download:
['AKRIX']: possibly delisted; no price data found  (1d 2015-12-01 -> 2026-10-01)
stop under rule 4: yfinance returned no data for ['AKRIX']: {}
```

To check the stop is not a one-off failure, a one-off shell command (not repo code, nothing committed) repeated the same `download` call for each ticker:

```
AKRIX (0, 6)
AKREX (0, 6)
AKRSX (0, 6)
JENIX (2723, 5) (datetime.date(2015, 12, 1), datetime.date(2026, 9, 30))
POLIX (2723, 5) (datetime.date(2015, 12, 1), datetime.date(2026, 9, 30))
AKRE (233, 5) (datetime.date(2025, 10, 27), datetime.date(2026, 9, 30))
AKRE info: {'longName': None, 'quoteType': 'ETF', 'fundInceptionDate': 1251676800, 'legalType': 'Exchange Traded Fund'}
```

`fundInceptionDate` 1251676800 is 2009-08-31. The 2 options are in `decisions/OPEN.md`, OPEN-31.

### 2.1 OpenFIGI status per distinct sec_id

The universe is every distinct `sec_id` in the 140 books in H: 1622 (1553 CUSIPs, 69 ISINs). Every job returned at most 1 result:

```
  id_type                status  n_sec_ids
0   cusip  No identifier found.        335
1   cusip                    ok       1218
2    isin  No identifier found.         19
3    isin                    ok         50

rows 1622, distinct sec_ids 1622, max results per sec_id 1
        market_sector  rows
0              Equity  1268
1  (blank, no result)   354
```

### 2.1 distinct sec_ids per entity, by id_type and map_status (all 28 books)

```
map_status    mapped  no_match  no_cik  no_sic
akre   cusip      38        10       0       0
jensen cusip     118        21       1       1
polen  cusip     459        78      29       1
ivv    cusip     535        76       4       0
       isin       33        13       0       0
iwf    cusip     762       235       4       0
       isin       28        13       0       0
```

### 2.1 sic.csv: CIKs with and without SIC

1267 distinct OpenFIGI equity tickers reach 1221 CIKs through `company_tickers.json`:

```
   ciks  with_sic  without_sic
0  1221      1220            1

        cik                    name sic sic_description
366  884394  SPDR S&P 500 ETF TRUST
```

### 2.2 SECURITY_MAP over all 1622 sec_ids

```
  id_type map_status     n
0   cusip     mapped  1183
1   cusip     no_cik    34
2   cusip   no_match   335
3   cusip     no_sic     1
4    isin     mapped    50
5    isin   no_match    19

                 ff12    n
0   (blank: no_match)  354
1               BusEq  265
2               Other  222
3               Money  194
4                Hlth  141
5               Manuf  130
6               Shops  107
7               NoDur   58
8               Utils   38
9               Chems   37
10              Telcm   28
11              Enrgy   25
12              Durbl   23

     source     n
0  openfigi  1622
```

The `no_sic` row:

```
         sec_id id_type ticker yf_ticker          figi                     figi_name     cik sic   ff12 map_status    source
1144  78462F103   cusip    SPY       SPY  BBG000BDTBL9  SS SPDR S&P 500 ETF TRUST-US  884394      Other     no_sic  openfigi
```

All 34 `no_cik` rows. 29 of them are exchange-traded funds, mostly in Polen's 13F book; the rest are delisted or acquired companies (CTRA, CMA, FTCHQ, FRCB, SBNY):

```
         sec_id ticker yf_ticker          figi                     figi_name map_status
249   127097103   CTRA      CTRA  BBG000C3GN47            COTERRA ENERGY INC     no_cik
336   200340107    CMA       CMA  BBG000C75N77                  COMERICA INC     no_cik
511   30744W107  FTCHQ     FTCHQ  BBG00LSD4456          FARFETCH LTD-CLASS A     no_cik
520   316092857   FREL      FREL  BBG008229880     FIDELITY MSCI RL EST INDX     no_cik
526   33616C100   FRCB      FRCB  BBG0019LSQ49        FIRST REPUBLIC BANK/CA     no_cik
528   337344105   QQEW      QQEW  BBG000F9KBH8    FIRST TR NASDAQ-100 SEL EQ     no_cik
582   37954Y889   CATH      CATH  BBG00CP9KWJ3   GLOBAL X S&P 500 CA VAL ETF     no_cik
694   46137V357    RSP       RSP  BBG00KJR2MY7  INVESCO S&P 500 EQUAL WEIGHT     no_cik
703   464287200    IVV       IVV  BBG000BVZ4F5      ISHARES CORE S&P 500 ETF     no_cik
704   464287572    IOO       IOO  BBG000DWS6F4        ISHARES GLOBAL 100 ETF     no_cik
705   464287614    IWF       IWF  BBG000BTR7Z0   ISHARES RUSSELL 1000 GROWTH     no_cik
706   464287648    IWO       IWO  BBG000C17LW4   ISHARES RUSSELL 2000 GROWTH     no_cik
707   464287655    IWM       IWM  BBG000CGC9C4      ISHARES RUSSELL 2000 ETF     no_cik
708   464287671   IUSG      IUSG  BBG000C18HW2  ISHARES CORE S&P U.S. GROWTH     no_cik
709   464288240   ACWX      ACWX  BBG000TH7DF8   ISHARES MSCI ACWI EX US ETF     no_cik
710   464288257   ACWI      ACWI  BBG000TH6VB3         ISHARES MSCI ACWI ETF     no_cik
711   464288513    HYG       HYG  BBG000R2T3H9  ISHR IBX USD HIYLD CB ETF-UI     no_cik
712   46429B671   MCHI      MCHI  BBG001LRJJH4        ISHARES MSCI CHINA ETF     no_cik
713   46434G772    EWT       EWT  BBG000CJLQ12       ISHARES MSCI TAIWAN ETF     no_cik
714   46435U853   USHY      USHY  BBG00J2DRZT9  ISHARES BROAD USD HIGH YIELD     no_cik
715   46436E718   SGOV      SGOV  BBG00TZR7XN3  ISHARES 0-3 MONTH TREASURY B     no_cik
720   46641Q654   JMST      JMST  BBG00M8D23F9   JPM ULTRA-SHORT MUNI INCOME     no_cik
1146  78468R663    BIL       BIL  BBG000RFQSH8    SS SPDR BB 1-3M T-BILL ETF     no_cik
1186  82669G104   SBNY      SBNY  BBG000M6TR37                SIGNATURE BANK     no_cik
1291  887432334   TPIF      TPIF  BBG00QXSPRP0         TIMOTHY PLAN INTL ETF     no_cik
1292  887432359   TPLC      TPLC  BBG00P1J0XV4    TIMOTHY PLN US LRG/MID CAP     no_cik
1311  89834G562   JGRW      JGRW  BBG01P7FWPV7     JENSEN QUALITY GROWTH ETF     no_cik
1351  922042742     VT        VT  BBG000GM5FZ6    VANGUARD TOT WORLD STK ETF     no_cik
1352  92206C680   VONG      VONG  BBG0016LBV85  VANGUARD RUSSELL 1000 GROWTH     no_cik
1358  922908363    VOO       VOO  BBG0015VYNT4          VANGUARD S&P 500 ETF     no_cik
1359  922908512    VOE       VOE  BBG000Q1ZR82  VNGRD MRNGSTR MD-CAP VAL ETF     no_cik
1360  922908629     VO        VO  BBG000HX76S7  VNGRD MRNGSTR MD-CAP ETF-USD     no_cik
1361  922908736    VUG       VUG  BBG000HT2CB6  VANGUARD MRNGSTAR GR ETF-SUI     no_cik
1362  922908769    VTI       VTI  BBG000HR9779  VG MORNINGSTAR TS MKT ETF-US     no_cik
```

### no_match weight per book (entity × period), all 140 books

Weights per Convention 4.5, by `sec_id`, from the Section 1 books joined to SECURITY_MAP:

```
entity          akre   jensen    polen      ivv      iwf
period_date
2019-09-30  0.031626 0.098287 0.058420 0.087346 0.062638
2019-12-31  0.040312 0.102235 0.056969 0.079104 0.054814
2020-03-31  0.043155 0.086222 0.053864 0.065977 0.046097
2020-06-30  0.043307 0.049077 0.053858 0.056395 0.041190
2020-09-30  0.048245 0.047825 0.056896 0.052903 0.038058
2020-12-31  0.054871 0.047252 0.059181 0.056611 0.038722
2021-03-31  0.058245 0.048865 0.061865 0.058232 0.038275
2021-06-30  0.059374 0.116654 0.058887 0.056581 0.034832
2021-09-30  0.059950 0.045705 0.058193 0.049293 0.029891
2021-12-31  0.065264 0.047881 0.065737 0.046616 0.027095
2022-03-31  0.070049 0.045246 0.058503 0.046187 0.023160
2022-06-30  0.053842 0.047794 0.062559 0.047498 0.030497
2022-09-30  0.053376 0.046457 0.064010 0.047206 0.047147
2022-12-31  0.004941 0.050494 0.066064 0.048848 0.044049
2023-03-31  0.005423 0.057183 0.061499 0.041687 0.041773
2023-06-30  0.006156 0.058699 0.062376 0.038815 0.032659
2023-09-30  0.007179 0.064492 0.062413 0.039951 0.033438
2023-12-31  0.006497 0.066002 0.054948 0.034574 0.029398
2024-03-31  0.006609 0.065642 0.059274 0.034350 0.026791
2024-06-30  0.005165 0.061859 0.054512 0.032624 0.024400
2024-09-30  0.002226 0.069365 0.058923 0.029549 0.017941
2024-12-31  0.001340 0.074188 0.055091 0.020305 0.009542
2025-03-31  0.000854 0.065050 0.085174 0.021968 0.010750
2025-06-30  0.001129 0.048287 0.069790 0.018329 0.018300
2025-09-30  0.001765 0.011285 0.058370 0.015327 0.017261
2025-12-31  0.001904 0.005100 0.056480 0.014476 0.016732
2026-03-31  0.003010 0.005285 0.058047 0.018673 0.016461
2026-06-30  0.004202 0.004810 0.017345 0.010765 0.015181

largest per entity:
             max      idxmax
entity
akre    0.070049  2022-03-31
jensen  0.116654  2021-06-30
polen   0.085174  2025-03-31
ivv     0.087346  2019-09-30
iwf     0.062638  2019-09-30

books with no_match weight > 0.05, per entity:
   entity  n_books
0    akre        8
1  jensen       14
2   polen       27
3     ivv        8
4     iwf        2
```

### 10 largest no_match offenders, by maximum weight across books

```
   sec_id id_type                      name  max_weight entity_of_max period_of_max  n_periods          held_by
G1151C101   cusip     Accenture plc Class A    0.072669        jensen    2024-12-31         28 jensen;polen;iwf
38259P508   cusip Alphabet Inc Cap Stk Cl A    0.069194        jensen    2021-06-30          1           jensen
913017109   cusip  United Technologies Corp    0.058794        jensen    2019-12-31          3       jensen;ivv
112585104   cusip BROOKFIELD ASSET MGMT INC    0.051406          akre    2022-03-31         13             akre
G0403H108   cusip                   AON PLC    0.037693         polen    2025-03-31         24 jensen;polen;iwf
03662Q105   cusip                 ANSYS INC    0.014991          akre    2020-12-31         24     akre;ivv;iwf
30231G102   cusip         Exxon Mobil Corp.    0.014137           ivv    2022-12-31         28              ivv
G4705A100   cusip                  ICON PLC    0.009100         polen    2023-06-30         26        polen;iwf
25401T603   cusip   DIGITALBRIDGE GROUP INC    0.007179          akre    2023-09-30         11             akre
25401T108   cusip   DIGITALBRIDGE GROUP INC    0.006410          akre    2022-06-30          5             akre
```

To see why live names such as Exxon fail, a one-off shell command (not repo code, nothing committed) sent the same CUSIPs to OpenFIGI with and without `exchCode`:

```
with "exchCode": "US"
30231G102 {"warning": "No identifier found."}
38259P508 {"warning": "No identifier found."}
G1151C101 {"warning": "No identifier found."}
438516106 {"warning": "No identifier found."}
000360206 {"data": [{"figi": "BBG000C2LZP3", "name": "AAON INC", "ticker": "AAON", "exchCode": "US", ...

without exchCode
30231G102 {"data": [{"figi": "BBG00B8TC1V3", "name": "EXXON MOBIL CORP", "ticker": "EXMOC", "exchCode": "CP", ...
38259P508 {"warning": "No identifier found."}
G1151C101 {"warning": "No identifier found."}
438516106 {"data": [{"figi": "BBG00QFYDC91", "name": "HONEYWELL INTERNATIONAL INC", "ticker": "HONGBP", "exchCode": "X1", ...
US30231G1022 {"data": [{"figi": "BBG00B8TC1V3", "name": "EXXON MOBIL CORP", "ticker": "EXMOC", "exchCode": "CP", ...
```

So there are 2 different failures. For Exxon and Honeywell, OpenFIGI knows the CUSIP but returns no US line for it. For Accenture's CUSIP and Google's pre-2015 CUSIP `38259P508`, it has nothing at all.

### 2.3 price panel and missing.csv

```
shape (2723, 1265), first 2015-12-01, last 2026-09-30, index dtype datetime64[ms], columns sorted True, dtypes {'float64'}

missing.csv:
  yf_ticker    sec_ids
0       CMA  200340107
1      CTRA  127097103

yf_tickers in SECURITY_MAP: 1267; in panel 1265; missing 2
```

The panel was pulled in 26 batches of 50. No batch raised. NAV first and last dates cannot be given: `nav_adjclose.csv` was not written (the stop).

### 2.2 and 2.3 French files

The last French month is 2026-08, so Section D's French condition (files ending before 2026-06) is not met:

```
ff5_monthly.csv: header ',Mkt-RF,SMB,HML,RMW,CMA,RF', first '196307,   -0.39,   -0.48,   -0.84,    0.64,   -1.15,    0.27', last '202608,    2.56,   -0.53,   -3.54,   -4.08,   -2.01,    0.29', 758 months
mom_monthly.csv: header ',Mom', first '192701,   0.57', last '202608,  -5.70', 1196 months
```

### Test prints: FF12 known codes, French March 2020 in percent and in decimals

```
{3571: 'BusEq', 2834: 'Hlth', 6021: 'Money', 1311: 'Enrgy', 4911: 'Utils', 9999: 'Other'}
......raw file, percent:
{'Mkt-RF': -13.35, 'SMB': -8.18, 'HML': -13.83, 'RMW': -1.61, 'CMA': 1.19, 'RF': 0.12, 'Mom': 8.2}
loader, decimal:
{'mkt': -0.1335, 'smb': -0.0818, 'hml': -0.1383, 'rmw': -0.0161, 'cma': 0.011899999999999999, 'umd': 0.08199999999999999, 'rf': 0.0012}
..
8 passed, 1 warning in 3.96s
```

`test_ff12_ranges_land_in_one_industry` found no SIC from 0100 to 9999 in 2 ranges, so the overlap stop in C 2.2 did not trigger.

### MANIFEST.json entries added in Section 2

```
{
  "edgar": "2026-10-02T18:11:25Z",
  "figi": "2026-10-02T21:10:16Z",
  "french": "2026-10-02T21:15:47Z",
  "prices": "2026-10-02T21:21:42Z",
  "sec": "2026-10-02T21:15:13Z"
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
  "french/Siccodes12.txt": "55b51d1dc6939a570cd866824e9d49a9b16c0ad6247286b676aca25af8c78409",
  "french/ff5_monthly.csv": "9b221d2a3d2a803b691e6aa7b3f3b6231f53de98c97b078bd10849bea2f3c1c2",
  "french/mom_monthly.csv": "fd793e12da4b6f48d2b5e40de29c6763f4067a5d7871f65c6028ce7af6bf2f20",
  "openfigi/mapping.csv": "1a35f73753950c0d6b1847a0ea13da14ea444dc8b446ef8c7c18cbfe18e630de",
  "prices/adjclose.parquet": "248c6504d891a5122dc26962351247750ac7f215e2759b4cd745f1733c6c21a3",
  "prices/missing.csv": "a2f64d477736dfded26a63663a61aabca4a32d8364e1d0e2c06686028473756c",
  "sec/company_tickers.json": "9058f1e002140b38df0001c64c6f0d98657e177359d2f2879ad92a30d1eee9ee",
  "sec/sic.csv": "89831db54463bc536029bec9c78daeb1b89d6ecb2a07e1e5dce3c63a7509374b"
}
{
  "french/ff5_monthly.csv": 758,
  "french/mom_monthly.csv": 1196,
  "openfigi/mapping.csv": 1622,
  "prices/missing.csv": 2,
  "sec/sic.csv": 1221
}
```

The `prices` manifest entry was written after the stage stopped, by calling `update_manifest("prices")`, so that `test_manifest_hashes_match_committed_files` covers the 2 committed price files.

## Tests run

`pytest -p socket --disable-socket -q`:

```
..................................                                       [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\Utkarsh\10. Quant Projects\6) Attribution Engine On Real Holdings\repo-clone\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
34 passed, 1 warning in 4.31s
```

26 earlier tests, plus 6 in `tests/test_mapping.py` and 2 in `tests/test_data_loaders.py`.

## Fresh-clone check

Per instruction 02, A answer 5: the 3 step commits were pushed first (`7225d13..c233354`), then GitHub was cloned into `C:\t\s2`. Install output is trimmed to its last lines:

```
$ git clone -q https://github.com/uty101/Attribution-Engine-On-Real-Holdings.git /c/t/s2
$ git log --oneline -1
c233354 step 2.3: prices and French loaders (stopped: yfinance has no AKRIX data)
$ uv venv --python 3.12
Using CPython 3.12.13
Creating virtual environment at: .venv
Activate with: .venv\Scripts\activate
$ uv pip install -r requirements-lock.txt
 + wrapt==2.5.0
 + yfinance==1.7.0
$ uv pip install -e . --no-deps
 + attrib==0.0.0 (from file:///C:/t/s2)
$ .venv/Scripts/python.exe -m pytest -p socket --disable-socket -q
..................................                                       [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\t\s2\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
34 passed, 1 warning in 10.69s
$ .venv/Scripts/python.exe scripts/run_all.py --section 2
section 1: all checks passed
section 2: all checks passed
exit 0
953ff419314dad70bb3675e855d1c4f7fdf592a861c4c05d431d79d01d79008a *outputs/tables/coverage.csv
10b349a491e8c88347e37519156787147a1085fb1d4bba83f96f10f064bbe399 *data/processed/security_map.csv
10b349a491e8c88347e37519156787147a1085fb1d4bba83f96f10f064bbe399 */c/Utkarsh/10. Quant Projects/6) Attribution Engine On Real Holdings/repo-clone/data/processed/security_map.csv
```

The clone's `security_map.csv` matches the local one byte for byte. `coverage.csv` keeps its Section 1 hash, since 2.5 did not run. `git status --short` in the clone printed nothing.

## Runtime per step

- 2.1: `--stage figi`, 7 min 48 s, 0 retries. A first run had been stopped at 1410 of 1622 by the 30-minute limit on background tasks in this session, before anything was written. That run's progress lines came in far more slowly than the rerun's, and the cause was not found. `--stage sec`, 4 min 47 s.
- 2.2: `--stage french`, a few seconds. `run_all.py --section 2`, about 5 s.
- 2.3: `--stage prices`, 26 batches plus the NAV call that stopped, 3 min 46 s.

## Deviations from PLAN.md

- Precedence: instruction 02 replaces the PLAN 2.1 to 2.2 key (`cusip`) with `sec_id` and adds `id_type`, `figi`, the `cik` override kind, and `nocik_top.csv`.
- 2.1: the OpenFIGI client is `OpenFigiClient` in `scripts/pull_data.py`, not in `attrib/`. It is the only caller (rule 8), and `EdgarClient` only sends GET. Each job carries `"exchCode": "US"`, as in PLAN 2.1, for both ID types. `result_rank` starts at 1.
- 2.1: `sic.csv` covers the CIKs of every OpenFIGI equity result's ticker, plus override `ticker` and `cik` values. Since every `sec_id` returned at most 1 result, this equals the set reached by the selection rule.
- 2.1: `pull_data.py` imports `run_all.fund_books` and `run_all.benchmark_books`, so the OpenFIGI universe is rebuilt from `data/raw/` and not read from `data/processed/`.
- 2.2: in SECURITY_MAP, `ff12` is blank for `no_match` rows (they are the Unmapped bucket) and `Other` for `no_cik` and `no_sic`. A ticker matching more than 1 CIK raises; none does. An override `cik` row applies only to a row that has a ticker.
- 2.2: `--stage french` keeps each monthly block's lines as filed (header and `YYYYMM` rows, values with French's padding), with LF line endings. The first header cell is blank, as French has it. It sends its own User-Agent, not `SEC_USER_AGENT`, so the owner's email is not sent outside EDGAR.
- 2.3: the price panel's index dtype is `datetime64[ms]`, as yfinance returns it.
- 2.3: the `prices` manifest entry was written after the stop (see Evidence).

## Not verified

- That the Akre Focus Fund converted into the AKRE ETF. This rests only on yfinance's `quoteType` and `fundInceptionDate`. No prospectus or filing was read.
- The 2 OpenFIGI and yfinance probes in Evidence were one-off shell commands, outside `pull_data.py`. Their outputs are pasted but not committed.
- No OpenFIGI ticker or SEC SIC was checked by hand against a third source.
- Steps 2.4 and 2.5 did not run, so QUARTERS, the coverage mapping columns and the 4 review lists do not exist.

## Open questions

1. **OpenFIGI `no_match` above 5% of book value (Section D, reported as instructed).** 59 of 140 books are above 5%: Akre 8, Jensen 14, Polen 27, IVV 8, IWF 2. The highest is Jensen 2021-06-30 at 11.67%. The 10 largest offenders are listed above. Accenture `G1151C101` (Jensen, Polen, IWF on all 28 dates) and Aon `G0403H108` stand out: OpenFIGI has nothing for these live CUSIPs. For Exxon `30231G102` it returns lines on other exchanges but none on `US`. `38259P508` is Google's pre-2015 CUSIP, filed by Jensen for 1 period. Two ways to fix this:
   - (a) `ticker` overrides from the reviewer for the top offenders, the route instruction 03 already plans;
   - (b) a second OpenFIGI pass for `no_match` IDs without `exchCode`, keeping the first result whose `exchCode` is `US`, `UN`, `UW` or another US venue the reviewer lists.
2. **AKRIX has no yfinance data (the stop).** OPEN-31 in `decisions/OPEN.md`:
   - (a) a non-yfinance NAV source for AKRIX, spliced onto AKRE after the conversion;
   - (b) Akre reported as failed for having no NAV data.
3. **`unpriced_weight` and `other_nosic_weight` can overlap** (step 2.5, not reached). This is OPEN-32. CMA and CTRA are both `no_cik` and have no prices.
4. **Exchange-traded funds in the 13F books.** 29 of the 34 `no_cik` rows are ETFs (IVV, IWF, VOO, SGOV and others), mostly in Polen's book. SPY is the only `no_sic` row. Under Convention 4.6 they land in Other. They are reported here, not judged.

## Files changed

- Step 2.1: `scripts/pull_data.py`, `data/raw/openfigi/mapping.csv`, `data/raw/sec/company_tickers.json`, `data/raw/sec/sic.csv`, `data/raw/MANIFEST.json`
- Step 2.2: `attrib/mapping.py`, `tests/test_mapping.py`, `scripts/pull_data.py`, `scripts/run_all.py`, `data/manual/overrides.csv`, `data/raw/french/` (3 files), `data/raw/MANIFEST.json`
- Step 2.3: `scripts/pull_data.py`, `attrib/returns.py`, `attrib/factors.py`, `tests/test_data_loaders.py`, `data/raw/prices/adjclose.parquet`, `data/raw/prices/missing.csv`, `data/raw/MANIFEST.json`
- Review: `review/section_2.md`, `decisions/OPEN.md`, `instructions/02_section_2.status.md`

## Reviewer reads

1. `instructions/02_section_2.status.md`
2. This file: Section, then "The stop", then Open questions
3. `decisions/OPEN.md` (OPEN-31, OPEN-32)
4. `attrib/mapping.py` (`build_security_map`)
5. `scripts/pull_data.py` (`stage_figi`, `stage_sec`, `stage_prices`)
