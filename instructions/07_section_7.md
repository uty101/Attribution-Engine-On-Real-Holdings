# instructions/07_section_7.md — Session 7: Section 7, Report and entry point

Pull `main` first. Precedence (rule 13): this file beats `CLAUDE.md` amendments and `PLAN.md`, which beat the kickoff.

---

## A. Section 6: approved

What the reviewer checked independently, from a clone of `73d799a`, on Linux with Python 3.12:

1. **Active share and ex-ante TE at 2026-06-30, from scratch.** The reviewer built its own CIK-keyed issuer weights, its own ticker-level risk weights, the kickoff 5.10 fill, and the covariance through `pc.cov.window_daily`, `cov_lw_cc` and `condition_cov`. All 3 funds match `risk_quarterly.csv` to 4 decimals:

   | fund | active share | ex-ante TE |
   |---|---|---|
   | Akre | 0.9737 | 13.46% |
   | Jensen | 0.6157 | 5.75% |
   | Polen | 0.6178 | 8.43% |

2. **Realised TE over the 83 months** matches `te_realised.csv`: 10.39%, 5.24% and 6.42%.
3. **Akre's September 2026 is real.** Its book fell 13.7% against IVV's −0.4%. FICO, 8.5% of the book, fell 48% in the month after the FHFA's 4 September order letting every GSE lender use VantageScore. Brookfield, KKR, Roper, CoStar and Copart each fell 11% to 18%. This is the single largest active month in the sample, so the write-up must name it.
4. **Cross-platform determinism.** On Linux, `run_all.py --section 6` reproduces every committed CSV to a maximum relative difference of 2.5e-11. PNGs differ at the byte level (font rasterisation). Rule 9's byte-identity holds on 1 machine, not across operating systems: the BLAS and libm last-bit differences show up because `%.17g` prints every bit. That is accepted. Record it in `docs/CONVENTIONS_RESOLVED.md` as item 24: "byte-identical on one platform; across platforms, numeric outputs agree to 1e-10 relative".

Answers to the session 6 questions:

1. **`n_names`.** The dimension of Σ. Accepted.
2. **Realised TE sample.** **Change it to all 84 book months (October 2019 to September 2026).** Realised TE needs no factor data, so the French end date has no reason to cut it, and the cut was hiding the largest active month (point 3). Set `n_months` = 84.
3. **Polen's ETFs.** Keep them. They are real holdings in the 13F book, Brinson and the returns already include them, and ridging handled the near-duplicate pairs as designed. The write-up names them.
4. **Format details.** Accepted.
5. **For the write-up:** noted, both points.

---

## B. Step 7.0 (new)

Commit `step 7.0: realised TE on 84 months; conventions item 24`. Apply answer 2 and point 4. Rerun `run_all.py --section 6`, and print the old and new `te_realised.csv` in the review.

---

## C. Decisions for Section 7

### C.1 Report layout (supersedes the outline of kickoff 5.11)

All numbers are in percent with 2 decimals unless stated. All text follows the kickoff Section 8 writing rules. A4 portrait, 2 cm margins, Helvetica 9 pt body, 8 pt tables.

**Page 1.**
- Title "{Fund} vs {benchmark}: performance and risk attribution".
- A line giving the window: holdings 2019-09-30 to 2026-06-30, returns 2019-09-30 to 2026-09-30.
- A line giving annualised book returns for the fund and the benchmark, and the cumulative D.
- A data line: mean unmapped and mean unpriced weight of the fund book over the 28 quarters.
- Table 1: the Carino rows of `linked.csv`, 14 buckets plus Total, with columns allocation, selection, interaction and total, in percentage points.
- A line with the bootstrap 90% intervals of mean quarterly allocation and selection.
- Chart 1, width 17 cm.

**Page 2.**
- Table 2: the fund's book rows of `factor_by_year.csv`, with columns year, n_months, excess return, the 6 factors, alpha and residual.
- A line giving the full-sample alpha a month, its HAC t, and R².
- Chart 2, width 17 cm.

**Page 3.**
- Table 3: the rows of `risk_quarterly.csv` at each 31 December from 2019 to 2025 and at 2026-06-30 (8 rows), with columns date, active share, ex-ante TE, n_names and ridged.
- A line giving realised TE (84 months) and the mean ex-ante TE.
- Chart 3, width 17 cm.

**Page 4.**
- Table 4: the fund's row of `gate.csv` (corr, n_quarters, mean gap, std gap, TE of the gap) and the gap bootstrap interval.
- Then the 13F limits paragraph below, verbatim.

> **What a 13F book cannot see.** The 13F lists a manager's long US-listed equity positions at each quarter end, filed up to 45 days later. It omits cash, shorts, most non-US shares, bonds and anything bought and sold inside the quarter. This report holds each quarter-end book unchanged for the next 3 months, so trades made during the quarter show up only in the gap between the book and the fund's NAV, together with fees and cash. A 13F belongs to the manager, not to one fund, so where a manager runs several strategies the book blends them. Sectors are Fama-French 12 industries built from SIC codes, which put payment networks such as Visa and Mastercard in Other. Securities that could not be mapped to a ticker, or had no price, earn the book's own return so that they move nothing.

### C.2 Report mechanics

| item | decision |
|---|---|
| `results` (D-26) | A dict whose keys are the output table stems (`linked`, `factor_by_year`, `factor_fit`, `risk_quarterly`, `te_realised`, `gate`, `bootstrap`, `book_quarterly`, `coverage`) mapping to DataFrames already filtered to this fund, plus `fund_name`, `benchmark_name` and the 3 chart PNG bytes under `chart1`, `chart2` and `chart3`. `build_report` filters nothing (D-26 B). |
| Charts in the report | The same PNG bytes as `outputs/figures/`, read from disk, not re-rendered |
| Determinism | `test_two_builds_byte_identical` runs on 1 machine. Across machines the PDF may differ (Section A point 4). |
| Page count | Exactly 4 for the 3 funds, asserted with pypdf. A user report may be shorter (D-28). |

### C.3 Entry point and the user path

| item | decision |
|---|---|
| Inputs | `holdings_path` and `benchmark_path` are HOLDINGS CSVs (amendment 8). `entity` may be absent. `isin` and `sec_id` may be absent, and `sec_id` defaults to `cusip`. |
| Window | `start` and `end` are holdings dates. Every calendar quarter end between them must be present in both files, else raise and list the missing dates. |
| Data | Reads `data_dir/raw` and `data_dir/manual`, then merges `data_dir/extra/security_map_extra.csv` and `data_dir/extra/adjclose_extra.parquet` when present (written by 7.3). The extra rows win on a duplicate `sec_id` or ticker. |
| Missing securities | Any `sec_id` absent from the merged map raises an error listing every one and naming `python scripts/pull_data.py --holdings <path> --benchmark <path>`. |
| No NAV (D-28) | Page 4 shows the limits paragraph and the line "No NAV series was supplied, so the reconstruction check is skipped." with no Table 4. |
| Output | `{out_dir}/{fund_name or holdings file stem}.pdf`; the function returns the path. |
| Mini fixture | `tests/fixtures/mini/`: 3 synthetic stocks (tickers MINA, MINB, MINC), 1 benchmark of the same 3 in different weights, holdings at 2019-12-31 and 2020-03-31. Daily prices from 2016-01-04 to 2020-06-30, generated once with `default_rng(run.bootstrap_seed)` and committed as CSV. Monthly French-format factors over the same span, generated the same way. A 3-row security map. All files are committed; nothing is generated at test time. |

### C.4 Step 7.3 evidence run
Run `--holdings` on a 2-row file: Akre's MA position at 2026-06-30, plus Teck Resources Class B, CUSIP `878742204`, which is absent from the current map. Expected: 1 new `sec_id` mapped (ticker TECK) and its prices written to `data/extra/`. Delete that file afterwards; nothing under `data/extra/` is committed.

---

## D. Review evidence

1. The step 7.0 before-and-after table.
2. Test output for 7.1 and 7.2, including the mini end-to-end run.
3. The 7.3 run log in full.
4. PNG renders of all 12 pages (3 funds × 4) in `review/section_7_pages/`, rendered with pymupdf (D-29) at 100 dpi, each embedded in the review.
5. The PDF file sizes and pypdf page counts.
6. Full test output, then the fresh-clone check against GitHub.

---

## E. End of session

Status file: `instructions/07_section_7.status.md`, per rule 11. Push the step commits, run the fresh-clone check against GitHub, then commit and push the review and status files.
