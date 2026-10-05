# instructions/03_section_3.md — Session 3: overrides, then Section 3, Book returns and reconstruction

Pull `main` first. Precedence (rule 13): this file beats `CLAUDE.md` amendments and `PLAN.md`, which beat the kickoff. Read 28 wherever 30 quarters is written (amendment 7).

---

## A. Section 2: approved

What the reviewer checked independently, from a clone of `4491264`:

1. **The fallback passes.** They cut mean unmapped weight for Jensen from 5.5% to 0.9% and for Polen from 5.9% to 0.4%. Akre, IVV and IWF barely moved: their gaps are a handful of large names, which Section B overrides by hand.
2. **The 6 rejections.** The reviewer read every rejected fallback result whose ticker is XOM, GE, NOV, QDEL, FWONK or FWONA. Each is the right company, renamed (GE Aerospace, NOV Inc., QuidelOrtho, Formula One Group) or on a non-US venue code (Exxon's `UZ`). The first-token rule did its job of refusing to guess. These 6 get ticker overrides below.
3. **B.5 against yfinance.** The mean absolute monthly difference is 1.1 bp for Jensen and 2.1 bp for Polen, with a worst month of 35 bp. That validates the N-PORT B.5 source for Akre. Accepted as evidence; no test is added.
4. **Deviations under 02c, item 4.** All accepted as listed.

---

## B. Overrides

Replace `data/manual/overrides.csv` with exactly these rows (LF line endings, no trailing blank line beyond the final newline):

```csv
kind,sec_id,period_date,value,source_note
ticker,38259P508,,GOOGL,Alphabet Class A filed under Google's pre-2015 CUSIP
ticker,913017109,,RTX,United Technologies; became Raytheon Technologies (RTX) on 2020-04-03
ticker,112585104,,BN,Brookfield Asset Management Inc; renamed Brookfield Corp (BN) 2022
ticker,03662Q105,,ANSS,ANSYS
cik,03662Q105,,1013462,ANSYS
ticker,30231G102,,XOM,Exxon Mobil
ticker,25401T108,,DBRG,DigitalBridge Group
ticker,19626G108,,DBRG,Colony Capital; renamed DigitalBridge (DBRG) 2021
cik,25401T108,,1679688,DigitalBridge
cik,19626G108,,1679688,DigitalBridge
ticker,IE00BZ12WP82,,LIN,Linde
ticker,G5494J103,,LIN,Linde
ticker,512807108,,LRCX,Lam Research
ticker,H82027105,,SOPH,SOPHiA Genetics
ticker,74165N105,,PRMW,Primo Water
ticker,74167P108,,PRMW,Primo Water
cik,74165N105,,884713,Primo Water
cik,74167P108,,884713,Primo Water
ticker,369604103,,GE,General Electric
ticker,040413106,,ANET,Arista Networks
ticker,09247X101,,BLK,BlackRock
ticker,IE00BY9D5467,,AGN,Allergan
cik,IE00BY9D5467,,1578845,Allergan
ticker,N07059210,,ASML,ASML Holding
ticker,GB00BZ09BD16,,TEAM,Atlassian
ticker,G06242104,,TEAM,Atlassian
ticker,755111507,,RTN,Raytheon
cik,755111507,,1047122,Raytheon
ticker,G5960L103,,MDT,Medtronic
ticker,00507V109,,ATVI,Activision Blizzard
cik,00507V109,,718877,Activision Blizzard
ticker,90184L102,,TWTR,Twitter
cik,90184L102,,1418091,Twitter
ticker,983919101,,XLNX,Xilinx
cik,983919101,,743988,Xilinx
ticker,848637104,,SPLK,Splunk
cik,848637104,,1353283,Splunk
ticker,26614N102,,DD,DuPont de Nemours
ticker,285512109,,EA,Electronic Arts
cik,285512109,,712515,Electronic Arts
ticker,G4388N106,,HELE,Helen of Troy
ticker,Y4600W108,,KARO,Karooooo
ticker,339041105,,CPAY,FleetCor Technologies; renamed Corpay (CPAY) 2024
ticker,723787107,,PXD,Pioneer Natural Resources
cik,723787107,,1038357,Pioneer Natural Resources
ticker,928563402,,VMW,VMware
cik,928563402,,1124610,VMware
ticker,44919P508,,MTCH,Match Group
ticker,054937107,,TFC,BB&T; renamed Truist Financial (TFC) 2019
ticker,156782104,,CERN,Cerner
cik,156782104,,804753,Cerner
ticker,812578102,,SGEN,Seattle Genetics
ticker,81181C104,,SGEN,Seagen
cik,812578102,,1060736,Seagen
cik,81181C104,,1060736,Seagen
ticker,G46188101,,HZNP,Horizon Therapeutics
ticker,IE00BQPVQZ61,,HZNP,Horizon Therapeutics
cik,G46188101,,1492426,Horizon Therapeutics
cik,IE00BQPVQZ61,,1492426,Horizon Therapeutics
ticker,BMG475671050,,INFO,IHS Markit
cik,BMG475671050,,1598014,IHS Markit
ticker,CH0102993182,,TEL,TE Connectivity
ticker,682680103,,OKE,ONEOK
ticker,22266L106,,COUP,Coupa Software
cik,22266L106,,1385867,Coupa Software
ticker,867914103,,STI,SunTrust Banks
cik,867914103,,750556,SunTrust Banks
ticker,904767704,,UL,Unilever
ticker,053484101,,AVB,AvalonBay Communities
cik,053484101,,915912,AvalonBay Communities
ticker,JE00B783TY65,,APTV,Aptiv
ticker,86800U104,,SMCI,Super Micro Computer
ticker,177376100,,CTXS,Citrix Systems
cik,177376100,,877890,Citrix Systems
ticker,254709108,,DFS,Discover Financial Services
cik,254709108,,1393612,Discover Financial Services
ticker,M22465104,,CHKP,Check Point Software
ticker,78486Q101,,SIVB,SVB Financial Group
cik,78486Q101,,719739,SVB Financial Group
ticker,94946T106,,WCG,WellCare Health Plans
cik,94946T106,,1279363,WellCare Health Plans
ticker,G29018101,,DLO,dLocal
ticker,M7S64H106,,MNDY,monday.com
ticker,30063P105,,EXAS,Exact Sciences
cik,30063P105,,1124140,Exact Sciences
ticker,98936J101,,ZEN,Zendesk
cik,98936J101,,1463172,Zendesk
ticker,531229854,,FWONK,Liberty Media Formula One Series C
ticker,531229870,,FWONA,Liberty Media Formula One Series A
ticker,637071101,,NOV,National Oilwell Varco; renamed NOV Inc
ticker,74838J101,,QDEL,Quidel; renamed QuidelOrtho
```

There are 62 `ticker` rows and 29 `cik` rows.
- The 62 `ticker` rows cover 58 of the 60 names in `unmapped_top.csv`, plus the 4 name-check rejections not already among them (Exxon and GE are).
- 2 names are left unmapped on purpose: old IAC `44891N109` and CBS `124857202`. Both went through mergers where today's ticker is a different security.

**2 changes to how overrides apply**, superseding 02 Section B:
- A `cik` override now always wins over ticker → CIK, not only when that lookup fails. Several delisted tickers have since been reused by other companies (for example `STI`), so today's `company_tickers.json` would hand back the wrong CIK.
- Every `cik` override is verified before use. Fetch the CIK's submissions JSON and compare the first token of its `name` with the first token of `source_note`, using the 02b name-normalisation rule. On a mismatch, do not apply the row; list it in the review with both names, and carry on.

Delisted tickers that yfinance cannot price (likely ATVI, TWTR, XLNX and others) will land in Unpriced with the right CIK and SIC. That is expected; report them, do not stop.

---

## C. Steps

### 3.0 Apply overrides and refresh Section 2 outputs
Commit `step 3.0: reviewer overrides and refreshed map`.
- Write `overrides.csv` (Section B). Implement the 2 rule changes in `build_security_map`.
- Tests in `tests/test_mapping.py`:
  - `test_cik_override_beats_ticker_lookup` (synthetic);
  - `test_cik_override_name_mismatch_not_applied` (synthetic).
- `--stage sec` for the override CIKs, which also performs the name verification. The verification result goes to `data/raw/sec/cik_override_check.csv`: sec_id, cik, submissions_name, note_name, match.
- `--stage prices` **only for `yf_ticker`s not already columns in `adjclose.parquet`.** Merge them in as new columns and leave existing columns untouched, because a full re-pull would restate adjusted closes as of a new date. Update `missing.csv` and the manifest.
- Rerun `scripts/run_all.py --section 2`. Every Section 2 check must still pass.

### 3.1 Overrides test
As in `PLAN.md` 3.1. `quarter_return` rows act through `apply_return_overrides` (D-16); there are none yet, so the test is synthetic.

### 3.2 Book returns
As in `PLAN.md` 3.2, with Conventions 4.5 to 4.12. Storage per D-17: `data/processed/position_returns.csv`, `outputs/tables/buckets.csv` (BUCKETS) and `outputs/tables/book_quarterly.csv` (entity, t, book_return, unmapped_weight, unpriced_weight, delisted_weight). Monthly book returns go to `outputs/tables/book_monthly.csv` (entity, month, ret).

### 3.3 Benchmark check (amended)
- Compute the 56 rows as in `PLAN.md`.
- New config key `[gates] benchmark_gap_stop = 0.03`, added to the key-list test.
- Stop under rule 4 only if any |gap| > 0.03.
- If any |gap| > `benchmark_gap_max` (0.01), finish the section and list those quarters, each with that book's unmapped, unpriced and delisted weights. About 3% to 4% of IVV now earns the neutral return, so a 1% gap in a violent quarter is possible without a bug; 3% is not.

### 3.4 Reconstruction and gate
As in `PLAN.md` 3.4, with the 02c rules:
- the quarterly NAV return is the compound of 3 monthly returns from `nav_monthly.csv`, blank when any month is missing;
- blank quarters are excluded from the gate and the gap statistics;
- `gate.csv` columns are fund, corr, pass, n_quarters, mean_gap, std_gap, mean_abs_gap, te_gap_ann.

Bootstrap per D-20.

### Large moves after the overrides
Regenerate `large_moves.csv` with the refreshed map. In the review, list every fund position-quarter (Akre, Jensen, Polen) with a daily |return| > 25% and weight > 0.5%. Also list every IVV or IWF position-quarter with weight > 1%. These are the candidates for `quarter_return` overrides, which handle spin-offs that adjusted closes miss, such as United Technologies in April 2020. The reviewer sets them in the next instruction file. Do not adjust anything yourself.

---

## D. Review evidence

Everything in `PLAN.md` 3.1 to 3.4, plus:

1. `cik_override_check.csv` in full.
2. For the 62 ticker overrides: the resulting `map_status`, `ff12`, and whether `yf_ticker` is priced at the first `q_start` where the security is held.
3. Mean and maximum `unmapped_weight` and `unpriced_weight` per entity after the overrides, in the Section A layout of 02b.
4. The large-move lists above.
5. For Akre t = 12 (holdings 2022-06-30): every position with weight, `r`, and bucket, so the reviewer can recompute the book return by hand.

---

## E. End of session

Status file: `instructions/03_section_3.status.md`, per rule 11. Push the step commits, run the fresh-clone check against GitHub, then commit and push the review and status files.
