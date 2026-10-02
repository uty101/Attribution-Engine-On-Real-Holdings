# Review — Section 1

## Section

Section 1, Foundation and EDGAR holdings, **completed**. Session 1 built steps 1.0 to 1.6 and stopped at 1.6 (`e5dba91`) because the IVV and IWF N-PORT books for 2019-03-31 and 2019-06-30 do not exist. Session 1b (`instructions/01b_section_1_completion.md`) applied the reviewer's decisions and fixes in steps 1.2b, 1.4b, 1.5b and 1.6b:

- H now starts at 2019-09-30, so there are 28 holdings dates.
- ISIN-only benchmark rows are kept.
- `NPORT-P/A` is accepted.
- CSVs are written with `%.17g`.
- `EdgarClient` now has a timeout.

`python scripts/run_all.py --section 1` passes every check on all 140 books. This file replaces the session 1 review and covers all of Section 1.

## Steps completed

- 1.0 apply session 0 decisions — `50a2892`
- 1.1 `attrib/config.py`, `tests/test_config.py` — `bf10c0e`
- 1.2 `EdgarClient`, `tests/test_edgar_client.py` — `4b1e319`
- 1.3 13F parsing, `--stage fixtures`, 2 Akre fixtures, `tests/test_edgar_13f.py` — `49435ea`
- 1.4 N-PORT parsing, IVV fixture, `tests/test_edgar_nport.py` — `2eb360a`
- 1.5 `--stage edgar`, `data/raw/` and `MANIFEST.json`, `tests/test_manifest.py` — `99ca50f`
- 1.6 `scripts/run_all.py --section 1`, holdings books, `outputs/tables/coverage.csv`; stopped on the Section 3.3 check — `15809d3`
- 1.2b `[edgar] timeout_s = 30`, `timeout` in the `EdgarClient` signature, retry on `requests.Timeout` and `requests.ConnectionError`, 2 new tests — `62f5b3d`
- 1.4b HOLDINGS gains `isin` and `sec_id`, aggregation by `sec_id`, ISIN-only EC/NS rows kept, `NPORT-P/A` listed, `coverage.csv` gains `isin_only_weight`, 3 new tests and 2 new assertions — `d46da92`
- 1.5b both CSV writers on `%.17g`, `--stage edgar` rerun, `MANIFEST.json` updated — `2ab736d`
- 1.6b `first_holdings_date = "2019-09-30"`, `run_all.py --section 1` rerun (all checks pass, 140 coverage rows), `CLAUDE.md` amendments 5 to 10 — `fb2eee2`

## Evidence

### Section 1 run on H = 2019-09-30 to 2026-06-30

`python scripts/run_all.py --section 1`, exit code 0:

```
section 1: all checks passed
```

The checks are:

- every date in H has a book for all 5 entities;
- the median implied price of every 13F book lies in [1, 5000];
- the kept `pctVal` of every N-PORT book sums to within [95, 101];
- no N-PORT book has a period outside H.

A second run left `coverage.csv` and the 5 `data/processed/holdings_{id}.csv` files byte-identical (sha256 compared). The same files regenerated in the fresh clone also have identical sha256:

```
953ff419314dad70bb3675e855d1c4f7fdf592a861c4c05d431d79d01d79008a  outputs/tables/coverage.csv
a7762350d70ddad269fcaa8b32b9a94407bf8d0897683dc4c1b07a3b140660f1  data/processed/holdings_akre.csv
9dc17b5017f2dfb4d20b9ad5a2baa825e90b6fa874dfc96bc77ff62ba44dc55c  data/processed/holdings_ivv.csv
9f93bf5830e12551998905bab60def5207582114e1f35958e919d19b8ddeb09e  data/processed/holdings_iwf.csv
803579934fe4eda19472400713b96ba9596e3ce6a5afd9799a6db18397f25576  data/processed/holdings_jensen.csv
7bf36f37a69a6abf8625ebe5152782e0c771231e360b6df0a956965340de51dc  data/processed/holdings_polen.csv
```

### The session 1 stop, for the record

The session 1 run on 30 dates failed only on these 4 books. 01b Section B decided option (a): H starts at 2019-09-30.

```
ivv: no NPORT-P for 2019-03-31
ivv: no NPORT-P for 2019-06-30
iwf: no NPORT-P for 2019-03-31
iwf: no NPORT-P for 2019-06-30
```

### Test prints: 1.2 and 1.2b fake-clock sleeps and timeout, 1.3 median implied prices, 1.4 and 1.4b fixture header and shape

`pytest -p socket --disable-socket -q -s tests/test_edgar_13f.py tests/test_edgar_nport.py tests/test_edgar_client.py`:

```
......2022-06-30_0001112520-22-000013.xml: median implied price 165.0400651465798
2023-06-30_0001112520-23-000013.xml: median implied price 209.98499260891637
...{'seriesId': 'S000004310', 'repPdDate': '2023-06-30'}
..kept rows 503, kept pctVal sum np.float64(99.72529541256701)
kept rows with an ISIN sec_id 25, their pctVal sum np.float64(3.153971924956)
.....recorded sleeps: [0.2, 0.2]
.recorded sleeps: [2.0, 4.0]
.recorded sleeps: [2.0, 4.0, 8.0]
.recorded timeout: [30]
.recorded sleeps: [2.0]
.
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\Utkarsh\10. Quant Projects\6) Attribution Engine On Real Holdings\repo-clone\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
21 passed, 1 warning in 0.71s
```

The IVV 2023-06-30 fixture has 25 kept rows with an ISIN `sec_id`, and their `pctVal` sums to 3.153971924956. The reviewer measured 25 rows and 3.154. `test_ivv_fixture_shape` still counts 503 kept rows, as in session 1: the 25 rows always passed the EC/NS filter and were lost only later, at the CUSIP check in `aggregate_book` (see Deviations, 1.4b).

### 1.3 fixtures (`tests/fixtures/FIXTURES.json`)

```
{
  "13f/akre/2022-06-30_0001112520-22-000013.xml": {
    "sha256": "4c071fd59e1f912ca5bd1cc4a6ac4de3f08325862aa6e7f1af63ea960acb562c",
    "url": "https://www.sec.gov/Archives/edgar/data/1112520/000111252022000013/infotable.xml"
  },
  "13f/akre/2023-06-30_0001112520-23-000013.xml": {
    "sha256": "439c2e43ef797906c769c2fcbac7f298254d09d9a41aa4870211a5a0a9c5d305",
    "url": "https://www.sec.gov/Archives/edgar/data/1112520/000111252023000013/infotable.xml"
  },
  "nport/ivv_2023-06-30_0001752724-23-191503.xml": {
    "sha256": "880c14e3a7f46ae08e7953d41d5809178bd9bcae13c5461f9bb71a0f944543eb",
    "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272423191503/primary_doc.xml"
  }
}
```

### H: 28 holdings dates

```
2019-09-30, 2019-12-31, 2020-03-31, 2020-06-30, 2020-09-30, 2020-12-31, 2021-03-31, 2021-06-30, 2021-09-30, 2021-12-31, 2022-03-31, 2022-06-30, 2022-09-30, 2022-12-31, 2023-03-31, 2023-06-30, 2023-09-30, 2023-12-31, 2024-03-31, 2024-06-30, 2024-09-30, 2024-12-31, 2025-03-31, 2025-06-30, 2025-09-30, 2025-12-31, 2026-03-31, 2026-06-30
```

### Section E item 2 data/raw/sec/series_resolved.csv

```
  entity ticker      cik   series_id    class_id
0    ivv    IVV  1100663  S000004310  C000012040
1    iwf    IWF  1100663  S000004346  C000012076
```

### Section E item 3 FILINGS_13F akre: period_date in H, plus every /A row (50 rows of 125)

```
    entity      cik             accession      form filing_date period_date amendment_type infotable_name
3     akre  1112520  0001112520-01-500011  13F-HR/A  2001-08-13  2001-03-31                              
4     akre  1112520  0001112520-01-500012  13F-HR/A  2001-08-13  2001-06-30                              
5     akre  1112520  0001112520-01-500013  13F-HR/A  2001-08-23  2001-06-30                              
6     akre  1112520  0001112520-01-500014  13F-HR/A  2001-08-23  2001-06-30                              
7     akre  1112520  0001112520-01-500015  13F-HR/A  2001-08-23  2001-06-30                              
8     akre  1112520  0001112520-01-500016  13F-HR/A  2001-08-28  2001-06-30                              
13    akre  1112520  0001112520-02-000008  13F-HR/A  2002-08-23  2002-06-30                              
21    akre  1112520  0001112520-04-000012  13F-HR/A  2004-04-22  2004-03-31                              
37    akre  1112520  0001112520-08-000019  13F-HR/A  2008-02-14  2007-12-31                              
38    akre  1112520  0001112520-08-000020  13F-HR/A  2008-02-14  2007-12-31                              
49    akre  1112520  0001112520-10-000021  13F-HR/A  2010-08-26  2010-03-31                              
55    akre  1112520  0001112520-11-000024  13F-HR/A  2011-11-25  2011-09-30                              
59    akre  1112520  0001112520-12-000014  13F-HR/A  2012-08-23  2012-03-31                              
60    akre  1112520  0001112520-12-000016  13F-HR/A  2012-10-02  2012-06-30                              
62    akre  1112520  0001112520-12-000020  13F-HR/A  2012-11-15  2012-03-31                              
65    akre  1112520  0000919574-13-004202  13F-HR/A  2013-07-29  2013-03-31   NEW HOLDINGS  infotable.xml
69    akre  1112520  0001112520-14-000011  13F-HR/A  2014-02-14  2013-12-31    RESTATEMENT  infotable.xml
82    akre  1112520  0001112520-17-000015  13F-HR/A  2017-05-09  2016-12-31   NEW HOLDINGS  infotable.xml
85    akre  1112520  0001112520-17-000026  13F-HR/A  2017-08-18  2016-06-30    RESTATEMENT  infotable.xml
86    akre  1112520  0001112520-17-000028  13F-HR/A  2017-08-29  2015-03-31    RESTATEMENT  infotable.xml
95    akre  1112520  0001112520-19-000024    13F-HR  2019-11-13  2019-09-30                 infotable.xml
96    akre  1112520  0001112520-20-000010    13F-HR  2020-02-14  2019-12-31                 infotable.xml
97    akre  1112520  0001112520-20-000016    13F-HR  2020-05-11  2020-03-31                 infotable.xml
98    akre  1112520  0001112520-20-000022    13F-HR  2020-08-11  2020-06-30                 infotable.xml
99    akre  1112520  0001112520-20-000024    13F-HR  2020-11-13  2020-09-30                 infotable.xml
100   akre  1112520  0001112520-21-000003    13F-HR  2021-02-10  2020-12-31                 infotable.xml
101   akre  1112520  0001112520-21-000012    13F-HR  2021-05-13  2021-03-31                 infotable.xml
102   akre  1112520  0001112520-21-000016  13F-HR/A  2021-07-09  2021-03-31    RESTATEMENT  infotable.xml
103   akre  1112520  0001112520-21-000020    13F-HR  2021-08-13  2021-06-30                 infotable.xml
104   akre  1112520  0001112520-21-000023    13F-HR  2021-11-12  2021-09-30                 infotable.xml
105   akre  1112520  0001112520-22-000005    13F-HR  2022-02-11  2021-12-31                 infotable.xml
106   akre  1112520  0001112520-22-000009    13F-HR  2022-05-13  2022-03-31                 infotable.xml
107   akre  1112520  0001112520-22-000013    13F-HR  2022-08-11  2022-06-30                 infotable.xml
108   akre  1112520  0001112520-22-000015    13F-HR  2022-11-14  2022-09-30                 infotable.xml
109   akre  1112520  0001112520-23-000006    13F-HR  2023-02-13  2022-12-31                 infotable.xml
110   akre  1112520  0001112520-23-000008    13F-HR  2023-05-12  2023-03-31                 infotable.xml
111   akre  1112520  0001112520-23-000013    13F-HR  2023-08-11  2023-06-30                 infotable.xml
112   akre  1112520  0001112520-23-000019    13F-HR  2023-11-13  2023-09-30                 infotable.xml
113   akre  1112520  0001112520-24-000006    13F-HR  2024-02-09  2023-12-31                 infotable.xml
114   akre  1112520  0001112520-24-000010    13F-HR  2024-05-13  2024-03-31                 infotable.xml
115   akre  1112520  0001112520-24-000012  13F-HR/A  2024-05-23  2024-03-31   NEW HOLDINGS  infotable.xml
116   akre  1112520  0001112520-24-000014    13F-HR  2024-08-13  2024-06-30                 infotable.xml
117   akre  1112520  0001112520-24-000025    13F-HR  2024-11-13  2024-09-30                 infotable.xml
118   akre  1112520  0001112520-25-000003    13F-HR  2025-02-13  2024-12-31                 infotable.xml
119   akre  1112520  0001112520-25-000015    13F-HR  2025-05-13  2025-03-31                 infotable.xml
120   akre  1112520  0001112520-25-000019    13F-HR  2025-08-14  2025-06-30                 infotable.xml
121   akre  1112520  0001112520-25-000029    13F-HR  2025-11-13  2025-09-30                 infotable.xml
122   akre  1112520  0001112520-26-000008    13F-HR  2026-02-13  2025-12-31                 infotable.xml
123   akre  1112520  0001112520-26-000009    13F-HR  2026-05-14  2026-03-31                 infotable.xml
124   akre  1112520  0001112520-26-000014    13F-HR  2026-08-14  2026-06-30                 infotable.xml
```

### Section E item 3 FILINGS_13F jensen: period_date in H, plus every /A row (35 rows of 117)

```
     entity      cik             accession      form filing_date period_date amendment_type infotable_name
65   jensen  1106129  0001171200-15-000022  13F-HR/A  2015-07-29  2015-03-31    RESTATEMENT  infotable.xml
68   jensen  1106129  0001171200-15-000057  13F-HR/A  2015-11-12  2013-09-30    RESTATEMENT  infotable.xml
69   jensen  1106129  0001171200-15-000058  13F-HR/A  2015-11-12  2014-06-30    RESTATEMENT  infotable.xml
70   jensen  1106129  0001171200-15-000059  13F-HR/A  2015-11-12  2014-09-30    RESTATEMENT  infotable.xml
71   jensen  1106129  0001171200-15-000060  13F-HR/A  2015-11-12  2014-12-31    RESTATEMENT  infotable.xml
77   jensen  1106129  0001171200-17-000072  13F-HR/A  2017-02-14  2016-12-31    RESTATEMENT  infotable.xml
88   jensen  1106129  0001171200-19-000366    13F-HR  2019-11-12  2019-09-30                 infotable.xml
89   jensen  1106129  0001171200-20-000061    13F-HR  2020-02-07  2019-12-31                 infotable.xml
90   jensen  1106129  0001171200-20-000338    13F-HR  2020-05-07  2020-03-31                 infotable.xml
91   jensen  1106129  0001171200-20-000521    13F-HR  2020-08-10  2020-06-30                 infotable.xml
92   jensen  1106129  0001171200-20-000622    13F-HR  2020-11-03  2020-09-30                 infotable.xml
93   jensen  1106129  0001171200-21-000057    13F-HR  2021-02-09  2020-12-31                 infotable.xml
94   jensen  1106129  0001171200-21-000236    13F-HR  2021-05-06  2021-03-31                 infotable.xml
95   jensen  1106129  0001171200-21-000290    13F-HR  2021-08-05  2021-06-30                 infotable.xml
96   jensen  1106129  0001171200-21-000388    13F-HR  2021-11-12  2021-09-30                 infotable.xml
97   jensen  1106129  0001171200-22-000037    13F-HR  2022-02-14  2021-12-31                 infotable.xml
98   jensen  1106129  0001171200-22-000245    13F-HR  2022-05-10  2022-03-31                 infotable.xml
99   jensen  1106129  0001171200-22-000293    13F-HR  2022-08-12  2022-06-30                 infotable.xml
100  jensen  1106129  0001171200-22-000347    13F-HR  2022-11-07  2022-09-30                 infotable.xml
101  jensen  1106129  0001171200-23-000057    13F-HR  2023-02-08  2022-12-31                 infotable.xml
102  jensen  1106129  0001171200-23-000206  13F-HR/A  2023-04-05  2022-12-31    RESTATEMENT  infotable.xml
103  jensen  1106129  0001171200-23-000298    13F-HR  2023-05-08  2023-03-31                 infotable.xml
104  jensen  1106129  0001171200-23-000356    13F-HR  2023-08-07  2023-06-30                 infotable.xml
105  jensen  1106129  0001171200-23-000445    13F-HR  2023-11-07  2023-09-30                 infotable.xml
106  jensen  1106129  0001171200-24-000016    13F-HR  2024-02-12  2023-12-31                 infotable.xml
107  jensen  1106129  0001171200-24-000202    13F-HR  2024-05-07  2024-03-31                 infotable.xml
108  jensen  1106129  0001171200-24-000243    13F-HR  2024-08-05  2024-06-30                 infotable.xml
109  jensen  1106129  0001171200-24-000330    13F-HR  2024-11-04  2024-09-30                 infotable.xml
110  jensen  1106129  0001171200-25-000017    13F-HR  2025-02-10  2024-12-31                 infotable.xml
111  jensen  1106129  0001171200-25-000219    13F-HR  2025-05-09  2025-03-31                 infotable.xml
112  jensen  1106129  0001171200-25-000262    13F-HR  2025-08-08  2025-06-30                 infotable.xml
113  jensen  1106129  0001171200-25-000265    13F-HR  2025-11-06  2025-09-30                 infotable.xml
114  jensen  1106129  0001171200-26-000003    13F-HR  2026-02-11  2025-12-31                 infotable.xml
115  jensen  1106129  0001171200-26-000007    13F-HR  2026-05-05  2026-03-31                 infotable.xml
116  jensen  1106129  0001171200-26-000010    13F-HR  2026-08-07  2026-06-30                 infotable.xml
```

### Section E item 3 FILINGS_13F polen: period_date in H, plus every /A row (54 rows of 117)

```
    entity      cik             accession      form filing_date period_date amendment_type infotable_name
7    polen  1034524  0001034524-00-000017  13F-HR/A  2000-10-19  2000-09-30                              
8    polen  1034524  0001034524-00-000018  13F-HR/A  2000-10-20  2000-09-30                              
9    polen  1034524  0001034524-01-000001  13F-HR/A  2001-01-17  2000-12-31                              
28   polen  1034524  0001034524-05-000009  13F-HR/A  2005-08-29  2005-06-30                              
29   polen  1034524  0001034524-05-000010  13F-HR/A  2005-11-10  2005-09-30                              
30   polen  1034524  0001034524-06-000001  13F-HR/A  2006-02-08  2005-12-31                              
31   polen  1034524  0001034524-06-000002  13F-HR/A  2006-04-21  2006-03-31                              
32   polen  1034524  0001034524-06-000005  13F-HR/A  2006-07-19  2006-06-30                              
33   polen  1034524  0001034524-06-000008  13F-HR/A  2006-10-05  2006-09-30                              
34   polen  1034524  0001034524-06-000009  13F-HR/A  2006-10-06  2006-09-30                              
35   polen  1034524  0001034524-07-000001  13F-HR/A  2007-02-06  2006-12-29                              
36   polen  1034524  0001034524-07-000002  13F-HR/A  2007-04-19  2007-03-30                              
37   polen  1034524  0001034524-07-000003  13F-HR/A  2007-07-27  2007-06-30                              
38   polen  1034524  0001034524-07-000007  13F-HR/A  2007-10-29  2007-09-30                              
39   polen  1034524  0001034524-08-000001  13F-HR/A  2008-01-31  2007-12-31                              
40   polen  1034524  0001034524-08-000002  13F-HR/A  2008-04-30  2008-03-31                              
41   polen  1034524  0001034524-08-000003  13F-HR/A  2008-07-25  2008-06-30                              
42   polen  1034524  0001034524-08-000005  13F-HR/A  2008-11-07  2008-09-30                              
43   polen  1034524  0001034524-09-000001  13F-HR/A  2009-02-06  2008-12-31                              
44   polen  1034524  0001034524-09-000002  13F-HR/A  2009-05-11  2009-03-31                              
45   polen  1034524  0001034524-09-000003  13F-HR/A  2009-08-05  2009-06-30                              
46   polen  1034524  0001034524-09-000004  13F-HR/A  2009-11-10  2009-09-30                              
47   polen  1034524  0001034524-10-000001  13F-HR/A  2010-02-10  2009-12-31                              
86   polen  1034524  0001172661-19-002155    13F-HR  2019-11-12  2019-09-30                 infotable.xml
87   polen  1034524  0001172661-20-000333    13F-HR  2020-02-06  2019-12-31                 infotable.xml
88   polen  1034524  0001172661-20-001182    13F-HR  2020-05-11  2020-03-31                 infotable.xml
89   polen  1034524  0001172661-20-001647    13F-HR  2020-08-13  2020-06-30                 infotable.xml
90   polen  1034524  0001172661-20-002092    13F-HR  2020-11-12  2020-09-30                 infotable.xml
91   polen  1034524  0001172661-21-000318    13F-HR  2021-02-11  2020-12-31                 infotable.xml
92   polen  1034524  0001172661-21-001092    13F-HR  2021-05-12  2021-03-31                 infotable.xml
93   polen  1034524  0001172661-21-001640    13F-HR  2021-08-12  2021-06-30                 infotable.xml
94   polen  1034524  0001172661-21-002146    13F-HR  2021-11-10  2021-09-30                 infotable.xml
95   polen  1034524  0001172661-22-000331    13F-HR  2022-02-11  2021-12-31                 infotable.xml
96   polen  1034524  0001172661-22-001239    13F-HR  2022-05-12  2022-03-31                 infotable.xml
97   polen  1034524  0001172661-22-001764    13F-HR  2022-08-10  2022-06-30                 infotable.xml
98   polen  1034524  0001172661-22-002289    13F-HR  2022-11-04  2022-09-30                 infotable.xml
99   polen  1034524  0001172661-23-000805    13F-HR  2023-02-13  2022-12-31                 infotable.xml
100  polen  1034524  0001172661-23-002012    13F-HR  2023-05-11  2023-03-31                 infotable.xml
101  polen  1034524  0001172661-23-002916    13F-HR  2023-08-11  2023-06-30                 infotable.xml
102  polen  1034524  0001172661-23-003726    13F-HR  2023-11-13  2023-09-30                 infotable.xml
103  polen  1034524  0001172661-24-000776    13F-HR  2024-02-13  2023-12-31                 infotable.xml
104  polen  1034524  0001172661-24-001616  13F-HR/A  2024-02-20  2023-12-31    RESTATEMENT  infotable.xml
105  polen  1034524  0001172661-24-002148  13F-HR/A  2024-05-10  2023-12-31    RESTATEMENT  infotable.xml
106  polen  1034524  0001172661-24-002149    13F-HR  2024-05-10  2024-03-31                 infotable.xml
107  polen  1034524  0001172661-24-003233    13F-HR  2024-08-12  2024-06-30                 infotable.xml
108  polen  1034524  0001172661-24-004624    13F-HR  2024-11-13  2024-09-30                 infotable.xml
109  polen  1034524  0001172661-25-000622  13F-HR/A  2025-02-10  2024-09-30    RESTATEMENT  infotable.xml
110  polen  1034524  0001172661-25-000623    13F-HR  2025-02-10  2024-12-31                 infotable.xml
111  polen  1034524  0001172661-25-001713    13F-HR  2025-05-12  2025-03-31                 infotable.xml
112  polen  1034524  0001172661-25-003133    13F-HR  2025-08-13  2025-06-30                 infotable.xml
113  polen  1034524  0001172661-25-004691    13F-HR  2025-11-12  2025-09-30                 infotable.xml
114  polen  1034524  0001172661-26-000654    13F-HR  2026-02-12  2025-12-31                 infotable.xml
115  polen  1034524  0001172661-26-001911    13F-HR  2026-05-14  2026-03-31                 infotable.xml
116  polen  1034524  0001172661-26-003035    13F-HR  2026-08-04  2026-06-30                 infotable.xml
```

### Section E item 4 FILINGS_NPORT ivv: period_date in H (29 rows of 29)

```
   entity   series_id             accession filing_date period_date
0     ivv  S000004310  0001752724-19-177847  2019-11-25  2019-09-30
1     ivv  S000004310  0001752724-20-038725  2020-02-27  2019-12-31
2     ivv  S000004310  0001752724-20-112027  2020-06-01  2020-03-31
3     ivv  S000004310  0001752724-20-176909  2020-08-27  2020-06-30
4     ivv  S000004310  0001752724-20-247818  2020-11-25  2020-09-30
5     ivv  S000004310  0001752724-21-040719  2021-02-25  2020-12-31
6     ivv  S000004310  0001752724-21-116363  2021-05-27  2021-03-31
7     ivv  S000004310  0001752724-21-186201  2021-08-26  2021-06-30
8     ivv  S000004310  0001752724-21-255857  2021-11-24  2021-09-30
9     ivv  S000004310  0001752724-22-046281  2022-02-25  2021-12-31
10    ivv  S000004310  0001752724-22-122805  2022-05-26  2022-03-31
11    ivv  S000004310  0001752724-22-193652  2022-08-25  2022-06-30
12    ivv  S000004310  0001752724-22-268673  2022-11-28  2022-09-30
13    ivv  S000004310  0001752724-23-039243  2023-02-24  2022-12-31
14    ivv  S000004310  0001752724-23-123220  2023-05-26  2023-03-31
15    ivv  S000004310  0001752724-23-191503  2023-08-25  2023-06-30
16    ivv  S000004310  0001752724-23-264277  2023-11-22  2023-09-30
17    ivv  S000004310  0001752724-24-043113  2024-02-27  2023-12-31
18    ivv  S000004310  0001752724-24-123331  2024-05-28  2024-03-31
19    ivv  S000004310  0001752724-24-194289  2024-08-27  2024-06-30
20    ivv  S000004310  0001752724-24-269943  2024-11-26  2024-09-30
21    ivv  S000004310  0001752724-25-043800  2025-02-27  2024-12-31
22    ivv  S000004310  0001752724-25-119791  2025-05-27  2025-03-31
23    ivv  S000004310  0001752724-25-210389  2025-08-28  2025-06-30
24    ivv  S000004310  0002071691-25-007634  2025-11-26  2025-09-30
25    ivv  S000004310  0002071691-26-004238  2026-02-25  2025-12-31
26    ivv  S000004310  0002071691-26-012459  2026-05-28  2026-03-31
27    ivv  S000004310  0002071691-26-015790  2026-07-13  2025-09-30
28    ivv  S000004310  0002071691-26-019760  2026-08-25  2026-06-30
```

### Section E item 4 FILINGS_NPORT iwf: period_date in H (28 rows of 28)

```
   entity   series_id             accession filing_date period_date
0     iwf  S000004346  0001752724-19-177844  2019-11-25  2019-09-30
1     iwf  S000004346  0001752724-20-038663  2020-02-27  2019-12-31
2     iwf  S000004346  0001752724-20-112153  2020-06-01  2020-03-31
3     iwf  S000004346  0001752724-20-176978  2020-08-27  2020-06-30
4     iwf  S000004346  0001752724-20-247763  2020-11-25  2020-09-30
5     iwf  S000004346  0001752724-21-040696  2021-02-25  2020-12-31
6     iwf  S000004346  0001752724-21-116383  2021-05-27  2021-03-31
7     iwf  S000004346  0001752724-21-186226  2021-08-26  2021-06-30
8     iwf  S000004346  0001752724-21-255846  2021-11-24  2021-09-30
9     iwf  S000004346  0001752724-22-046298  2022-02-25  2021-12-31
10    iwf  S000004346  0001752724-22-122801  2022-05-26  2022-03-31
11    iwf  S000004346  0001752724-22-193669  2022-08-25  2022-06-30
12    iwf  S000004346  0001752724-22-269723  2022-11-28  2022-09-30
13    iwf  S000004346  0001752724-23-039553  2023-02-24  2022-12-31
14    iwf  S000004346  0001752724-23-114945  2023-05-24  2023-03-31
15    iwf  S000004346  0001752724-23-192397  2023-08-28  2023-06-30
16    iwf  S000004346  0001752724-23-265163  2023-11-24  2023-09-30
17    iwf  S000004346  0001752724-24-034941  2024-02-23  2023-12-31
18    iwf  S000004346  0001752724-24-118346  2024-05-24  2024-03-31
19    iwf  S000004346  0001752724-24-189692  2024-08-26  2024-06-30
20    iwf  S000004346  0001752724-24-268863  2024-11-26  2024-09-30
21    iwf  S000004346  0001752724-25-034056  2025-02-24  2024-12-31
22    iwf  S000004346  0001752724-25-118601  2025-05-23  2025-03-31
23    iwf  S000004346  0001752724-25-204350  2025-08-26  2025-06-30
24    iwf  S000004346  0001004726-25-002059  2025-11-25  2025-09-30
25    iwf  S000004346  0001004726-26-000787  2026-02-23  2025-12-31
26    iwf  S000004346  0001004726-26-003755  2026-05-22  2026-03-31
27    iwf  S000004346  0001004726-26-007047  2026-08-24  2026-06-30
```

### Section E item 5 outputs/tables/coverage.csv (140 rows)

```
     entity period_date filing_date lag_days n_rows_raw n_rows_kept   dropped_value_usd     total_value_usd median_implied_price       amendments_used      isin_only_weight unmapped_weight unpriced_weight other_nosic_weight
0      akre  2019-09-30  2019-11-13       44         25          25                   0         10144069000   144.43001268652208                                           0                                                   
1      akre  2019-12-31  2020-02-14       45         25          25                   0         10905311000   153.47973177067601                                           0                                                   
2      akre  2020-03-31  2020-05-11       41         28          28                   0         10293636000   138.89494306665986                                           0                                                   
3      akre  2020-06-30  2020-08-11       42         28          28                   0         13274303000   173.51513797797574                                           0                                                   
4      akre  2020-09-30  2020-11-13       44         28          28                   0         14185865000   206.46402301781177                                           0                                                   
5      akre  2020-12-31  2021-02-10       41         28          28                   0         14797811000   220.43492422591669                                           0                                                   
6      akre  2021-03-31  2021-07-09      100         24          24                   0         14686334000   218.40498704056569  0001112520-21-000016                     0                                                   
7      akre  2021-06-30  2021-08-13       44         25          25                   0         16237460000   233.82006880038622                                           0                                                   
8      akre  2021-09-30  2021-11-12       43         25          23             5202000         16241832000   222.74992573508916                                           0                                                   
9      akre  2021-12-31  2022-02-11       42         24          22           686600000         17920618000    241.4299838998021                                           0                                                   
10     akre  2022-03-31  2022-05-13       43         22          21           219000000         14665397000   214.62995737814643                                           0                                                   
11     akre  2022-06-30  2022-08-11       42         23          21            14092000         12492617000   165.04006514657979                                           0                                                   
12     akre  2022-09-30  2022-11-14       45         22          20            12458000         11336077000   170.24498126651301                                           0                                                   
13     akre  2022-12-31  2023-02-13       44         21          19            12347300         11064607827   176.42000421585161                                           0                                                   
14     akre  2023-03-31  2023-05-12       42         20          18            14034100         11365336959   198.09999049147251                                           0                                                   
15     akre  2023-06-30  2023-08-11       42         19          18             7463261         12003999013   209.98499260891637                                           0                                                   
16     akre  2023-09-30  2023-11-13       44         18          17           623462836         11515409077   164.45000002954984                                           0                                                   
17     akre  2023-12-31  2024-02-09       40         18          18                   0         11884542493   223.60999999118243                                           0                                                   
18     akre  2024-03-31  2024-05-13       43         41          41                   0         24176910344   133.14984297891431  0001112520-24-000012                     0                                                   
19     akre  2024-06-30  2024-08-13       44         19          19                   0         11366082231     194.380000055426                                           0                                                   
20     akre  2024-09-30  2024-11-13       44         18          18                   0         12017990024   181.56999746663894                                           0                                                   
21     akre  2024-12-31  2025-02-13       44         18          18                   0         11561087092   165.65999679796658                                           0                                                   
22     akre  2025-03-31  2025-05-13       43         18          18                   0         10400552669   162.22999996915414                                           0                                                   
23     akre  2025-06-30  2025-08-14       45         19          19                   0         10210810464   133.02999334053985                                           0                                                   
24     akre  2025-09-30  2025-11-13       44         19          19                   0         10030655183   129.94999336643536                                           0                                                   
25     akre  2025-12-31  2026-02-13       44         18          18                   0          9120742965   131.59999651947294                                           0                                                   
26     akre  2026-03-31  2026-05-14       44         20          19            18667000          6134537825   104.54999958945314                                           0                                                   
27     akre  2026-06-30  2026-08-14       45         20          19            15666000          5122536308   99.280000224701254                                           0                                                   
28   jensen  2019-09-30  2019-11-12       43         76          76                   0          9359105000     99.6194122995947                                           0                                                   
29   jensen  2019-12-31  2020-02-07       38         75          75                   0         10082174000   109.36749399519616                                           0                                                   
30   jensen  2020-03-31  2020-05-07       37         75          75                   0          8927902000   82.739963908473683                                           0                                                   
31   jensen  2020-06-30  2020-08-10       41         74          74                   0         10446228000   95.341743632751701                                           0                                                   
32   jensen  2020-09-30  2020-11-03       34         78          78                   0         11288835000   104.68804943143728                                           0                                                   
33   jensen  2020-12-31  2021-02-09       40         76          76                   0         12069598000   118.80744074828351                                           0                                                   
34   jensen  2021-03-31  2021-05-06       36         75          75                   0         12499593000   122.14996026351325                                           0                                                   
35   jensen  2021-06-30  2021-08-05       36         76          76                   0         13233116000    135.9449935664226                                           0                                                   
36   jensen  2021-09-30  2021-11-12       43         77          77                   0         12623142000   142.50972762645915                                           0                                                   
37   jensen  2021-12-31  2022-02-14       45         78          78                   0         14226059000   163.01575916471074                                           0                                                   
38   jensen  2022-03-31  2022-05-10       40         80          80                   0         13405004000   143.95717561404106                                           0                                                   
39   jensen  2022-06-30  2022-08-12       43         81          81                   0         12080212000   129.40997266084011                                           0                                                   
40   jensen  2022-09-30  2022-11-07       38         81          81                   0         11482946000   117.83854166666667                                           0                                                   
41   jensen  2022-12-31  2023-04-05       95         84          84                   0         12786876197   125.66499995018496  0001171200-23-000206                     0                                                   
42   jensen  2023-03-31  2023-05-08       38         81          81                   0         12682490501    120.0999999790203                                           0                                                   
43   jensen  2023-06-30  2023-08-07       38         82          82                   0         13628401703   140.49500626178627                                           0                                                   
44   jensen  2023-09-30  2023-11-07       38         83          83                   0         12654195071    132.3099853157122                                           0                                                   
45   jensen  2023-12-31  2024-02-12       43         82          82                   0         13201983108   144.56500265390508                                           0                                                   
46   jensen  2024-03-31  2024-05-07       37         84          84                   0         13091698543   155.65499887311245                                           0                                                   
47   jensen  2024-06-30  2024-08-05       36         87          87                   0         12220495522   164.92999991601889                                           0                                                   
48   jensen  2024-09-30  2024-11-04       35         87          87                   0         11959966628   170.40000268305116                                           0                                                   
49   jensen  2024-12-31  2025-02-10       41         85          85                   0         11048719969   160.62999230966417                                           0                                                   
50   jensen  2025-03-31  2025-05-09       39         84          84                   0          9043338708   154.45997973350291                                           0                                                   
51   jensen  2025-06-30  2025-08-08       39         83          83                   0          8532330700   159.31999999999999                                           0                                                   
52   jensen  2025-09-30  2025-11-06       37         87          87                   0          8059138040   185.41998619261304                                           0                                                   
53   jensen  2025-12-31  2026-02-11       42         89          89                   0          6355926761   203.19001081860802                                           0                                                   
54   jensen  2026-03-31  2026-05-05       35         84          84                   0          5072800848   191.32499199987836                                           0                                                   
55   jensen  2026-06-30  2026-08-07       38         83          83                   0          4125081649   189.73001250995111                                           0                                                   
56    polen  2019-09-30  2019-11-12       43         58          58                   0         21710787000   121.22907804476564                                           0                                                   
57    polen  2019-12-31  2020-02-06       37         62          62                   0         25392583000   121.09338882180867                                           0                                                   
58    polen  2020-03-31  2020-05-11       41         63          63                   0         23050442000   100.53975623911782                                           0                                                   
59    polen  2020-06-30  2020-08-13       44         63          63                   0         33086882000   137.03998689446988                                           0                                                   
60    polen  2020-09-30  2020-11-12       43         65          65                   0         37389091000   155.80998038463972                                           0                                                   
61    polen  2020-12-31  2021-02-11       42         72          72                   0         43039600000   152.55636883231145                                           0                                                   
62    polen  2021-03-31  2021-05-12       42         71          71                   0         44489600000   141.41400991967924                                           0                                                   
63    polen  2021-06-30  2021-08-12       43         81          81                   0         52218982000   154.49003920954863                                           0                                                   
64    polen  2021-09-30  2021-11-10       41         91          91                   0         54491390000   167.74997307073446                                           0                                                   
65    polen  2021-12-31  2022-02-11       42         92          92                   0         59532156000   167.29396643678382                                           0                                                   
66    polen  2022-03-31  2022-05-12       42         91          90            56103000         51274260000   133.79474668848371                                           0                                                   
67    polen  2022-06-30  2022-08-10       41         84          83            56103000         37931832000   90.719746709854391                                           0                                                   
68    polen  2022-09-30  2022-11-04       35         85          84            56103000         35758340000   96.302635821354656                                           0                                                   
69    polen  2022-12-31  2023-02-13       44         93          92            53473128         34279625946   92.805001912784718                                           0                                                   
70    polen  2023-03-31  2023-05-11       41         94          94                   0         37930613438   103.51000830284386                                           0                                                   
71    polen  2023-06-30  2023-08-11       42        100          99            24935969         40333393617   110.37000577197715                                           0                                                   
72    polen  2023-09-30  2023-11-13       44         99          98            24684720         38026346605   115.40638709269857                                           0                                                   
73    polen  2023-12-31  2024-05-10      131        107         106            24373736         41490887814   146.44567025501078  0001172661-24-002148                     0                                                   
74    polen  2024-03-31  2024-05-10       40        104         103            23628131         43317845975   116.36984393560807                                           0                                                   
75    polen  2024-06-30  2024-08-12       43        110         110                   0         39855562577   125.21762720310156                                           0                                                   
76    polen  2024-09-30  2025-02-10      133        118         118                   0         38739600406   125.48998224517499  0001172661-25-000622                     0                                                   
77    polen  2024-12-31  2025-02-10       41        124         124                   0         37010355943    121.6140596325788                                           0                                                   
78    polen  2025-03-31  2025-05-12       42        117         117                   0         31845099652   125.93125074662525                                           0                                                   
79    polen  2025-06-30  2025-08-13       44        240         240                   0         32586427255   75.460002040413656                                           0                                                   
80    polen  2025-09-30  2025-11-12       43        232         232                   0         30802400951   84.470001496699439                                           0                                                   
81    polen  2025-12-31  2026-02-12       43        234         231             5131648         23420875210   75.909986292328782                                           0                                                   
82    polen  2026-03-31  2026-05-14       44        221         221                   0         14456164077   74.260003483258586                                           0                                                   
83    polen  2026-06-30  2026-08-04       35        219         219                   0         11610786601                 88.5                                           0                                                   
84      ivv  2019-09-30  2019-11-25       56        508         505  1704982871.6099854  187935715202.09998   86.140000000000001  0001752724-19-177847  0.037223678127077039                                                   
85      ivv  2019-12-31  2020-02-27       58        508         505  2036487319.3499756  203062413031.03998   91.209999999999994  0001752724-20-038725  0.039873503386154925                                                   
86      ivv  2020-03-31  2020-06-01       62        508         505  3774576916.1700134     165446622458.47   68.530000000000001  0001752724-20-112027  0.035330368612893723                                                   
87      ivv  2020-06-30  2020-08-27       58        509         505  2406067300.7000122  196838310574.07001   79.640000000000001  0001752724-20-176909  0.032294549200009175                                                   
88      ivv  2020-09-30  2020-11-25       56        508         505  1536944007.3300171  215930793956.26001   86.519999999999996  0001752724-20-247818   0.03210019815764005                                                   
89      ivv  2020-12-31  2021-02-25       56        508         505  1651228767.6499634  239910030240.17999   97.759999999999991  0001752724-21-040719  0.032929055281697782                                                   
90      ivv  2021-03-31  2021-05-27       57        508         505  1777694393.8999329  262957957956.69998               107.69  0001752724-21-116363  0.035205271513439253                                                   
91      ivv  2021-06-30  2021-08-26       57        508         505  1288860988.1898804  287634387138.05994   115.93000000000001  0001752724-21-186201  0.034574392640443534                                                   
92      ivv  2021-09-30  2021-11-24       55        508         505        1226164521.5  287508464954.33002   113.20999999999999  0001752724-21-255857  0.034792597733917609                                                   
93      ivv  2021-12-31  2022-02-25       56        508         505  1550837601.0100098  335505600891.43005   119.91999999999999  0001752724-22-046281  0.034343019889840884                                                   
94      ivv  2022-03-31  2022-05-26       56        508         505  2055331835.6700439      334007862196.5   118.22999999999999  0001752724-22-122805  0.030413677557317709                                                   
95      ivv  2022-06-30  2022-08-25       56        508         505  2778811693.2299805  280296800663.79999   97.465000000000003  0001752724-22-193652  0.030137328003183753                                                   
96      ivv  2022-09-30  2022-11-28       59        506         503  3312193382.5799561  271105501828.41998   90.829999999999998  0001752724-22-268673  0.030008133828800427                                                   
97      ivv  2022-12-31  2023-02-24       55        506         503  4868219246.4000244  293485415064.28003               101.53  0001752724-23-039243  0.031720858945310397                                                   
98      ivv  2023-03-31  2023-05-26       56        506         503  3296424021.4399414  307956485382.18994               104.52  0001752724-23-123220  0.031786874378269381                                                   
99      ivv  2023-06-30  2023-08-25       56        506         503  2644605585.4499512     335980755381.13   109.61999999999999  0001752724-23-191503  0.031626598967804558                                                   
100     ivv  2023-09-30  2023-11-22       53        506         503  4744622505.8800049  343861466821.23999   103.07000000000001  0001752724-23-264277  0.031830089473945632                                                   
101     ivv  2023-12-31  2024-02-27       58        506         503  2803914144.3099365  401347968655.71997               116.89  0001752724-24-043113  0.031149528732574736                                                   
102     ivv  2024-03-31  2024-05-28       58        506         503  2270628836.3199463     455826382363.87               126.14  0001752724-24-123331  0.031114348998381294                                                   
103     ivv  2024-06-30  2024-08-27       58        506         503  3393776346.1599731  490169537793.16998               117.19  0001752724-24-194289  0.029005434809919142                                                   
104     ivv  2024-09-30  2024-11-26       57        507         504  3263116134.3500366  533190604502.15002   126.18000000000001  0001752724-24-269943  0.030332945378507226                                                   
105     ivv  2024-12-31  2025-02-27       58        506         503  4642265115.2797852  589040826234.10986   119.44999999999999  0001752724-25-043800  0.028229978354764346                                                   
106     ivv  2025-03-31  2025-05-27       57        508         504  3947454570.5500488  582417536396.68005              120.295  0001752724-25-119791  0.029156243479138817                                                   
107     ivv  2025-06-30  2025-08-28       59        508         504  4101606926.9100342  625581446505.93005   126.82999999999998  0001752724-25-210389  0.028355370861180375                                                   
108     ivv  2025-09-30  2026-07-13      286        507         503  3495517839.3299561     703600482611.75   134.17000000000002  0002071691-26-015790  0.026839703631123622                                                   
109     ivv  2025-12-31  2026-02-25       56        507         503  2713386165.6098633  761881724623.10986   136.06999999999999  0002071691-26-004238  0.026832224000553958                                                   
110     ivv  2026-03-31  2026-05-28       58        507         503  2094312171.5200195  721016497487.06006   135.46000000000001  0002071691-26-012459  0.028133213126595672                                                   
111     ivv  2026-06-30  2026-08-25       56        508         503  2526541924.8400879  889159485657.55005   140.64000000000001  0002071691-26-019760  0.028395715558004228                                                   
112     iwf  2019-09-30  2019-11-25       56        534         531  1338669071.7600021  46150213082.900002   92.269999999999996  0001752724-19-177844  0.020904286239213858                                                   
113     iwf  2019-12-31  2020-02-27       58        533         530  1385640991.5399933  50744482270.039993   98.969999999999999  0001752724-20-038663  0.020892276646477598                                                   
114     iwf  2020-03-31  2020-06-01       62        535         532  1843643733.8600006         44190901508   73.055000000000007  0001752724-20-112153  0.018712153071547794                                                   
115     iwf  2020-06-30  2020-08-27       58        439         435  923421188.81999969      54974347311.93               103.97  0001752724-20-176978  0.020598585602661239                                                   
116     iwf  2020-09-30  2020-11-25       56        449         446  1329061464.0200043  59527225170.119995               108.83  0001752724-20-247763  0.019887039161146064                                                   
117     iwf  2020-12-31  2021-02-25       56        457         454  1067765583.1199951         65454057363   129.80000000000001  0001752724-21-040696  0.021319012922544772                                                   
118     iwf  2021-03-31  2021-05-27       57        465         462  1059820709.0999985  64231931663.029999   128.11000000000001  0001752724-21-116383  0.021257402376965502                                                   
119     iwf  2021-06-30  2021-08-26       57        501         498  815003599.02999878         69875218347   134.78999999999999  0001752724-21-186226   0.01962049008832295                                                   
120     iwf  2021-09-30  2021-11-24       55        505         501   913625405.1499939  72217709977.029999   127.10000000000001  0001752724-21-255846  0.019642057790646327                                                   
121     iwf  2021-12-31  2022-02-25       56        506         502  1028687251.1499939  80019086115.259995   130.86500000000001  0001752724-22-046298  0.019801410227220317                                                   
122     iwf  2022-03-31  2022-05-26       56        502         498  1084895102.0900116  72312194774.190002   115.91500000000001  0001752724-22-122801  0.018032052277184591                                                   
123     iwf  2022-06-30  2022-08-25       56        524         520  1044309303.2199936  58147929228.649994   91.200000000000003  0001752724-22-193669  0.021889660812962678                                                   
124     iwf  2022-09-30  2022-11-28       59        523         519  1489120923.8099976  56469293839.619995   86.120000000000005  0001752724-22-269723                     0                                                   
125     iwf  2022-12-31  2023-02-24       55        516         512  1561426803.8899994  60844251682.049995                89.25  0001752724-23-039553                     0                                                   
126     iwf  2023-03-31  2023-05-24       54        513         509  1340169479.3499985  64746426241.479996               100.13  0001752724-23-114945                     0                                                   
127     iwf  2023-06-30  2023-08-28       59        448         444        809095429.25  72187840158.900009   119.39500000000001  0001752724-23-192397                     0                                                   
128     iwf  2023-09-30  2023-11-24       55        450         446   1325479791.719986  70392263206.369995               112.16  0001752724-23-265163                     0                                                   
129     iwf  2023-12-31  2024-02-23       54        446         443   704174912.0900116  82471049404.230011   129.49000000000001  0001752724-24-034941                     0                                                   
130     iwf  2024-03-31  2024-05-24       54        443         440  720238531.82000732  89730995529.790009   137.51999999999998  0001752724-24-118346                     0                                                   
131     iwf  2024-06-30  2024-08-26       57        443         440  1183714039.8999939  98003957923.709991   129.50999999999999  0001752724-24-189692                     0                                                   
132     iwf  2024-09-30  2024-11-26       57        397         394  961668295.48999023  100019001339.94998   148.01499999999999  0001752724-24-268863                     0                                                   
133     iwf  2024-12-31  2025-02-24       55        399         396  1006910278.8400116      107259032932.8   143.91999999999999  0001752724-25-034056                     0                                                   
134     iwf  2025-03-31  2025-05-23       53        397         394  1110751123.1500092  97198214884.900009              136.505  0001752724-25-118601                     0                                                   
135     iwf  2025-06-30  2025-08-26       57        388         385  621920663.14001465     111978843675.66   140.11999999999998  0001752724-25-204350                     0                                                   
136     iwf  2025-09-30  2025-11-25       56        394         391   1047897046.260025  123008661862.11002               140.78  0001004726-25-002059                     0                                                   
137     iwf  2025-12-31  2026-02-23       54        394         391  914313640.20999146        126711560071   136.19999999999999  0001004726-26-000787                     0                                                   
138     iwf  2026-03-31  2026-05-22       52        390         387  755699548.98001099  112349595351.33002   128.31999999999999  0001004726-26-003755                     0                                                   
139     iwf  2026-06-30  2026-08-24       55        371         368  963738384.05000305  129691017223.62999   167.24250000768404  0001004726-26-007047                     0                                                   
```

### Section E item 6a Akre 2023-06-30 book: 5 largest positions (HOLDINGS rows)

```
    entity period_date      cusip isin     sec_id                     name  value_usd  shares
367   akre  2023-06-30  57636Q104       57636Q104  MASTERCARD INCORPORATED 2308458225 5869459
368   akre  2023-06-30  615369105       615369105              MOODYS CORP 1836386862 5281223
356   akre  2023-06-30  03027X100       03027X100  AMERICAN TOWER CORP NEW 1308115021 6744947
372   akre  2023-06-30  92826C839       92826C839                 VISA INC 1168909332 4922138
369   akre  2023-06-30  67103H107       67103H107   OREILLY AUTOMOTIVE INC 1063968241 1113753
```

### Section E item 6b raw infoTable elements for those CUSIPs, from data/raw/edgar/13f/akre/2023-06-30_0001112520-23-000013.xml

```
<infoTable xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable" xmlns:n1="http://www.sec.gov/edgar/document/thirteenf/informationtable" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <nameOfIssuer>MASTERCARD INCORPORATED</nameOfIssuer>
    <titleOfClass>CL A</titleOfClass>
    <cusip>57636Q104</cusip>
    <figi>BBG000F1ZSQ2</figi>
    <value>2308458225</value>
    <shrsOrPrnAmt>
      <sshPrnamt>5869459</sshPrnamt>
      <sshPrnamtType>SH</sshPrnamtType>
    </shrsOrPrnAmt>
    <investmentDiscretion>SOLE</investmentDiscretion>
    <votingAuthority>
      <Sole>5869459</Sole>
      <Shared>0</Shared>
      <None>0</None>
    </votingAuthority>
  </infoTable>
<infoTable xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable" xmlns:n1="http://www.sec.gov/edgar/document/thirteenf/informationtable" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <nameOfIssuer>MASTERCARD INCORPORATED</nameOfIssuer>
    <titleOfClass>COM</titleOfClass>
    <cusip>57636Q104</cusip>
    <figi>BBG000F1ZSQ2</figi>
    <value>7463261</value>
    <shrsOrPrnAmt>
      <sshPrnamt>10000</sshPrnamt>
      <sshPrnamtType>SH</sshPrnamtType>
    </shrsOrPrnAmt>
    <putCall>Call</putCall>
    <investmentDiscretion>SOLE</investmentDiscretion>
    <votingAuthority>
      <Sole>10000</Sole>
      <Shared>0</Shared>
      <None>0</None>
    </votingAuthority>
  </infoTable>
<infoTable xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable" xmlns:n1="http://www.sec.gov/edgar/document/thirteenf/informationtable" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <nameOfIssuer>MOODYS CORP</nameOfIssuer>
    <titleOfClass>COM</titleOfClass>
    <cusip>615369105</cusip>
    <figi>BBG000F86GP6</figi>
    <value>1836386862</value>
    <shrsOrPrnAmt>
      <sshPrnamt>5281223</sshPrnamt>
      <sshPrnamtType>SH</sshPrnamtType>
    </shrsOrPrnAmt>
    <investmentDiscretion>SOLE</investmentDiscretion>
    <votingAuthority>
      <Sole>5281223</Sole>
      <Shared>0</Shared>
      <None>0</None>
    </votingAuthority>
  </infoTable>
<infoTable xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable" xmlns:n1="http://www.sec.gov/edgar/document/thirteenf/informationtable" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <nameOfIssuer>AMERICAN TOWER CORP NEW</nameOfIssuer>
    <titleOfClass>COM</titleOfClass>
    <cusip>03027X100</cusip>
    <figi>BBG000B9Y2N0</figi>
    <value>1308115021</value>
    <shrsOrPrnAmt>
      <sshPrnamt>6744947</sshPrnamt>
      <sshPrnamtType>SH</sshPrnamtType>
    </shrsOrPrnAmt>
    <investmentDiscretion>SOLE</investmentDiscretion>
    <votingAuthority>
      <Sole>6744947</Sole>
      <Shared>0</Shared>
      <None>0</None>
    </votingAuthority>
  </infoTable>
<infoTable xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable" xmlns:n1="http://www.sec.gov/edgar/document/thirteenf/informationtable" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <nameOfIssuer>VISA INC</nameOfIssuer>
    <titleOfClass>COM CL A</titleOfClass>
    <cusip>92826C839</cusip>
    <figi>BBG000PSKYX7</figi>
    <value>1168909332</value>
    <shrsOrPrnAmt>
      <sshPrnamt>4922138</sshPrnamt>
      <sshPrnamtType>SH</sshPrnamtType>
    </shrsOrPrnAmt>
    <investmentDiscretion>SOLE</investmentDiscretion>
    <votingAuthority>
      <Sole>4922138</Sole>
      <Shared>0</Shared>
      <None>0</None>
    </votingAuthority>
  </infoTable>
<infoTable xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable" xmlns:n1="http://www.sec.gov/edgar/document/thirteenf/informationtable" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <nameOfIssuer>OREILLY AUTOMOTIVE INC</nameOfIssuer>
    <titleOfClass>COM</titleOfClass>
    <cusip>67103H107</cusip>
    <figi>BBG000BGYWY6</figi>
    <value>1063968241</value>
    <shrsOrPrnAmt>
      <sshPrnamt>1113753</sshPrnamt>
      <sshPrnamtType>SH</sshPrnamtType>
    </shrsOrPrnAmt>
    <investmentDiscretion>SOLE</investmentDiscretion>
    <votingAuthority>
      <Sole>1113753</Sole>
      <Shared>0</Shared>
      <None>0</None>
    </votingAuthority>
  </infoTable>
```

### Section E item 7 IVV 2023-06-30 (0001752724-23-191503): 3 largest val_usd rows of holdings_ivv.csv

```
                  name      cusip          isin   balance            val_usd            pct_val
7685       Apple, Inc.  037833100  US0378331005 132617379 25723793004.630001 7.6958735441600004
7982   Microsoft Corp.  594918104  US5949181045  66694365 22712099057.099998 6.7948549513829999
7651  Amazon.com, Inc.  023135106  US0231351067  80068427 10437720143.719999 3.1226877895079999
```

### Section E item 8 per fund: distinct CUSIPs across all 28 books, largest single-position weight

```
     fund  n_books  distinct_cusips     max_w_2019-09-30      max_name_2019-09-30     max_w_2022-12-31      max_name_2022-12-31     max_w_2026-06-30        max_name_2026-06-30
0    akre       28               48  0.15665794465711935  AMERICAN TOWER CORP NEW  0.18455891589027504  MASTERCARD INCORPORATED  0.20012564650388612    MASTERCARD INCORPORATED
1  jensen       28              141 0.070228510097920693             PepsiCo Inc. 0.069639211429052356             PepsiCo Inc. 0.069055339078938072  Alphabet Inc Cap Stk Cl A
2   polen       28              567  0.10358947374869459           MICROSOFT CORP 0.086263439881775386           AMAZON COM INC 0.068894073975238335             ELI LILLY & CO
```

### 01b D item 1: ISIN-only rows (sec_id is an ISIN) per period, IVV and IWF, now kept

```
   entity period_date  n_rows  n_isin_only     isin_only_weight
0     ivv  2019-09-30     505           28 0.037223678127077039
1     ivv  2019-12-31     505           31 0.039873503386154925
2     ivv  2020-03-31     505           31 0.035330368612893723
3     ivv  2020-06-30     505           29 0.032294549200009175
4     ivv  2020-09-30     505           29  0.03210019815764005
5     ivv  2020-12-31     505           28 0.032929055281697782
6     ivv  2021-03-31     505           28 0.035205271513439253
7     ivv  2021-06-30     505           28 0.034574392640443534
8     ivv  2021-09-30     505           27 0.034792597733917609
9     ivv  2021-12-31     505           27 0.034343019889840884
10    ivv  2022-03-31     505           24 0.030413677557317709
11    ivv  2022-06-30     505           24 0.030137328003183753
12    ivv  2022-09-30     503           24 0.030008133828800427
13    ivv  2022-12-31     503           24 0.031720858945310397
14    ivv  2023-03-31     503           25 0.031786874378269381
15    ivv  2023-06-30     503           25 0.031626598967804558
16    ivv  2023-09-30     503           25 0.031830089473945632
17    ivv  2023-12-31     503           25 0.031149528732574736
18    ivv  2024-03-31     503           25 0.031114348998381294
19    ivv  2024-06-30     503           25 0.029005434809919142
20    ivv  2024-09-30     504           26 0.030332945378507226
21    ivv  2024-12-31     503           26 0.028229978354764346
22    ivv  2025-03-31     504           26 0.029156243479138817
23    ivv  2025-06-30     504           26 0.028355370861180375
24    ivv  2025-09-30     503           26 0.026839703631123622
25    ivv  2025-12-31     503           27 0.026832224000553958
26    ivv  2026-03-31     503           27 0.028133213126595672
27    ivv  2026-06-30     503           29 0.028395715558004228
28    iwf  2019-09-30     531           25 0.020904286239213858
29    iwf  2019-12-31     530           25 0.020892276646477598
30    iwf  2020-03-31     532           25 0.018712153071547794
31    iwf  2020-06-30     435           17 0.020598585602661239
32    iwf  2020-09-30     446           18 0.019887039161146064
33    iwf  2020-12-31     454           19 0.021319012922544772
34    iwf  2021-03-31     462           19 0.021257402376965502
35    iwf  2021-06-30     498           25  0.01962049008832295
36    iwf  2021-09-30     501           25 0.019642057790646327
37    iwf  2021-12-31     502           26 0.019801410227220317
38    iwf  2022-03-31     498           26 0.018032052277184591
39    iwf  2022-06-30     520           21 0.021889660812962678
40    iwf  2022-09-30     519            0                    0
41    iwf  2022-12-31     512            0                    0
42    iwf  2023-03-31     509            0                    0
43    iwf  2023-06-30     444            0                    0
44    iwf  2023-09-30     446            0                    0
45    iwf  2023-12-31     443            0                    0
46    iwf  2024-03-31     440            0                    0
47    iwf  2024-06-30     440            0                    0
48    iwf  2024-09-30     394            0                    0
49    iwf  2024-12-31     396            0                    0
50    iwf  2025-03-31     394            0                    0
51    iwf  2025-06-30     385            0                    0
52    iwf  2025-09-30     391            0                    0
53    iwf  2025-12-31     391            0                    0
54    iwf  2026-03-31     387            0                    0
55    iwf  2026-06-30     368            0                    0
```
```
       n_isin_only         isin_only_weight                     
               min max                  min                  max
entity                                                          
ivv             24  31 0.026832224000553958 0.039873503386154925
iwf              0  26                    0 0.021889660812962678
```

### 01b D item 1b: CUSIP strings of kept ISIN-only rows, and EC/NS rows dropped for having neither id (books used)

```
  entity cusip_as_filed  rows
0    ivv             ''   334
1    ivv          'N/A'   411
2    iwf             ''   271
```
```
EC/NS rows with neither a valid CUSIP nor a valid ISIN, in the books used: 0
```

### 01b D item 2: every NPORT-P/A in either feed

```
  entity             accession filing_date period_date  in_H  used
0    ivv  0002071691-26-015790  2026-07-13  2025-09-30  True  True
```
```
forms recorded in MANIFEST.json uncommitted_sha256 (from each filing's submissionType):
NPORT-P      56
NPORT-P/A     1
```

### 01b D item 2b: every ivv filing for period 2025-09-30, and the original against the amendment

```
   entity   series_id             accession filing_date period_date
24    ivv  S000004310  0002071691-25-007634  2025-11-26  2025-09-30
27    ivv  S000004310  0002071691-26-015790  2026-07-13  2025-09-30
```
```
              accession  n_rows_raw     sum_val_usd      sum_pct_val
0  0002071691-25-007634         507 703600482611.75 100.318112507142
1  0002071691-26-015790         507 703600482611.75 100.318112507142
```
```
rows whose val_usd differs between the 2 filings: 0 of 507
Empty DataFrame
Columns: [name, cusip, asset_cat, val_usd_orig, val_usd_amend, delta]
Index: []
```

### 01b D item 3: precision check, coverage.csv total_value_usd against a recomputation from the raw file

```
  entity period_date                                          raw_file   coverage_csv_text       recomputed  difference
0   akre  2023-06-30               2023-06-30_0001112520-23-000013.xml         12003999013      12003999013           0
1  polen  2023-06-30               2023-06-30_0001172661-23-002916.xml         40333393617      40333393617           0
2    ivv  2026-06-30  holdings_ivv.csv, accession 0002071691-26-019760  889159485657.55005  889159485657.55           0
```
```
all 84 13F rows of coverage.csv against the same lxml recomputation: 0 differ
        count  min  max
entity                 
akre       28    0    0
jensen     28    0    0
polen      28    0    0
```

### 01b D item 4: MANIFEST.json sha256 of the 13F information tables, before (e5dba91) and after the re-pull

```
                                                    file                                                     sha256_before                                                      sha256_after  identical
0     edgar/13f/akre/2019-03-31_0001112520-19-000015.xml  9c802ea6fef4d850c7c8c384618eb1954fb6d226d15ccebea1751df486f138c2  9c802ea6fef4d850c7c8c384618eb1954fb6d226d15ccebea1751df486f138c2       True
1     edgar/13f/akre/2019-06-30_0001112520-19-000017.xml  4c6cb15ee79df7542c40c1a8afbbb6440f1625192e518c335f26062a5c822992  4c6cb15ee79df7542c40c1a8afbbb6440f1625192e518c335f26062a5c822992       True
2     edgar/13f/akre/2019-09-30_0001112520-19-000024.xml  54783025bdfadae5f1130bcc124264f77e53b8398b4af320f87c95acdf761a05  54783025bdfadae5f1130bcc124264f77e53b8398b4af320f87c95acdf761a05       True
3     edgar/13f/akre/2019-12-31_0001112520-20-000010.xml  33d3c756b05c1b6e46d16cfaaa559b67ddbfb1e3d4882abe4b27d02792d41322  33d3c756b05c1b6e46d16cfaaa559b67ddbfb1e3d4882abe4b27d02792d41322       True
4     edgar/13f/akre/2020-03-31_0001112520-20-000016.xml  8272356a13f8bd0dc4b26bc8e3ea893041dbf858e85aa1ad22aeb1a0828de555  8272356a13f8bd0dc4b26bc8e3ea893041dbf858e85aa1ad22aeb1a0828de555       True
5     edgar/13f/akre/2020-06-30_0001112520-20-000022.xml  0161aa3e12512991ae0ad2710ca4bb689005907a3064419869db79488da85e7a  0161aa3e12512991ae0ad2710ca4bb689005907a3064419869db79488da85e7a       True
6     edgar/13f/akre/2020-09-30_0001112520-20-000024.xml  70dde337b9f781be21f13353c651682cda3b04f9eded8ef27f7cd3529439c984  70dde337b9f781be21f13353c651682cda3b04f9eded8ef27f7cd3529439c984       True
7     edgar/13f/akre/2020-12-31_0001112520-21-000003.xml  44e76e574dff7a17f4fc06188ed069dcf3966e51c4a3c4ae320a08604f3e06ed  44e76e574dff7a17f4fc06188ed069dcf3966e51c4a3c4ae320a08604f3e06ed       True
8     edgar/13f/akre/2021-03-31_0001112520-21-000012.xml  a4c90af2249ad8c03a11ffcc1f7e7c6c3ebd64405a65bfcbe249f4580cae549e  a4c90af2249ad8c03a11ffcc1f7e7c6c3ebd64405a65bfcbe249f4580cae549e       True
9     edgar/13f/akre/2021-03-31_0001112520-21-000016.xml  fe4137fca20e1cfc056a4c7c0e7e94b8f7e24dba2112fb035d324987b2e1cb49  fe4137fca20e1cfc056a4c7c0e7e94b8f7e24dba2112fb035d324987b2e1cb49       True
10    edgar/13f/akre/2021-06-30_0001112520-21-000020.xml  b1a35d4cb8842774fc5e2cfd9ad92e537486748a493faedfabba20b602f7bddd  b1a35d4cb8842774fc5e2cfd9ad92e537486748a493faedfabba20b602f7bddd       True
11    edgar/13f/akre/2021-09-30_0001112520-21-000023.xml  48164b6cb6b2db029eb0476948f4c8a119f39c437b0a208c75bf4f73ab3c6a0c  48164b6cb6b2db029eb0476948f4c8a119f39c437b0a208c75bf4f73ab3c6a0c       True
12    edgar/13f/akre/2021-12-31_0001112520-22-000005.xml  e1b51756bcf03469267737cd8416c66cbb76d5cf2db27d55ee3f32ec84acc799  e1b51756bcf03469267737cd8416c66cbb76d5cf2db27d55ee3f32ec84acc799       True
13    edgar/13f/akre/2022-03-31_0001112520-22-000009.xml  e45e302db161e8b23d291d11298805b9730cae9e4edc8eb86517d3887bd7df6a  e45e302db161e8b23d291d11298805b9730cae9e4edc8eb86517d3887bd7df6a       True
14    edgar/13f/akre/2022-06-30_0001112520-22-000013.xml  4c071fd59e1f912ca5bd1cc4a6ac4de3f08325862aa6e7f1af63ea960acb562c  4c071fd59e1f912ca5bd1cc4a6ac4de3f08325862aa6e7f1af63ea960acb562c       True
15    edgar/13f/akre/2022-09-30_0001112520-22-000015.xml  05eaa7923a74b499d657ac32f2c0254bcb397c4a0d16eb7882940377132e1925  05eaa7923a74b499d657ac32f2c0254bcb397c4a0d16eb7882940377132e1925       True
16    edgar/13f/akre/2022-12-31_0001112520-23-000006.xml  6143a596b6b581bf247e7b8d9b278311bd3363798dbcbcfb4b5428c98e3a9bc1  6143a596b6b581bf247e7b8d9b278311bd3363798dbcbcfb4b5428c98e3a9bc1       True
17    edgar/13f/akre/2023-03-31_0001112520-23-000008.xml  5e91a9a2417f8274dfebf70c60faaf8e6426482f72899355ecf71a7c624ac1e4  5e91a9a2417f8274dfebf70c60faaf8e6426482f72899355ecf71a7c624ac1e4       True
18    edgar/13f/akre/2023-06-30_0001112520-23-000013.xml  439c2e43ef797906c769c2fcbac7f298254d09d9a41aa4870211a5a0a9c5d305  439c2e43ef797906c769c2fcbac7f298254d09d9a41aa4870211a5a0a9c5d305       True
19    edgar/13f/akre/2023-09-30_0001112520-23-000019.xml  306ee9731c20b71fab0fedaca5e1199b0a2ba7d8a0770281270b8bcfdebb39f5  306ee9731c20b71fab0fedaca5e1199b0a2ba7d8a0770281270b8bcfdebb39f5       True
20    edgar/13f/akre/2023-12-31_0001112520-24-000006.xml  380179b5358956b57b6abc0176bd047efc032b89efb6bfd73f1e140453559f11  380179b5358956b57b6abc0176bd047efc032b89efb6bfd73f1e140453559f11       True
21    edgar/13f/akre/2024-03-31_0001112520-24-000010.xml  d20bf9f83da524604663bca9332b2b1d6f3c974a26b9d3d8094cb8f81d384bf4  d20bf9f83da524604663bca9332b2b1d6f3c974a26b9d3d8094cb8f81d384bf4       True
22    edgar/13f/akre/2024-03-31_0001112520-24-000012.xml  87b861d6fe80bb1856f62909e9750436ee5a46de5c18afca91458f43e2e51a6a  87b861d6fe80bb1856f62909e9750436ee5a46de5c18afca91458f43e2e51a6a       True
23    edgar/13f/akre/2024-06-30_0001112520-24-000014.xml  2af450eef75f808a1bf00af16e18123b29ac6cc918a6f0928f5433e4a175e2d8  2af450eef75f808a1bf00af16e18123b29ac6cc918a6f0928f5433e4a175e2d8       True
24    edgar/13f/akre/2024-09-30_0001112520-24-000025.xml  23b7c35bed9eac5bc04065be56f344cc6d00020b8ac753dab14264840d84451c  23b7c35bed9eac5bc04065be56f344cc6d00020b8ac753dab14264840d84451c       True
25    edgar/13f/akre/2024-12-31_0001112520-25-000003.xml  b891b54daa2ba597a8dbfc17593d0ee93b1c5d599474f24f2da9d9f3bdd99409  b891b54daa2ba597a8dbfc17593d0ee93b1c5d599474f24f2da9d9f3bdd99409       True
26    edgar/13f/akre/2025-03-31_0001112520-25-000015.xml  9b7f24d68534dda74cc83d1b7c3bcfcbc08fa5e08234f4b1b6288f74dd41eeb8  9b7f24d68534dda74cc83d1b7c3bcfcbc08fa5e08234f4b1b6288f74dd41eeb8       True
27    edgar/13f/akre/2025-06-30_0001112520-25-000019.xml  da7a924817e0983b6eab1ba163c663cf0d48dff7faeb9807f78e7df7c9a50b71  da7a924817e0983b6eab1ba163c663cf0d48dff7faeb9807f78e7df7c9a50b71       True
28    edgar/13f/akre/2025-09-30_0001112520-25-000029.xml  e923a4cca9199f0698611aa25bada88e754fa13ba8e7f235f30ae0ae5c300866  e923a4cca9199f0698611aa25bada88e754fa13ba8e7f235f30ae0ae5c300866       True
29    edgar/13f/akre/2025-12-31_0001112520-26-000008.xml  a8fc1019b8a146a7a63d3766757a617ab3cb1ea6d0f26555f60681c0af0e2cb4  a8fc1019b8a146a7a63d3766757a617ab3cb1ea6d0f26555f60681c0af0e2cb4       True
30    edgar/13f/akre/2026-03-31_0001112520-26-000009.xml  68f9b140a43ad70c6de441ec73382a6fe11f69a8e6f5db371b688c070b1af5a8  68f9b140a43ad70c6de441ec73382a6fe11f69a8e6f5db371b688c070b1af5a8       True
31    edgar/13f/akre/2026-06-30_0001112520-26-000014.xml  b038bfc6641c7b120128f2549a7689ef839fb370d796cd4f323af9aa852fa6b5  b038bfc6641c7b120128f2549a7689ef839fb370d796cd4f323af9aa852fa6b5       True
32  edgar/13f/jensen/2019-03-31_0001171200-19-000211.xml  14a54b67bff3904814bec2e09f16e493a449e54cf78c36223e719606b15077c7  14a54b67bff3904814bec2e09f16e493a449e54cf78c36223e719606b15077c7       True
33  edgar/13f/jensen/2019-06-30_0001171200-19-000284.xml  c53158c335f01ba5e7c175fd669bea7ebf166ced0f29f6abe70999dc248ebb11  c53158c335f01ba5e7c175fd669bea7ebf166ced0f29f6abe70999dc248ebb11       True
34  edgar/13f/jensen/2019-09-30_0001171200-19-000366.xml  7f004a9e430f90051ddd8250e38d0d8926b44c2dc557340da15c4377a5b45eae  7f004a9e430f90051ddd8250e38d0d8926b44c2dc557340da15c4377a5b45eae       True
35  edgar/13f/jensen/2019-12-31_0001171200-20-000061.xml  4edf0d251271b2132da6392c5a0e4b9fba4f4f57bb4798669f2fab14f53044ce  4edf0d251271b2132da6392c5a0e4b9fba4f4f57bb4798669f2fab14f53044ce       True
36  edgar/13f/jensen/2020-03-31_0001171200-20-000338.xml  017d7e05019e0fda87250d05aacf9bb1559d9426fe2c83d4d0c7bb4384bc73da  017d7e05019e0fda87250d05aacf9bb1559d9426fe2c83d4d0c7bb4384bc73da       True
37  edgar/13f/jensen/2020-06-30_0001171200-20-000521.xml  31a25e853f8da4e86b658e65e9da09f6bf59dc865833927e19c825ced6420dec  31a25e853f8da4e86b658e65e9da09f6bf59dc865833927e19c825ced6420dec       True
38  edgar/13f/jensen/2020-09-30_0001171200-20-000622.xml  7ad0fecf3c747b5f06e6aa9be8841ec0a068c36c99f5b713f5a749e0e68537d0  7ad0fecf3c747b5f06e6aa9be8841ec0a068c36c99f5b713f5a749e0e68537d0       True
39  edgar/13f/jensen/2020-12-31_0001171200-21-000057.xml  37cfe2a3fc65583c3636535b3af49543ca5be888f080b0947943ec578bbd48ab  37cfe2a3fc65583c3636535b3af49543ca5be888f080b0947943ec578bbd48ab       True
40  edgar/13f/jensen/2021-03-31_0001171200-21-000236.xml  537019a72aea297b488ac89155cdaae9eafcabf719b27491cf19e963b619ccdd  537019a72aea297b488ac89155cdaae9eafcabf719b27491cf19e963b619ccdd       True
41  edgar/13f/jensen/2021-06-30_0001171200-21-000290.xml  b28c4c1912f99a12a2d081109c16e39291e0166464842a88f1f9d232bd5be7ec  b28c4c1912f99a12a2d081109c16e39291e0166464842a88f1f9d232bd5be7ec       True
42  edgar/13f/jensen/2021-09-30_0001171200-21-000388.xml  7dc55aaa0e99c40e91bd7f144f9a566d5f27706d4ad73ec0854e59e517a471ab  7dc55aaa0e99c40e91bd7f144f9a566d5f27706d4ad73ec0854e59e517a471ab       True
43  edgar/13f/jensen/2021-12-31_0001171200-22-000037.xml  33cce176c2870d4f2d0603b801afa801c611aa9361abe68c4e7e9c04e6afae6b  33cce176c2870d4f2d0603b801afa801c611aa9361abe68c4e7e9c04e6afae6b       True
44  edgar/13f/jensen/2022-03-31_0001171200-22-000245.xml  72e01f46dc68b0418a21bf906fd88721ccd4c91c6776df4124dff5124705a093  72e01f46dc68b0418a21bf906fd88721ccd4c91c6776df4124dff5124705a093       True
45  edgar/13f/jensen/2022-06-30_0001171200-22-000293.xml  54f097769c64651a44f6c51de3adbbaef5a6b53e10783038aa5110ec502a3296  54f097769c64651a44f6c51de3adbbaef5a6b53e10783038aa5110ec502a3296       True
46  edgar/13f/jensen/2022-09-30_0001171200-22-000347.xml  d3d9bb6aff0dd9356653a87a8cbd75eae5afa3551bc215c3bb7eeacd9fa7bd0d  d3d9bb6aff0dd9356653a87a8cbd75eae5afa3551bc215c3bb7eeacd9fa7bd0d       True
47  edgar/13f/jensen/2022-12-31_0001171200-23-000057.xml  bc7698e12c9a44569a690f074812d6ea77f6585ff8ef872d4ab22b808358efb3  bc7698e12c9a44569a690f074812d6ea77f6585ff8ef872d4ab22b808358efb3       True
48  edgar/13f/jensen/2022-12-31_0001171200-23-000206.xml  0bcbab4c042a1e855069c96d02e6a6fcfa5bc53189f0532f40d4104c0e37a7be  0bcbab4c042a1e855069c96d02e6a6fcfa5bc53189f0532f40d4104c0e37a7be       True
49  edgar/13f/jensen/2023-03-31_0001171200-23-000298.xml  324fe6f58e1e7bb635f97a361f64961e6dd87de56043dc96ddc1279229c1725d  324fe6f58e1e7bb635f97a361f64961e6dd87de56043dc96ddc1279229c1725d       True
50  edgar/13f/jensen/2023-06-30_0001171200-23-000356.xml  82a53ed673f9d5d8ff0d97f38ad49a2bceb773a4e0d783195de7b502ba4c70f8  82a53ed673f9d5d8ff0d97f38ad49a2bceb773a4e0d783195de7b502ba4c70f8       True
51  edgar/13f/jensen/2023-09-30_0001171200-23-000445.xml  387259c30000d478b6f59b77443854d305ab9dd4b905441a9e595ad2e90969d1  387259c30000d478b6f59b77443854d305ab9dd4b905441a9e595ad2e90969d1       True
52  edgar/13f/jensen/2023-12-31_0001171200-24-000016.xml  ff514adde12353e6bb011c88a45969082412ad79213d50d259575435a1bffb6d  ff514adde12353e6bb011c88a45969082412ad79213d50d259575435a1bffb6d       True
53  edgar/13f/jensen/2024-03-31_0001171200-24-000202.xml  eda5ff5629d192abc800451565c1f35be9ece57e9dad035287c7f5486e8d92e8  eda5ff5629d192abc800451565c1f35be9ece57e9dad035287c7f5486e8d92e8       True
54  edgar/13f/jensen/2024-06-30_0001171200-24-000243.xml  ba5f930f80997b8fc18b0d1ab2ca867131f75613bda4a86bfaf34d1a823c1cd0  ba5f930f80997b8fc18b0d1ab2ca867131f75613bda4a86bfaf34d1a823c1cd0       True
55  edgar/13f/jensen/2024-09-30_0001171200-24-000330.xml  587cf76743926b770144efd803441d212880dc39353ab71624e502581b72f83a  587cf76743926b770144efd803441d212880dc39353ab71624e502581b72f83a       True
56  edgar/13f/jensen/2024-12-31_0001171200-25-000017.xml  c158f585d132dc4f99923b57070137a69ee89cb5802f6e12957eef437c021d1e  c158f585d132dc4f99923b57070137a69ee89cb5802f6e12957eef437c021d1e       True
57  edgar/13f/jensen/2025-03-31_0001171200-25-000219.xml  177588de79a8252eeef29cb11b0a91f91a2d445df6ad9349129c7a90c949b025  177588de79a8252eeef29cb11b0a91f91a2d445df6ad9349129c7a90c949b025       True
58  edgar/13f/jensen/2025-06-30_0001171200-25-000262.xml  b16507dde3f1b4a64c42b5bf51d2e801b882a490053e7651ffa2ff0a198505bf  b16507dde3f1b4a64c42b5bf51d2e801b882a490053e7651ffa2ff0a198505bf       True
59  edgar/13f/jensen/2025-09-30_0001171200-25-000265.xml  3fcbf1a379d56ec4fc960955788c797e80532cc0f1063dd5cadd79ff1fe0e1d5  3fcbf1a379d56ec4fc960955788c797e80532cc0f1063dd5cadd79ff1fe0e1d5       True
60  edgar/13f/jensen/2025-12-31_0001171200-26-000003.xml  8634ebff01ce9819e76e7939daa936b3c4bb16d1f111d883aec73ff27afffe44  8634ebff01ce9819e76e7939daa936b3c4bb16d1f111d883aec73ff27afffe44       True
61  edgar/13f/jensen/2026-03-31_0001171200-26-000007.xml  6b23a04d0ac252b5b339e8a920b1a41ac3a9a12ad0d2ebc560e8451302da2d18  6b23a04d0ac252b5b339e8a920b1a41ac3a9a12ad0d2ebc560e8451302da2d18       True
62  edgar/13f/jensen/2026-06-30_0001171200-26-000010.xml  fac842c620f6a8b337f57defdfd4255be925f8ed2a5e2c2c027ca812f9782920  fac842c620f6a8b337f57defdfd4255be925f8ed2a5e2c2c027ca812f9782920       True
63   edgar/13f/polen/2019-03-31_0001172661-19-001172.xml  643b637252e1ece2b32c2541eac473f25755495a536862242d5bd4f04a0f0bfc  643b637252e1ece2b32c2541eac473f25755495a536862242d5bd4f04a0f0bfc       True
64   edgar/13f/polen/2019-06-30_0001172661-19-001677.xml  76c713d4f075b9bb7a8e5a22c635d02102f0cf575bd353ed9b01c9f70a1bf3f1  76c713d4f075b9bb7a8e5a22c635d02102f0cf575bd353ed9b01c9f70a1bf3f1       True
65   edgar/13f/polen/2019-09-30_0001172661-19-002155.xml  4b0d4680184b79014b928c4b776b4028ef16f8673e50511149110dcc588d54df  4b0d4680184b79014b928c4b776b4028ef16f8673e50511149110dcc588d54df       True
66   edgar/13f/polen/2019-12-31_0001172661-20-000333.xml  2c9df712e22597b71dd945ff29133d182159b16a051cc8d403a406885cea586b  2c9df712e22597b71dd945ff29133d182159b16a051cc8d403a406885cea586b       True
67   edgar/13f/polen/2020-03-31_0001172661-20-001182.xml  85dadcda5cca4b268398c39088f7c44c0b9cd74e0399cdc34cef4ff0068bca93  85dadcda5cca4b268398c39088f7c44c0b9cd74e0399cdc34cef4ff0068bca93       True
68   edgar/13f/polen/2020-06-30_0001172661-20-001647.xml  edefd439e548d8a13863ffc6ba4eecbdc7a6e8af1e3ebac2d70fad66e0832edb  edefd439e548d8a13863ffc6ba4eecbdc7a6e8af1e3ebac2d70fad66e0832edb       True
69   edgar/13f/polen/2020-09-30_0001172661-20-002092.xml  49b3b3a728815f90deaa862e56729f029e36c7e0d32f2e18d7de5d0df0cd9d89  49b3b3a728815f90deaa862e56729f029e36c7e0d32f2e18d7de5d0df0cd9d89       True
70   edgar/13f/polen/2020-12-31_0001172661-21-000318.xml  49886e9d6619ade50ef1d6e38a4d40fa34136d3792e60227f5b2cf73d99c7499  49886e9d6619ade50ef1d6e38a4d40fa34136d3792e60227f5b2cf73d99c7499       True
71   edgar/13f/polen/2021-03-31_0001172661-21-001092.xml  451234eda0cfa8bc40893369375e98e1364c3c917165f2fd480dd19fa847e68f  451234eda0cfa8bc40893369375e98e1364c3c917165f2fd480dd19fa847e68f       True
72   edgar/13f/polen/2021-06-30_0001172661-21-001640.xml  e3d4945c2348bab83c9701dd436982daf345c63d1af396731b51e3b2b9337e3b  e3d4945c2348bab83c9701dd436982daf345c63d1af396731b51e3b2b9337e3b       True
73   edgar/13f/polen/2021-09-30_0001172661-21-002146.xml  4b3cd95875a926290e471d54e0c81e9e226e040e19c580d9e8a8782dc75c4857  4b3cd95875a926290e471d54e0c81e9e226e040e19c580d9e8a8782dc75c4857       True
74   edgar/13f/polen/2021-12-31_0001172661-22-000331.xml  e3cdc6a046e41975510eeebeaafc04c9d44409a0c7ac71ff20faf5ed9c863062  e3cdc6a046e41975510eeebeaafc04c9d44409a0c7ac71ff20faf5ed9c863062       True
75   edgar/13f/polen/2022-03-31_0001172661-22-001239.xml  8a7b39e5537a4f848bdfc4309c93e5cc99b862bd3bfb62263ecae57d69f4c818  8a7b39e5537a4f848bdfc4309c93e5cc99b862bd3bfb62263ecae57d69f4c818       True
76   edgar/13f/polen/2022-06-30_0001172661-22-001764.xml  4f278ad664a31cc2da153fed5a8a02ca8cd6dfa23740ba73d91c90d9d8071104  4f278ad664a31cc2da153fed5a8a02ca8cd6dfa23740ba73d91c90d9d8071104       True
77   edgar/13f/polen/2022-09-30_0001172661-22-002289.xml  9b61cbe6c8e81adbf1b6074f86ec490ab755d3eb41e12cb9729d0ee60fd2d881  9b61cbe6c8e81adbf1b6074f86ec490ab755d3eb41e12cb9729d0ee60fd2d881       True
78   edgar/13f/polen/2022-12-31_0001172661-23-000805.xml  99564d4c7af4e9c5fe9882032689f552f74da75e0ca9fd86354e8a9ca214f4cc  99564d4c7af4e9c5fe9882032689f552f74da75e0ca9fd86354e8a9ca214f4cc       True
79   edgar/13f/polen/2023-03-31_0001172661-23-002012.xml  b33e5c52f2b282568a591b9d683f4af188dab43b90965c1a71d193fb1acc350e  b33e5c52f2b282568a591b9d683f4af188dab43b90965c1a71d193fb1acc350e       True
80   edgar/13f/polen/2023-06-30_0001172661-23-002916.xml  d55151ed1f4ea84c02f18c7755eb12bbaa5c9c063783be60613ef1c1f8c67c97  d55151ed1f4ea84c02f18c7755eb12bbaa5c9c063783be60613ef1c1f8c67c97       True
81   edgar/13f/polen/2023-09-30_0001172661-23-003726.xml  de15eea970baeeb5f36cd6630972fe1522446a860ef16510aa82c20f47195f65  de15eea970baeeb5f36cd6630972fe1522446a860ef16510aa82c20f47195f65       True
82   edgar/13f/polen/2023-12-31_0001172661-24-000776.xml  2100b5000891be39c9daf99194cf483dad08c6f1129242a0604beb3b9aeb9c33  2100b5000891be39c9daf99194cf483dad08c6f1129242a0604beb3b9aeb9c33       True
83   edgar/13f/polen/2023-12-31_0001172661-24-001616.xml  8c5bcab42482536ae938e06d22e89f29081636e5d205416cc26303027bc1ce7e  8c5bcab42482536ae938e06d22e89f29081636e5d205416cc26303027bc1ce7e       True
84   edgar/13f/polen/2023-12-31_0001172661-24-002148.xml  1a4104131f3a0a0f9a87d0d281ffb05afa1b5917ca80638768d8d16390677115  1a4104131f3a0a0f9a87d0d281ffb05afa1b5917ca80638768d8d16390677115       True
85   edgar/13f/polen/2024-03-31_0001172661-24-002149.xml  eb95ae5eb970ae6dc2a86210d818325ee69e2211a179aaa8aa46cb3930155768  eb95ae5eb970ae6dc2a86210d818325ee69e2211a179aaa8aa46cb3930155768       True
86   edgar/13f/polen/2024-06-30_0001172661-24-003233.xml  658988d7d68a019485ca854fe8183889935b647af1d999a839ec3365dbe00b7e  658988d7d68a019485ca854fe8183889935b647af1d999a839ec3365dbe00b7e       True
87   edgar/13f/polen/2024-09-30_0001172661-24-004624.xml  c2e9a30ec3e06dc5b124fe369a2aa263ec5ed8b60d643410dfd47b1098d034dd  c2e9a30ec3e06dc5b124fe369a2aa263ec5ed8b60d643410dfd47b1098d034dd       True
88   edgar/13f/polen/2024-09-30_0001172661-25-000622.xml  eed80ef58f0423fe7add05389b8219a984b34d3970ddb0f976d178c96f189e90  eed80ef58f0423fe7add05389b8219a984b34d3970ddb0f976d178c96f189e90       True
89   edgar/13f/polen/2024-12-31_0001172661-25-000623.xml  99d2f6e83ab66615c7c368fa9db26fc2c645d80f9934f7b74e0be4849757a4e3  99d2f6e83ab66615c7c368fa9db26fc2c645d80f9934f7b74e0be4849757a4e3       True
90   edgar/13f/polen/2025-03-31_0001172661-25-001713.xml  35ae35f39d63be01dac76f4abf935fc728eec100d282061db7361da14e9dc7d4  35ae35f39d63be01dac76f4abf935fc728eec100d282061db7361da14e9dc7d4       True
91   edgar/13f/polen/2025-06-30_0001172661-25-003133.xml  bd2bfde4dfc5f85248835e6eaffb310a04b543c2a30d7535b62423594f14641b  bd2bfde4dfc5f85248835e6eaffb310a04b543c2a30d7535b62423594f14641b       True
92   edgar/13f/polen/2025-09-30_0001172661-25-004691.xml  c0bfd970e0ede3b81d7a2beb4696e258b9736a6ccc18bcbc169405dbfaf27a60  c0bfd970e0ede3b81d7a2beb4696e258b9736a6ccc18bcbc169405dbfaf27a60       True
93   edgar/13f/polen/2025-12-31_0001172661-26-000654.xml  35f2a5eddcf32d3b9061f6593842cd293e92ea882417e8cdc4507d812a17fd7e  35f2a5eddcf32d3b9061f6593842cd293e92ea882417e8cdc4507d812a17fd7e       True
94   edgar/13f/polen/2026-03-31_0001172661-26-001911.xml  83e4a40d6ed629836e2cb0ce7801aafdedd4891019461cb429a17bb4213bf5b0  83e4a40d6ed629836e2cb0ce7801aafdedd4891019461cb429a17bb4213bf5b0       True
95   edgar/13f/polen/2026-06-30_0001172661-26-003035.xml  6899ef1afa5377ed531f5eaeaa80f504b7c21efe72642cbbacd1ec1b06b7d063  6899ef1afa5377ed531f5eaeaa80f504b7c21efe72642cbbacd1ec1b06b7d063       True
```
```
96 of 96 identical
```
```
the other committed files under data/raw/:
                           file                                                     sha256_before                                                      sha256_after rows_before rows_after  identical
0    edgar/13f/filings_akre.csv  b762e41a70ffb522a07802654098a63d59cd611a92ce01acd39fecf9619c7961  b762e41a70ffb522a07802654098a63d59cd611a92ce01acd39fecf9619c7961         125        125       True
1  edgar/13f/filings_jensen.csv  e5a30a7dce76b841cdf3adfd466edd67e87aeda8bd2ec7b60a85c1160939d634  e5a30a7dce76b841cdf3adfd466edd67e87aeda8bd2ec7b60a85c1160939d634         117        117       True
2   edgar/13f/filings_polen.csv  84189143d31c2c16dd5e3abe99938a069876efe70c2bee56ffe1ba90c7581a50  84189143d31c2c16dd5e3abe99938a069876efe70c2bee56ffe1ba90c7581a50         117        117       True
3   edgar/nport/filings_ivv.csv  6ad691e8b4f72df1a5fd94341247a5681e08f455dba64989319e23fdd37a8991  f2c07eb460da3ae58451cd0868b11c0a65b3bbaa4f1f4ec31fb2685ef0329616          28         29      False
4   edgar/nport/filings_iwf.csv  d27212d049000ee3e1851fb737b6cbdf92d35108f522de68c23cfc868006e6f0  d27212d049000ee3e1851fb737b6cbdf92d35108f522de68c23cfc868006e6f0          28         28       True
5  edgar/nport/holdings_ivv.csv  14c791b34cb28f4943119cfab9709c5358bedda4755de02f48d623abe19eb440  f6f5ca6423422e8326f9b6daed7f1d5d651f0f0f896dbe6ab61e9a121892f84b       14203      14710      False
6  edgar/nport/holdings_iwf.csv  053d197f961f4eee4bd534e3d59f66bb58849a1bc802b6aaca702630db1f2c6a  6efecac85f70cb9ea13258d4bd003631f572a4a7f887561f9c03c0d3a88976e9       12862      12862      False
7   sec/company_tickers_mf.json  f17facb023662f07c36a4809b6a65e65cd336eb3afae8e160d2b665cbe536c38  f17facb023662f07c36a4809b6a65e65cd336eb3afae8e160d2b665cbe536c38                              True
8       sec/series_resolved.csv  dce782156fc755c8edc0422e3dd432b8da622639e7da94bce013929c5cf4ea5e  dce782156fc755c8edc0422e3dd432b8da622639e7da94bce013929c5cf4ea5e           2          2       True
```

### Section E item 10 data/raw/MANIFEST.json

```
{
  "libraries": {
    "lxml": "6.1.3",
    "numpy": "2.5.3",
    "pandas": "3.0.6",
    "python": "3.12.13",
    "requests": "2.34.2"
  },
  "pulled_at_utc": {
    "edgar": "2026-10-02T18:11:25Z"
  },
  "row_counts": {
    "edgar/13f/filings_akre.csv": 125,
    "edgar/13f/filings_jensen.csv": 117,
    "edgar/13f/filings_polen.csv": 117,
    "edgar/nport/filings_ivv.csv": 29,
    "edgar/nport/filings_iwf.csv": 28,
    "edgar/nport/holdings_ivv.csv": 14710,
    "edgar/nport/holdings_iwf.csv": 12862,
    "sec/series_resolved.csv": 2
  },
  "sha256": {
    "edgar/13f/akre/2019-03-31_0001112520-19-000015.xml": "9c802ea6fef4d850c7c8c384618eb1954fb6d226d15ccebea1751df486f138c2",
    "edgar/13f/akre/2019-06-30_0001112520-19-000017.xml": "4c6cb15ee79df7542c40c1a8afbbb6440f1625192e518c335f26062a5c822992",
    "edgar/13f/akre/2019-09-30_0001112520-19-000024.xml": "54783025bdfadae5f1130bcc124264f77e53b8398b4af320f87c95acdf761a05",
    "edgar/13f/akre/2019-12-31_0001112520-20-000010.xml": "33d3c756b05c1b6e46d16cfaaa559b67ddbfb1e3d4882abe4b27d02792d41322",
    "edgar/13f/akre/2020-03-31_0001112520-20-000016.xml": "8272356a13f8bd0dc4b26bc8e3ea893041dbf858e85aa1ad22aeb1a0828de555",
    "edgar/13f/akre/2020-06-30_0001112520-20-000022.xml": "0161aa3e12512991ae0ad2710ca4bb689005907a3064419869db79488da85e7a",
    "edgar/13f/akre/2020-09-30_0001112520-20-000024.xml": "70dde337b9f781be21f13353c651682cda3b04f9eded8ef27f7cd3529439c984",
    "edgar/13f/akre/2020-12-31_0001112520-21-000003.xml": "44e76e574dff7a17f4fc06188ed069dcf3966e51c4a3c4ae320a08604f3e06ed",
    "edgar/13f/akre/2021-03-31_0001112520-21-000012.xml": "a4c90af2249ad8c03a11ffcc1f7e7c6c3ebd64405a65bfcbe249f4580cae549e",
    "edgar/13f/akre/2021-03-31_0001112520-21-000016.xml": "fe4137fca20e1cfc056a4c7c0e7e94b8f7e24dba2112fb035d324987b2e1cb49",
    "edgar/13f/akre/2021-06-30_0001112520-21-000020.xml": "b1a35d4cb8842774fc5e2cfd9ad92e537486748a493faedfabba20b602f7bddd",
    "edgar/13f/akre/2021-09-30_0001112520-21-000023.xml": "48164b6cb6b2db029eb0476948f4c8a119f39c437b0a208c75bf4f73ab3c6a0c",
    "edgar/13f/akre/2021-12-31_0001112520-22-000005.xml": "e1b51756bcf03469267737cd8416c66cbb76d5cf2db27d55ee3f32ec84acc799",
    "edgar/13f/akre/2022-03-31_0001112520-22-000009.xml": "e45e302db161e8b23d291d11298805b9730cae9e4edc8eb86517d3887bd7df6a",
    "edgar/13f/akre/2022-06-30_0001112520-22-000013.xml": "4c071fd59e1f912ca5bd1cc4a6ac4de3f08325862aa6e7f1af63ea960acb562c",
    "edgar/13f/akre/2022-09-30_0001112520-22-000015.xml": "05eaa7923a74b499d657ac32f2c0254bcb397c4a0d16eb7882940377132e1925",
    "edgar/13f/akre/2022-12-31_0001112520-23-000006.xml": "6143a596b6b581bf247e7b8d9b278311bd3363798dbcbcfb4b5428c98e3a9bc1",
    "edgar/13f/akre/2023-03-31_0001112520-23-000008.xml": "5e91a9a2417f8274dfebf70c60faaf8e6426482f72899355ecf71a7c624ac1e4",
    "edgar/13f/akre/2023-06-30_0001112520-23-000013.xml": "439c2e43ef797906c769c2fcbac7f298254d09d9a41aa4870211a5a0a9c5d305",
    "edgar/13f/akre/2023-09-30_0001112520-23-000019.xml": "306ee9731c20b71fab0fedaca5e1199b0a2ba7d8a0770281270b8bcfdebb39f5",
    "edgar/13f/akre/2023-12-31_0001112520-24-000006.xml": "380179b5358956b57b6abc0176bd047efc032b89efb6bfd73f1e140453559f11",
    "edgar/13f/akre/2024-03-31_0001112520-24-000010.xml": "d20bf9f83da524604663bca9332b2b1d6f3c974a26b9d3d8094cb8f81d384bf4",
    "edgar/13f/akre/2024-03-31_0001112520-24-000012.xml": "87b861d6fe80bb1856f62909e9750436ee5a46de5c18afca91458f43e2e51a6a",
    "edgar/13f/akre/2024-06-30_0001112520-24-000014.xml": "2af450eef75f808a1bf00af16e18123b29ac6cc918a6f0928f5433e4a175e2d8",
    "edgar/13f/akre/2024-09-30_0001112520-24-000025.xml": "23b7c35bed9eac5bc04065be56f344cc6d00020b8ac753dab14264840d84451c",
    "edgar/13f/akre/2024-12-31_0001112520-25-000003.xml": "b891b54daa2ba597a8dbfc17593d0ee93b1c5d599474f24f2da9d9f3bdd99409",
    "edgar/13f/akre/2025-03-31_0001112520-25-000015.xml": "9b7f24d68534dda74cc83d1b7c3bcfcbc08fa5e08234f4b1b6288f74dd41eeb8",
    "edgar/13f/akre/2025-06-30_0001112520-25-000019.xml": "da7a924817e0983b6eab1ba163c663cf0d48dff7faeb9807f78e7df7c9a50b71",
    "edgar/13f/akre/2025-09-30_0001112520-25-000029.xml": "e923a4cca9199f0698611aa25bada88e754fa13ba8e7f235f30ae0ae5c300866",
    "edgar/13f/akre/2025-12-31_0001112520-26-000008.xml": "a8fc1019b8a146a7a63d3766757a617ab3cb1ea6d0f26555f60681c0af0e2cb4",
    "edgar/13f/akre/2026-03-31_0001112520-26-000009.xml": "68f9b140a43ad70c6de441ec73382a6fe11f69a8e6f5db371b688c070b1af5a8",
    "edgar/13f/akre/2026-06-30_0001112520-26-000014.xml": "b038bfc6641c7b120128f2549a7689ef839fb370d796cd4f323af9aa852fa6b5",
    "edgar/13f/filings_akre.csv": "b762e41a70ffb522a07802654098a63d59cd611a92ce01acd39fecf9619c7961",
    "edgar/13f/filings_jensen.csv": "e5a30a7dce76b841cdf3adfd466edd67e87aeda8bd2ec7b60a85c1160939d634",
    "edgar/13f/filings_polen.csv": "84189143d31c2c16dd5e3abe99938a069876efe70c2bee56ffe1ba90c7581a50",
    "edgar/13f/jensen/2019-03-31_0001171200-19-000211.xml": "14a54b67bff3904814bec2e09f16e493a449e54cf78c36223e719606b15077c7",
    "edgar/13f/jensen/2019-06-30_0001171200-19-000284.xml": "c53158c335f01ba5e7c175fd669bea7ebf166ced0f29f6abe70999dc248ebb11",
    "edgar/13f/jensen/2019-09-30_0001171200-19-000366.xml": "7f004a9e430f90051ddd8250e38d0d8926b44c2dc557340da15c4377a5b45eae",
    "edgar/13f/jensen/2019-12-31_0001171200-20-000061.xml": "4edf0d251271b2132da6392c5a0e4b9fba4f4f57bb4798669f2fab14f53044ce",
    "edgar/13f/jensen/2020-03-31_0001171200-20-000338.xml": "017d7e05019e0fda87250d05aacf9bb1559d9426fe2c83d4d0c7bb4384bc73da",
    "edgar/13f/jensen/2020-06-30_0001171200-20-000521.xml": "31a25e853f8da4e86b658e65e9da09f6bf59dc865833927e19c825ced6420dec",
    "edgar/13f/jensen/2020-09-30_0001171200-20-000622.xml": "7ad0fecf3c747b5f06e6aa9be8841ec0a068c36c99f5b713f5a749e0e68537d0",
    "edgar/13f/jensen/2020-12-31_0001171200-21-000057.xml": "37cfe2a3fc65583c3636535b3af49543ca5be888f080b0947943ec578bbd48ab",
    "edgar/13f/jensen/2021-03-31_0001171200-21-000236.xml": "537019a72aea297b488ac89155cdaae9eafcabf719b27491cf19e963b619ccdd",
    "edgar/13f/jensen/2021-06-30_0001171200-21-000290.xml": "b28c4c1912f99a12a2d081109c16e39291e0166464842a88f1f9d232bd5be7ec",
    "edgar/13f/jensen/2021-09-30_0001171200-21-000388.xml": "7dc55aaa0e99c40e91bd7f144f9a566d5f27706d4ad73ec0854e59e517a471ab",
    "edgar/13f/jensen/2021-12-31_0001171200-22-000037.xml": "33cce176c2870d4f2d0603b801afa801c611aa9361abe68c4e7e9c04e6afae6b",
    "edgar/13f/jensen/2022-03-31_0001171200-22-000245.xml": "72e01f46dc68b0418a21bf906fd88721ccd4c91c6776df4124dff5124705a093",
    "edgar/13f/jensen/2022-06-30_0001171200-22-000293.xml": "54f097769c64651a44f6c51de3adbbaef5a6b53e10783038aa5110ec502a3296",
    "edgar/13f/jensen/2022-09-30_0001171200-22-000347.xml": "d3d9bb6aff0dd9356653a87a8cbd75eae5afa3551bc215c3bb7eeacd9fa7bd0d",
    "edgar/13f/jensen/2022-12-31_0001171200-23-000057.xml": "bc7698e12c9a44569a690f074812d6ea77f6585ff8ef872d4ab22b808358efb3",
    "edgar/13f/jensen/2022-12-31_0001171200-23-000206.xml": "0bcbab4c042a1e855069c96d02e6a6fcfa5bc53189f0532f40d4104c0e37a7be",
    "edgar/13f/jensen/2023-03-31_0001171200-23-000298.xml": "324fe6f58e1e7bb635f97a361f64961e6dd87de56043dc96ddc1279229c1725d",
    "edgar/13f/jensen/2023-06-30_0001171200-23-000356.xml": "82a53ed673f9d5d8ff0d97f38ad49a2bceb773a4e0d783195de7b502ba4c70f8",
    "edgar/13f/jensen/2023-09-30_0001171200-23-000445.xml": "387259c30000d478b6f59b77443854d305ab9dd4b905441a9e595ad2e90969d1",
    "edgar/13f/jensen/2023-12-31_0001171200-24-000016.xml": "ff514adde12353e6bb011c88a45969082412ad79213d50d259575435a1bffb6d",
    "edgar/13f/jensen/2024-03-31_0001171200-24-000202.xml": "eda5ff5629d192abc800451565c1f35be9ece57e9dad035287c7f5486e8d92e8",
    "edgar/13f/jensen/2024-06-30_0001171200-24-000243.xml": "ba5f930f80997b8fc18b0d1ab2ca867131f75613bda4a86bfaf34d1a823c1cd0",
    "edgar/13f/jensen/2024-09-30_0001171200-24-000330.xml": "587cf76743926b770144efd803441d212880dc39353ab71624e502581b72f83a",
    "edgar/13f/jensen/2024-12-31_0001171200-25-000017.xml": "c158f585d132dc4f99923b57070137a69ee89cb5802f6e12957eef437c021d1e",
    "edgar/13f/jensen/2025-03-31_0001171200-25-000219.xml": "177588de79a8252eeef29cb11b0a91f91a2d445df6ad9349129c7a90c949b025",
    "edgar/13f/jensen/2025-06-30_0001171200-25-000262.xml": "b16507dde3f1b4a64c42b5bf51d2e801b882a490053e7651ffa2ff0a198505bf",
    "edgar/13f/jensen/2025-09-30_0001171200-25-000265.xml": "3fcbf1a379d56ec4fc960955788c797e80532cc0f1063dd5cadd79ff1fe0e1d5",
    "edgar/13f/jensen/2025-12-31_0001171200-26-000003.xml": "8634ebff01ce9819e76e7939daa936b3c4bb16d1f111d883aec73ff27afffe44",
    "edgar/13f/jensen/2026-03-31_0001171200-26-000007.xml": "6b23a04d0ac252b5b339e8a920b1a41ac3a9a12ad0d2ebc560e8451302da2d18",
    "edgar/13f/jensen/2026-06-30_0001171200-26-000010.xml": "fac842c620f6a8b337f57defdfd4255be925f8ed2a5e2c2c027ca812f9782920",
    "edgar/13f/polen/2019-03-31_0001172661-19-001172.xml": "643b637252e1ece2b32c2541eac473f25755495a536862242d5bd4f04a0f0bfc",
    "edgar/13f/polen/2019-06-30_0001172661-19-001677.xml": "76c713d4f075b9bb7a8e5a22c635d02102f0cf575bd353ed9b01c9f70a1bf3f1",
    "edgar/13f/polen/2019-09-30_0001172661-19-002155.xml": "4b0d4680184b79014b928c4b776b4028ef16f8673e50511149110dcc588d54df",
    "edgar/13f/polen/2019-12-31_0001172661-20-000333.xml": "2c9df712e22597b71dd945ff29133d182159b16a051cc8d403a406885cea586b",
    "edgar/13f/polen/2020-03-31_0001172661-20-001182.xml": "85dadcda5cca4b268398c39088f7c44c0b9cd74e0399cdc34cef4ff0068bca93",
    "edgar/13f/polen/2020-06-30_0001172661-20-001647.xml": "edefd439e548d8a13863ffc6ba4eecbdc7a6e8af1e3ebac2d70fad66e0832edb",
    "edgar/13f/polen/2020-09-30_0001172661-20-002092.xml": "49b3b3a728815f90deaa862e56729f029e36c7e0d32f2e18d7de5d0df0cd9d89",
    "edgar/13f/polen/2020-12-31_0001172661-21-000318.xml": "49886e9d6619ade50ef1d6e38a4d40fa34136d3792e60227f5b2cf73d99c7499",
    "edgar/13f/polen/2021-03-31_0001172661-21-001092.xml": "451234eda0cfa8bc40893369375e98e1364c3c917165f2fd480dd19fa847e68f",
    "edgar/13f/polen/2021-06-30_0001172661-21-001640.xml": "e3d4945c2348bab83c9701dd436982daf345c63d1af396731b51e3b2b9337e3b",
    "edgar/13f/polen/2021-09-30_0001172661-21-002146.xml": "4b3cd95875a926290e471d54e0c81e9e226e040e19c580d9e8a8782dc75c4857",
    "edgar/13f/polen/2021-12-31_0001172661-22-000331.xml": "e3cdc6a046e41975510eeebeaafc04c9d44409a0c7ac71ff20faf5ed9c863062",
    "edgar/13f/polen/2022-03-31_0001172661-22-001239.xml": "8a7b39e5537a4f848bdfc4309c93e5cc99b862bd3bfb62263ecae57d69f4c818",
    "edgar/13f/polen/2022-06-30_0001172661-22-001764.xml": "4f278ad664a31cc2da153fed5a8a02ca8cd6dfa23740ba73d91c90d9d8071104",
    "edgar/13f/polen/2022-09-30_0001172661-22-002289.xml": "9b61cbe6c8e81adbf1b6074f86ec490ab755d3eb41e12cb9729d0ee60fd2d881",
    "edgar/13f/polen/2022-12-31_0001172661-23-000805.xml": "99564d4c7af4e9c5fe9882032689f552f74da75e0ca9fd86354e8a9ca214f4cc",
    "edgar/13f/polen/2023-03-31_0001172661-23-002012.xml": "b33e5c52f2b282568a591b9d683f4af188dab43b90965c1a71d193fb1acc350e",
    "edgar/13f/polen/2023-06-30_0001172661-23-002916.xml": "d55151ed1f4ea84c02f18c7755eb12bbaa5c9c063783be60613ef1c1f8c67c97",
    "edgar/13f/polen/2023-09-30_0001172661-23-003726.xml": "de15eea970baeeb5f36cd6630972fe1522446a860ef16510aa82c20f47195f65",
    "edgar/13f/polen/2023-12-31_0001172661-24-000776.xml": "2100b5000891be39c9daf99194cf483dad08c6f1129242a0604beb3b9aeb9c33",
    "edgar/13f/polen/2023-12-31_0001172661-24-001616.xml": "8c5bcab42482536ae938e06d22e89f29081636e5d205416cc26303027bc1ce7e",
    "edgar/13f/polen/2023-12-31_0001172661-24-002148.xml": "1a4104131f3a0a0f9a87d0d281ffb05afa1b5917ca80638768d8d16390677115",
    "edgar/13f/polen/2024-03-31_0001172661-24-002149.xml": "eb95ae5eb970ae6dc2a86210d818325ee69e2211a179aaa8aa46cb3930155768",
    "edgar/13f/polen/2024-06-30_0001172661-24-003233.xml": "658988d7d68a019485ca854fe8183889935b647af1d999a839ec3365dbe00b7e",
    "edgar/13f/polen/2024-09-30_0001172661-24-004624.xml": "c2e9a30ec3e06dc5b124fe369a2aa263ec5ed8b60d643410dfd47b1098d034dd",
    "edgar/13f/polen/2024-09-30_0001172661-25-000622.xml": "eed80ef58f0423fe7add05389b8219a984b34d3970ddb0f976d178c96f189e90",
    "edgar/13f/polen/2024-12-31_0001172661-25-000623.xml": "99d2f6e83ab66615c7c368fa9db26fc2c645d80f9934f7b74e0be4849757a4e3",
    "edgar/13f/polen/2025-03-31_0001172661-25-001713.xml": "35ae35f39d63be01dac76f4abf935fc728eec100d282061db7361da14e9dc7d4",
    "edgar/13f/polen/2025-06-30_0001172661-25-003133.xml": "bd2bfde4dfc5f85248835e6eaffb310a04b543c2a30d7535b62423594f14641b",
    "edgar/13f/polen/2025-09-30_0001172661-25-004691.xml": "c0bfd970e0ede3b81d7a2beb4696e258b9736a6ccc18bcbc169405dbfaf27a60",
    "edgar/13f/polen/2025-12-31_0001172661-26-000654.xml": "35f2a5eddcf32d3b9061f6593842cd293e92ea882417e8cdc4507d812a17fd7e",
    "edgar/13f/polen/2026-03-31_0001172661-26-001911.xml": "83e4a40d6ed629836e2cb0ce7801aafdedd4891019461cb429a17bb4213bf5b0",
    "edgar/13f/polen/2026-06-30_0001172661-26-003035.xml": "6899ef1afa5377ed531f5eaeaa80f504b7c21efe72642cbbacd1ec1b06b7d063",
    "edgar/nport/filings_ivv.csv": "f2c07eb460da3ae58451cd0868b11c0a65b3bbaa4f1f4ec31fb2685ef0329616",
    "edgar/nport/filings_iwf.csv": "d27212d049000ee3e1851fb737b6cbdf92d35108f522de68c23cfc868006e6f0",
    "edgar/nport/holdings_ivv.csv": "f6f5ca6423422e8326f9b6daed7f1d5d651f0f0f896dbe6ab61e9a121892f84b",
    "edgar/nport/holdings_iwf.csv": "6efecac85f70cb9ea13258d4bd003631f572a4a7f887561f9c03c0d3a88976e9",
    "sec/company_tickers_mf.json": "f17facb023662f07c36a4809b6a65e65cd336eb3afae8e160d2b665cbe536c38",
    "sec/series_resolved.csv": "dce782156fc755c8edc0422e3dd432b8da622639e7da94bce013929c5cf4ea5e"
  },
  "uncommitted_sha256": {
    "edgar/nport/ivv/2019-09-30_0001752724-19-177847.xml": {
      "form": "NPORT-P",
      "sha256": "a8ad5728461a9ae02699c276accdccb7a865a15140a31a2cddcebfe7a1b64418",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272419177847/primary_doc.xml"
    },
    "edgar/nport/ivv/2019-12-31_0001752724-20-038725.xml": {
      "form": "NPORT-P",
      "sha256": "436a491e534ef88d51249581a2acaa34b6deb8b056ad9f3561ec26658cff4deb",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272420038725/primary_doc.xml"
    },
    "edgar/nport/ivv/2020-03-31_0001752724-20-112027.xml": {
      "form": "NPORT-P",
      "sha256": "4c99610a77d3e073a708710c1477652d87f9ce68f315afa27185e16e22d463bb",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272420112027/primary_doc.xml"
    },
    "edgar/nport/ivv/2020-06-30_0001752724-20-176909.xml": {
      "form": "NPORT-P",
      "sha256": "f8c05eadc5b70080b181deaa88d0ecba3745aaaf2226ae48186b8d6383d00770",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272420176909/primary_doc.xml"
    },
    "edgar/nport/ivv/2020-09-30_0001752724-20-247818.xml": {
      "form": "NPORT-P",
      "sha256": "406e2973c57d0af17ecafc5feef7063c1bc5c1da1d3d29f6dcbe7e90ad51ee15",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272420247818/primary_doc.xml"
    },
    "edgar/nport/ivv/2020-12-31_0001752724-21-040719.xml": {
      "form": "NPORT-P",
      "sha256": "9a7586edadcce2c0b90f5aa08f281cf8098a09cbad5cff0b54eb769e422f4afc",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272421040719/primary_doc.xml"
    },
    "edgar/nport/ivv/2021-03-31_0001752724-21-116363.xml": {
      "form": "NPORT-P",
      "sha256": "4f10902d236dc0ea71dda6789a1dd47edab706beac5aa5000ecc1e31cd5e1e2e",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272421116363/primary_doc.xml"
    },
    "edgar/nport/ivv/2021-06-30_0001752724-21-186201.xml": {
      "form": "NPORT-P",
      "sha256": "580584dca74ffabfbcb0b3733c664c476838a0a0986115ca4243c98c1a7d0a62",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272421186201/primary_doc.xml"
    },
    "edgar/nport/ivv/2021-09-30_0001752724-21-255857.xml": {
      "form": "NPORT-P",
      "sha256": "9c6b17b707e6d60232d2227655a64998b919b91e9c6f085e8fd3cdd5031cebc8",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272421255857/primary_doc.xml"
    },
    "edgar/nport/ivv/2021-12-31_0001752724-22-046281.xml": {
      "form": "NPORT-P",
      "sha256": "d9ea9f4ad33589364a8fb0b061ef3686f0b2c7dd3c2a5bfe35ddca1249875546",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272422046281/primary_doc.xml"
    },
    "edgar/nport/ivv/2022-03-31_0001752724-22-122805.xml": {
      "form": "NPORT-P",
      "sha256": "a430f88ae10cb7f0a1d5caa1d864e6ef57edd21845e35276bfc8502880f12c3f",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272422122805/primary_doc.xml"
    },
    "edgar/nport/ivv/2022-06-30_0001752724-22-193652.xml": {
      "form": "NPORT-P",
      "sha256": "aef1dfc3287356459f79a9331ea15d473b8cf2a5add863098fcf22ed51912294",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272422193652/primary_doc.xml"
    },
    "edgar/nport/ivv/2022-09-30_0001752724-22-268673.xml": {
      "form": "NPORT-P",
      "sha256": "86aaa8b4f08c5e9c2b9192bf895f09da509220cd185abdfd8cce6256e30fbae3",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272422268673/primary_doc.xml"
    },
    "edgar/nport/ivv/2022-12-31_0001752724-23-039243.xml": {
      "form": "NPORT-P",
      "sha256": "cbedf22f3dcc4125c0101577e34094e5ebc23b40f35e4a0524f8cad053e606fe",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272423039243/primary_doc.xml"
    },
    "edgar/nport/ivv/2023-03-31_0001752724-23-123220.xml": {
      "form": "NPORT-P",
      "sha256": "6985b68805b64f7a5855c9c6e1b8b3a69bc733f508164d66b686d769f39efdf4",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272423123220/primary_doc.xml"
    },
    "edgar/nport/ivv/2023-06-30_0001752724-23-191503.xml": {
      "form": "NPORT-P",
      "sha256": "880c14e3a7f46ae08e7953d41d5809178bd9bcae13c5461f9bb71a0f944543eb",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272423191503/primary_doc.xml"
    },
    "edgar/nport/ivv/2023-09-30_0001752724-23-264277.xml": {
      "form": "NPORT-P",
      "sha256": "2c05fb9a33bce24b332529b02a1b8e9c929f737bdb1343b9d5731526bbf1420c",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272423264277/primary_doc.xml"
    },
    "edgar/nport/ivv/2023-12-31_0001752724-24-043113.xml": {
      "form": "NPORT-P",
      "sha256": "09392c3b791f8362b1417132174aa0d4638eef1540fa38f5a931c08a5f997841",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272424043113/primary_doc.xml"
    },
    "edgar/nport/ivv/2024-03-31_0001752724-24-123331.xml": {
      "form": "NPORT-P",
      "sha256": "1a47c29eb9170b35676891faa6e589c1b3beeb449130680b6905c52524fe3ee5",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272424123331/primary_doc.xml"
    },
    "edgar/nport/ivv/2024-06-30_0001752724-24-194289.xml": {
      "form": "NPORT-P",
      "sha256": "90f811e92de7400b7f97badf4db3a635d6053c5b9de304a34e271b09508249d2",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272424194289/primary_doc.xml"
    },
    "edgar/nport/ivv/2024-09-30_0001752724-24-269943.xml": {
      "form": "NPORT-P",
      "sha256": "8ac677d7db72db7f73808cf46115c6629f9accb3273287ca2be863ef9ea4e33e",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272424269943/primary_doc.xml"
    },
    "edgar/nport/ivv/2024-12-31_0001752724-25-043800.xml": {
      "form": "NPORT-P",
      "sha256": "68398fe4f2bd7602650fb68e8f7192ac3119ef4a281f4a4c758cc5abe1ad1f49",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272425043800/primary_doc.xml"
    },
    "edgar/nport/ivv/2025-03-31_0001752724-25-119791.xml": {
      "form": "NPORT-P",
      "sha256": "5c131afc756820cc7b4b89f8eb9cd2445624ce26da0e601dfa064de1b4911571",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272425119791/primary_doc.xml"
    },
    "edgar/nport/ivv/2025-06-30_0001752724-25-210389.xml": {
      "form": "NPORT-P",
      "sha256": "55308af31eda702c5b1033a868cfe66f02f578aa6215a081f01bf13cf0a94c7f",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272425210389/primary_doc.xml"
    },
    "edgar/nport/ivv/2025-09-30_0002071691-25-007634.xml": {
      "form": "NPORT-P",
      "sha256": "f77988290be2e35e0b553f7f4146b182a97e0d659689455adb766aba930c0b1e",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000207169125007634/primary_doc.xml"
    },
    "edgar/nport/ivv/2025-09-30_0002071691-26-015790.xml": {
      "form": "NPORT-P/A",
      "sha256": "4732db6d3bbc5c16dfe777de3c8a9ea88260a9e4bb22eea14edccdb9a6b37104",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000207169126015790/primary_doc.xml"
    },
    "edgar/nport/ivv/2025-12-31_0002071691-26-004238.xml": {
      "form": "NPORT-P",
      "sha256": "146ce98ea43e10ae2d729ca663f07cb4a7728907a671c6f3b2b7ee3fb0219c31",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000207169126004238/primary_doc.xml"
    },
    "edgar/nport/ivv/2026-03-31_0002071691-26-012459.xml": {
      "form": "NPORT-P",
      "sha256": "b7acb48358d9d7d52ba45955b46442570e1d3b92c6c6d8386756fbf2aa806a00",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000207169126012459/primary_doc.xml"
    },
    "edgar/nport/ivv/2026-06-30_0002071691-26-019760.xml": {
      "form": "NPORT-P",
      "sha256": "9924e5b86bf304d0c2d24679e15642b681de6605ed38ca8b1bb1db7aa5b3b7e9",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000207169126019760/primary_doc.xml"
    },
    "edgar/nport/iwf/2019-09-30_0001752724-19-177844.xml": {
      "form": "NPORT-P",
      "sha256": "ec1c5c8ba57a2db0481b34127763448ad7391ffc702e90ffb895f9ef2dad9450",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272419177844/primary_doc.xml"
    },
    "edgar/nport/iwf/2019-12-31_0001752724-20-038663.xml": {
      "form": "NPORT-P",
      "sha256": "737cd39191713ea7d4a05ecd46cd2d04f27437e070d29c3e918fa0a58f7edb46",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272420038663/primary_doc.xml"
    },
    "edgar/nport/iwf/2020-03-31_0001752724-20-112153.xml": {
      "form": "NPORT-P",
      "sha256": "67b952911581842d15773d0de6d644bd1d9f195a511c3d389dec71701d619e0e",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272420112153/primary_doc.xml"
    },
    "edgar/nport/iwf/2020-06-30_0001752724-20-176978.xml": {
      "form": "NPORT-P",
      "sha256": "373539ef678358e6b4bcc03466afb0de67f0f2f7c1c6e819841cf14ab811e82f",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272420176978/primary_doc.xml"
    },
    "edgar/nport/iwf/2020-09-30_0001752724-20-247763.xml": {
      "form": "NPORT-P",
      "sha256": "cb6112d312c84710e156ab21e4f98edf1f025c93e1389c0094219e0f35a59842",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272420247763/primary_doc.xml"
    },
    "edgar/nport/iwf/2020-12-31_0001752724-21-040696.xml": {
      "form": "NPORT-P",
      "sha256": "832567ac1426e1f0d686a59ac32fed5474529ed391dab4eaf87726f5df7aa69a",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272421040696/primary_doc.xml"
    },
    "edgar/nport/iwf/2021-03-31_0001752724-21-116383.xml": {
      "form": "NPORT-P",
      "sha256": "82dff5b503a7a985c4598ff01032eb970f39452481e10305f9f99f22e5641db4",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272421116383/primary_doc.xml"
    },
    "edgar/nport/iwf/2021-06-30_0001752724-21-186226.xml": {
      "form": "NPORT-P",
      "sha256": "1c0e91d019ca8c1729112ea56f8722b38810e5d2ec8c2902bd960562363316ea",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272421186226/primary_doc.xml"
    },
    "edgar/nport/iwf/2021-09-30_0001752724-21-255846.xml": {
      "form": "NPORT-P",
      "sha256": "9ec0326b29f83372fee7b4f368dcbb781de98d5022b2a0a089dd0424527636ba",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272421255846/primary_doc.xml"
    },
    "edgar/nport/iwf/2021-12-31_0001752724-22-046298.xml": {
      "form": "NPORT-P",
      "sha256": "34928ebfb4f5fe0a76edfc43ce8dd71ae5edb31555f4ad7ede34980155a8d210",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272422046298/primary_doc.xml"
    },
    "edgar/nport/iwf/2022-03-31_0001752724-22-122801.xml": {
      "form": "NPORT-P",
      "sha256": "e088b1325ef41ceb873267a92c2e73e600047e71952f8e2b4589742f84a5afe4",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272422122801/primary_doc.xml"
    },
    "edgar/nport/iwf/2022-06-30_0001752724-22-193669.xml": {
      "form": "NPORT-P",
      "sha256": "346a9b27709462ad9a6bda56042bd8962e2ff01ab98c5b7f807c5819f6680f10",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272422193669/primary_doc.xml"
    },
    "edgar/nport/iwf/2022-09-30_0001752724-22-269723.xml": {
      "form": "NPORT-P",
      "sha256": "659df25bf856681d908fe5cb70f35f3488939c4261ef130f9d1d50838a3b95fb",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272422269723/primary_doc.xml"
    },
    "edgar/nport/iwf/2022-12-31_0001752724-23-039553.xml": {
      "form": "NPORT-P",
      "sha256": "dc53ee178139caaa1d5180a608e5342d15e92e1c5eee96632fc11559bb8c903e",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272423039553/primary_doc.xml"
    },
    "edgar/nport/iwf/2023-03-31_0001752724-23-114945.xml": {
      "form": "NPORT-P",
      "sha256": "bcf46c9aca66dd401c3ab1319360a4cd8395560899e55dc8deac16d3168a4720",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272423114945/primary_doc.xml"
    },
    "edgar/nport/iwf/2023-06-30_0001752724-23-192397.xml": {
      "form": "NPORT-P",
      "sha256": "5e59a3763f290d47fdd119842237cd849e07a80749dbfef043503bb7786c8a42",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272423192397/primary_doc.xml"
    },
    "edgar/nport/iwf/2023-09-30_0001752724-23-265163.xml": {
      "form": "NPORT-P",
      "sha256": "a4d0f8d2f11f078390fd1458243487ebdb52d9b36517b1b01865cd0dda9d4d2f",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272423265163/primary_doc.xml"
    },
    "edgar/nport/iwf/2023-12-31_0001752724-24-034941.xml": {
      "form": "NPORT-P",
      "sha256": "73d298390e6d4f931bea1586a60d3ac03bc26027aad8649384873ac54054f085",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272424034941/primary_doc.xml"
    },
    "edgar/nport/iwf/2024-03-31_0001752724-24-118346.xml": {
      "form": "NPORT-P",
      "sha256": "85ecba30ed96e0648c3944141615aa690b8dde64ae8270e6cedde85d0b6012dd",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272424118346/primary_doc.xml"
    },
    "edgar/nport/iwf/2024-06-30_0001752724-24-189692.xml": {
      "form": "NPORT-P",
      "sha256": "6dd63fe7444ddd83d1f54902c2ebd2927239206f0fdfdc86247f1bd078f75316",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272424189692/primary_doc.xml"
    },
    "edgar/nport/iwf/2024-09-30_0001752724-24-268863.xml": {
      "form": "NPORT-P",
      "sha256": "13b27b3a7e0f2b58f10415ccbe0db7ab9b3d289e9b9ffb1163e7ee55feb0dbc6",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272424268863/primary_doc.xml"
    },
    "edgar/nport/iwf/2024-12-31_0001752724-25-034056.xml": {
      "form": "NPORT-P",
      "sha256": "3fee08000f1de837f7811ea9af0ebff59354e2c5ba4ee3ec3c744271e6f73cea",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272425034056/primary_doc.xml"
    },
    "edgar/nport/iwf/2025-03-31_0001752724-25-118601.xml": {
      "form": "NPORT-P",
      "sha256": "3cf8dc8dafedf436bab8e0f1fe46a0c42da801c596e4e99b3781b295ecae3761",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272425118601/primary_doc.xml"
    },
    "edgar/nport/iwf/2025-06-30_0001752724-25-204350.xml": {
      "form": "NPORT-P",
      "sha256": "7221fd32eb2600a276c62224c494f81037c77fd5bf2b088f6f52eba0a2c3cf4a",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000175272425204350/primary_doc.xml"
    },
    "edgar/nport/iwf/2025-09-30_0001004726-25-002059.xml": {
      "form": "NPORT-P",
      "sha256": "7fe35c56f45a39044315248f18a9f59f7f4e2338f62e597d3543ddc70ad7f744",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000100472625002059/primary_doc.xml"
    },
    "edgar/nport/iwf/2025-12-31_0001004726-26-000787.xml": {
      "form": "NPORT-P",
      "sha256": "72166c72baee7b302eba7cbf6767624350e2de06d198c78fc0630fb246f8b1f7",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000100472626000787/primary_doc.xml"
    },
    "edgar/nport/iwf/2026-03-31_0001004726-26-003755.xml": {
      "form": "NPORT-P",
      "sha256": "10cc0e4b980e8338508fa987c3155753a2d51ff19c42d0bbc7eaa441249a9a07",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000100472626003755/primary_doc.xml"
    },
    "edgar/nport/iwf/2026-06-30_0001004726-26-007047.xml": {
      "form": "NPORT-P",
      "sha256": "c66e19366e1623ac3e479745b3790fdc204efb16f228a95f9a633a80cf90a6e8",
      "url": "https://www.sec.gov/Archives/edgar/data/1100663/000100472626007047/primary_doc.xml"
    }
  }
}
```

### How 01b D item 3 recomputes the totals

The review script does not go through `attrib/`.

- **13F:** it reads every `value` element of the committed XML with lxml and multiplies by 1000 when the filing date is before `units_switch_date`.
- **N-PORT:** it reads `holdings_ivv.csv` as strings and converts each `val_usd` with `float()`.

```python
for p in files:                                   # data/raw/edgar/13f/{eid}/{period}_*.xml
    for v in etree.fromstring(p.read_bytes()).iter("{*}value"):
        total += int(v.text.strip()) * mult       # mult = 1000 if filed < 2023-01-03 else 1
...
vals = str_csv(RAW / "edgar" / "nport" / "holdings_ivv.csv")
vals = vals[vals["accession"] == c["amendments_used"]]["val_usd"].map(float)
total = float(vals.sum())
```

For IVV, `coverage.csv` holds `889159485657.55005`, the `%.17g` text, and the recomputation's `repr` is `889159485657.55`. Both are the same float64, so the difference is exactly 0. Under `%.10g` the akre 2023-06-30 total of 12,003,999,013 had been written as 12,003,999,010. The check over all 84 fund rows is the reviewer's A.3 check, rerun: 0 rows now differ, against 23 rows off by $1 to $5 before.

### Section E item 1: this section's commits

```
fb2eee2 step 1.6b: rerun section 1 on 28 dates
2ab736d step 1.5b: re-pull EDGAR with %.17g and NPORT-P/A
d46da92 step 1.4b: keep ISIN-only equity rows, accept NPORT-P/A
62f5b3d step 1.2b: HTTP timeout and retry on connection errors
883bdb2 instructions: 01b section 1 completion
e5dba91 session 1: review and status (stopped at 1.6, 2019 N-PORT books missing)
15809d3 step 1.6: holdings books and coverage (stopped: 4 N-PORT books missing)
99ca50f step 1.5: EDGAR pull, raw filings and holdings, manifest
2eb360a step 1.4: N-PORT parsing, IVV fixture and tests
49435ea step 1.3: 13F parsing, Akre fixtures and tests
dda8105 session 1: review and status (stopped at 1.3, SEC_USER_AGENT unset)
4b1e319 step 1.2: EDGAR client with rate limit and retries
bf10c0e step 1.1: config loader and tests
50a2892 step 1.0: apply session 0 decisions
```

## Tests run

`.venv/Scripts/python.exe -m pytest -p socket --disable-socket -q` (CPython 3.12.13):

```
..........................                                               [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\Utkarsh\10. Quant Projects\6) Attribution Engine On Real Holdings\repo-clone\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
26 passed, 1 warning in 0.73s
```

The warning comes from `-p socket` loading pytest-socket a second time, because the plugin is also registered through its entry point. It does not affect the run.

## Fresh-clone check

01b Section E says to push once, at the end. So this check cloned the local committed `main` at `fb2eee2`, the head of the commits that are pushed, rather than the GitHub copy (see Deviations). The clone went into `C:\t\s1b`, followed by `uv venv --python 3.12`, `uv pip install -r requirements-lock.txt`, `uv pip install -e . --no-deps` and `pytest -p socket --disable-socket -q`. Each install's output is trimmed to its last lines:

```
$ git clone -q '/c/Utkarsh/10. Quant Projects/6) Attribution Engine On Real Holdings/repo-clone' /c/t/s1b
$ git log --oneline -1
fb2eee2 step 1.6b: rerun section 1 on 28 dates
$ uv venv --python 3.12
Using CPython 3.12.13
Creating virtual environment at: .venv
Activate with: .venv\Scripts\activate
$ uv pip install -r requirements-lock.txt
 + wrapt==2.5.0
 + yfinance==1.7.0
$ uv pip install -e . --no-deps
 + attrib==0.0.0 (from file:///C:/t/s1b)
$ .venv/Scripts/python.exe -m pytest -p socket --disable-socket -q
..........................                                               [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\_pytest\config\__init__.py:864
  C:\t\s1b\.venv\Lib\site-packages\_pytest\config\__init__.py:864: PytestAssertRewriteWarning: Module already imported so cannot be rewritten; socket
    self.import_plugin(arg, consider_entry_points=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
26 passed, 1 warning in 6.01s
```

`python scripts/run_all.py --section 1` in the clone printed `section 1: all checks passed`. It reproduced the committed `coverage.csv` and the 5 holdings books byte for byte (sha256 under "Section 1 run" above).

## Runtime per step

- 1.0: lock compile plus venv rebuild, under 1 minute.
- 1.3 and 1.4: `--stage fixtures`, 32 s for the Akre part, then about 1 minute with IVV.
- 1.5: `--stage edgar`, 2 min 32 s.
- 1.6: `run_all.py --section 1`, 3.1 s.
- 1.2b and 1.4b: code and tests only; the suite runs in under 1 s.
- 1.5b: `--stage edgar`, 2 min 9 s.
- 1.6b: `run_all.py --section 1`, 4.4 s.

## Deviations from PLAN.md

Carried over from session 1, accepted in 01b Section B:

- 1.0: the generic `**OPEN-NN**` in the `PLAN.md` preamble was left as written. All 33 numbered markers are `D-NN`.
- 1.3: text-era 13F filings (no `primary_doc.xml`, all before 2013) get a blank `infotable_name` and `amendment_type`.
- 1.3 and 1.4: `entity` is filled by the caller (`pull_data.py`). The same holds for `accession` in `parse_nport`.
- 1.5: uncommitted N-PORT XML hashes are kept in `MANIFEST.json` under `uncommitted_sha256`.
- 1.6 `coverage.csv` columns:
  - `filing_date` and `lag_days` belong to the filing the book starts from.
  - `n_rows_kept` counts kept equity rows before same-id aggregation.
  - `median_implied_price` is `units_check` on the aggregated book.
  - For N-PORT rows, `total_value_usd` sums `valUSD` over every `invstOrSec` row, and `amendments_used` is the accession of the filing used.
- 1.6: `run_all.py` writes its outputs before it reports failed checks, and still exits 1 when a check fails.

New in session 1b:

- **1.4b, what "blank CUSIP" looks like in the filings.** The ISIN-only rows rarely carry an empty CUSIP element. Over the 28 books used, IVV files 411 of them as `<cusip>N/A</cusip>` and 334 with no `cusip` element; IWF files 271 with no `cusip` element (D item 1b). The implemented rule is the one in 01b step 1.4b: `sec_id` is the CUSIP when it is valid, else the ISIN when it is valid. That covers a blank CUSIP, `000000000` and `N/A` alike. `parse_nport` still blanks only an absent CUSIP or `000000000` (01 D 1.4), so the raw CSVs keep `N/A` as filed.
- **1.4b, what "a valid 12-character ISIN" means.** It is implemented as ISO 6166: 2 letters, 9 alphanumeric characters, then a Luhn check digit (`attrib.edgar.valid_isin`). A plain 12-character check would break a fixed test. `test_only_ec_ns_rows_kept` (01 D 1.4) has an EC/NS row with CUSIP `000000000` and ISIN `US0000000000` that must not be kept. That ISIN is 12 alphanumeric characters, but its check digit should be 2, not 0. With the check digit the test passes unchanged. CUSIP validity is unchanged: Convention 4.3, 9 alphanumeric characters, no check digit. Every ISIN on the ISIN-only rows of the 28 IVV and IWF books passes the check, and no EC/NS row in any book used is dropped for having neither id (D item 1b). **Please confirm.**
- 1.4b: in HOLDINGS, `cusip` is blank where it is not a valid CUSIP, so an ISIN-only row shows `cusip` blank rather than `N/A`. `isin` is blank for every 13F row.
- 1.4b: `equity_rows_nport` now returns a `sec_id` column with the rows it keeps. `test_ivv_fixture_shape` needs it to count kept rows by `sec_id`.
- 1.4b: when a timeout or connection error persists through all retries, `RuntimeError` is raised as for 5xx, with the exception named in the message.
- 1.5b: FILINGS_NPORT has no form column, and its schema is fixed. To support D item 2, `pull_data.py` reads `submissionType` from each downloaded N-PORT XML. It records that value as `form` in the file's `uncommitted_sha256` entry and prints every filing that is not `NPORT-P`.
- 1.5b ran before 1.6b changed H, as the steps are ordered. So it still downloaded the 13F information tables for 2019-03-31 and 2019-06-30, 6 files that are byte-identical to before. They stay committed and unused.
- E item 8 asks for the largest weight at 2019-03-31, which is no longer in H. The table uses 2019-09-30, the first date of H, together with 2022-12-31 and 2026-06-30.
- Fresh-clone check: rule 12 says to clone the pushed repo, but 01b Section E says to push once, at the end. The clone was taken from the local `main` at `fb2eee2`, which carries the same commits as the push, and only this review and the status file follow it.

## Not verified

- No figure here was checked against EDGAR by hand. The reviewer's independent checks are E6, E7 and A.2 of 01b.
- IVV's `identifiers` block carries `<other otherDesc="Inhouse Asset ID" value="G1151C101"/>` on the Accenture row of the fixture, which looks like Accenture's CUSIP. Nothing parses that field, and it has not been checked on the other ISIN-only rows (Open question 1).
- The `timeout` path has only been exercised with the fake session. No request timed out in the 1.5b pull.

## Open questions

1. **The same non-US issuer is keyed differently in IVV and in the other books (Section 2 impact, not decided here).** On all 28 dates, IVV files companies such as Accenture with only an ISIN (`IE00B4BNMY34`). IWF does the same until 2022-06-30. From 2022-09-30, IWF files the same issuers with their CUSIP (`G1151C101`; D item 1 shows 0 ISIN-only rows from that date). The funds' 13F books always use the CUSIP. So one issuer can carry 2 different `sec_id` values across books. SECURITY_MAP is keyed by `cusip` in kickoff 6.2 and OpenFIGI is queried with `cusip`, so the ISIN-only rows (2.7% to 4.0% of IVV) have no lookup key yet. 2 options for the reviewer:
   - (a) Key SECURITY_MAP by `sec_id` and query OpenFIGI with `ID_ISIN` for ISIN rows and `ID_CUSIP` for the rest.
   - (b) In `parse_nport`, take the CUSIP from the `other` identifier labelled "Inhouse Asset ID" when the `cusip` element is not valid and that value is a valid CUSIP, so that `sec_id` becomes a CUSIP. This changes a fixed parser rule and needs verifying on every ISIN-only row.

   Active share is unaffected either way, because amendment 10 keys the issuer by CIK.
2. **Polen's book size** varies from 58 to 240 kept rows across the 28 dates (E5). This is reported, not judged. The gate in 3.4 decides whether the 13F book tracks the fund.
3. `PLAN.md` and the kickoff still say 30 dates and 30 quarters. Under rule 14 they were not edited; `CLAUDE.md` amendment 7 says to read 28.

## Files changed

- Step 1.0: `pyproject.toml`, `requirements-lock.txt`, `decisions/OPEN.md`, `decisions/section_0_review.md`, `CLAUDE.md`, `PLAN.md`
- Steps 1.1 to 1.2: `attrib/config.py`, `attrib/edgar.py`, `tests/test_config.py`, `tests/test_edgar_client.py`
- Steps 1.3 to 1.4: `attrib/edgar.py`, `scripts/pull_data.py`, `tests/test_edgar_13f.py`, `tests/test_edgar_nport.py`, `tests/fixtures/FIXTURES.json`, `tests/fixtures/13f/akre/` (2 files), `tests/fixtures/nport/` (1 file)
- Step 1.5: `scripts/pull_data.py`, `tests/test_manifest.py`, `data/raw/MANIFEST.json`, `data/raw/sec/` (2 files), `data/raw/edgar/13f/` (3 filings lists, 96 XML), `data/raw/edgar/nport/` (4 CSV)
- Step 1.6: `scripts/run_all.py`, `outputs/tables/coverage.csv`
- Step 1.2b: `config.toml`, `attrib/config.py`, `attrib/edgar.py`, `scripts/pull_data.py`, `tests/test_config.py`, `tests/test_edgar_client.py`
- Step 1.4b: `attrib/edgar.py`, `scripts/run_all.py`, `tests/test_edgar_nport.py`
- Step 1.5b: `scripts/pull_data.py`, `scripts/run_all.py`, `data/raw/MANIFEST.json`, `data/raw/edgar/nport/filings_ivv.csv`, `data/raw/edgar/nport/holdings_ivv.csv`, `data/raw/edgar/nport/holdings_iwf.csv`
- Step 1.6b: `config.toml`, `outputs/tables/coverage.csv`, `CLAUDE.md`
- Status: `review/section_1.md`, `instructions/01b_section_1_completion.status.md`

## Reviewer reads

1. `instructions/01b_section_1_completion.status.md`
2. This file: Deviations (the 2 ISIN points), Open question 1, then 01b D items 1 to 4 and E5
3. `git diff e5dba91 fb2eee2 -- attrib/ scripts/ tests/ config.toml`
4. `attrib/edgar.py`: `valid_isin`, `sec_ids`, `aggregate_book`, `equity_rows_nport`, `EdgarClient._get`
5. `tests/test_edgar_nport.py`, `tests/test_edgar_client.py`
