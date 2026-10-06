# instructions/08_section_8.md — Session 8: Section 8, Write-up and reproducibility

Pull `main` first. Precedence (rule 13): this file beats `CLAUDE.md` amendments and `PLAN.md`, which beat the kickoff. This is the last build section.

---

## A. Section 7: approved

What the reviewer checked, from a clone of `252d664`, on Linux with Python 3.12:

1. **Suite.** 80 tests pass offline.
2. **Reports.** The reviewer read the renders of Akre's pages 1 and 4 line by line against the CSVs: the annualised returns (7.17% against 16.27%), D of −124.90 pp, the Table 1 Totals (−55.06, −130.44 and +60.59), the bootstrap intervals, and Table 4 (corr 0.99, 26 quarters, mean gap 0.16%, interval −0.07% to 0.39%). The limits paragraph is verbatim.
3. **One reading the write-up must carry.** Akre's selection loss sits almost entirely in BusEq: −124.6 pp of selection and +78.2 of interaction. The fund's BusEq names (FICO, CoStar, Roper, CCC) did far worse than IVV's BusEq, which is mega-cap technology.
4. **The 7.2 fix (`805b5ee`).** It was found by running `attribute()` on the real Akre and IVV books and reproducing the committed tables to 2.2e-16. Good practice, accepted.

Answers to the session 7 questions:

1. **Item 25.** Accepted.
2. **Mini fixture and 3. short user windows.** Keep the fixture as it is. Add `[report] min_factor_months = 24` to `config.toml` and to the key-list test. When the fund has fewer monthly returns than that, page 2 shows the line "Fewer than 24 monthly returns, so the factor fit is skipped." with no Table 2 and no Chart 2, and the factor fit is not run. New test `test_short_window_skips_factor_page`, on the mini fixture: the line is present and the PDF has no Table 2.
3. **4. Known-missing tickers.** Skip the ones in `missing.csv` by default. Add a `--retry-missing` flag that retries them.
4. **5. Charts moved into `attrib/report.py`.** Accepted.
5. **6. Deviations 3 to 9.** Accepted.

---

## B. Step 8.0 (new)

Commit `step 8.0: short-window rule and --retry-missing`. Apply answers 2 and 4. `run_all.py --section 7` must still give 4-page reports and byte-identical PNGs.

---

## C. answers.csv (8.2): exactly these rows, per fund in config order

Columns per kickoff 6.2. `value`, `interval_lo` and `interval_hi` are decimals, not percent. Intervals are blank where none is named. `source_table` is the CSV stem, and `source_row` is a short key such as `fund=akre,method=carino,bucket=Total`.

| question | figure | value | interval | source |
|---|---|---|---|---|
| 1 | `cum_excess_D` | R_P − R_B over 28 quarters | | `book_quarterly` |
| 1 | `ann_return_fund`, `ann_return_bench` | annualised book returns | | `book_quarterly` |
| 1 | `linked_allocation`, `linked_selection`, `linked_interaction` | Carino Totals | | `linked` |
| 1 | `mean_q_allocation`, `mean_q_selection` | bootstrap mean | p05 to p95 | `bootstrap` |
| 2 | `alpha_month_book`, `alpha_month_nav` | alpha | alpha ± 1.645 × HAC se | `factor_fit` |
| 2 | `alpha_t_book`, `alpha_t_nav` | HAC t | | `factor_fit` |
| 2 | `beta_mkt_book`, `r2_book`, `resid_vol_ann_book` | | | `factor_fit` |
| 3 | `active_share_2026_06_30`, `te_exante_2026_06_30` | | | `risk_quarterly` |
| 3 | `te_exante_mean`, `te_realised_84m` | | | `te_realised` |
| 3 | `top15_cte_share_2026_06_30`, `largest_cte_<TICKER>_2026_06_30` | share of TE; largest single CTE | | `cte_positions` |
| 4 | `gate_corr`, `gate_n_quarters`, `te_gap_ann` | | | `gate` |
| 4 | `mean_q_gap` | bootstrap mean | p05 to p95 | `bootstrap` |

Test `test_answers_trace_to_source`: every row's value equals its source cell to 1e-15, or for the 2 annualised returns, a recomputation from `book_quarterly`.

---

## D. README (8.3)

### D.1 How it is built
`scripts/build_readme.py` renders `README.md` from `docs/README_template.md`. The template holds the prose. Every number in the prose is a placeholder such as `{akre.linked_selection:pp}`, filled from `answers.csv`. Every table is a placeholder filled from its CSV. Formats:
- `pp`: × 100, 1 decimal, the unit "pp";
- `pct`: × 100, 1 decimal, "%";
- `pct2`: 2 decimals;
- `num2`: 2 decimals;
- `t`: 2 decimals.

`run_all.py --section 8` calls it. Tests:
- `test_readme_tables_match_csvs`: rendering again equals the committed `README.md` byte for byte.
- `test_readme_has_no_bare_numbers_in_answers`: the Answers section of the template contains no digit outside a placeholder, except years, the 28 and 84 counts, and the date 2026-06-30.

### D.2 Structure, in this order
1. **What this is**, 2 short paragraphs: 13F and N-PORT holdings for 3 concentrated quality-growth managers, attributed against their ETF benchmarks with Brinson-Fachler linked by Carino, a Fama-French 5-factor plus momentum regression, and a Ledoit-Wolf risk model. All from free public data.
2. **Answers**, 1 paragraph per research question, in the kickoff's order.
3. **Results**:
   - Table 1, Carino Totals: 3 rows by 4 effects plus D.
   - The 3 Chart 1s, each preceded by a 1-sentence callout.
   - Table 2: per fund, book and NAV alpha with t, market beta and R².
   - Akre's Chart 2 and exposures chart, each with a callout.
   - Table 3: active share, ex-ante TE at 2026-06-30, mean ex-ante TE, and realised TE.
   - The 3 Chart 3s, each with a callout.
   - Table 4: the gate rows.
4. **Use it on your own holdings:**
   - a copy-paste `attribute()` example on 2 small CSVs in `examples/` (Akre's and IVV's books, 2025-06-30 to 2026-06-30, committed);
   - the `pull_data.py --holdings` line;
   - `run_all.py`.
5. **Data and method limits.** The 13F limits paragraph (from instruction 07), then:
   - mean unpriced weight per entity;
   - Akre's NAV gap months, 2025-08 to 2025-10;
   - the start in September 2019, the first public N-PORT;
   - FF12 rather than GICS;
   - holdings-based and returns-based exposures sharing a window;
   - cross-platform determinism (conventions item 25);
   - the project 1 link dropped, because project 1 produced no characteristic scores.
6. **Reproduce**: Python 3.12, `uv`, the lock file, `run_all.py`, `pytest -p socket --disable-socket`.

### D.3 Claims the README must make
- All 3 funds trailed their benchmark over the window. Selection, not allocation, carried most of it for Akre and Polen.
- Jensen's and Polen's alphas are below −2 HAC standard errors on both book and NAV. Akre's is not distinguishable from 0, and its R² of about 0.76 says its active risk is mostly stock-specific.
- Akre's selection loss sits in BusEq (FICO, CoStar, Roper and CCC against mega-cap technology). Its large interaction comes from 39% to 56% in FF12 Other (Mastercard, Visa, Moody's).
- Akre's September 2026: FICO fell 48% after the FHFA's 4 September VantageScore order. It is the largest active month, and it is why realised TE (84 months) exceeds the ex-ante mean.
- Polen's 13F mixes strategies, including ETFs, yet tracks its fund's NAV at a correlation of 0.998. Every mean gap is positive, which fees and cash predict.

### D.4 Claims the README must not make
- No statement about skill, future returns, or whether to own any fund.
- No "outperform" or "underperform" without the window.
- No GICS sector names.
- No number that is not a placeholder.
- No claim that selection is significant for a fund whose interval contains 0. Check each against `bootstrap.csv`.

### D.5 Writing rules
Kickoff Section 8 rules, plus:
- conversational but technical, in plain English;
- no hyphen or dash joining 2 clauses;
- none of the words robust, resilient, rigorous, leveraging or grounded;
- no filler opening sentences;
- numerals for numbers;
- the vehicle is "the fund".

---

## E. METHODS.md (8.4)

`docs/METHODS.md` states the method as it now stands, in the kickoff's Sections 4 and 5 order, with every amendment folded in:
- 28 dates;
- `sec_id` and ISIN rows;
- N-PORT B.5 NAV for Akre;
- the OpenFIGI fallback passes and the override rules;
- the CIK issuer key;
- the 84-month realised TE;
- regression standard error with n − 7;
- the report layout and the short-window rule.

Each amended item cites the instruction file that set it. No history narrative.

---

## F. Final check and tidy (8.5)

- `run_all.py` with no `--section` runs everything. 2 runs in a row leave `git status` clean on your machine.
- Fresh clone against GitHub: install from the lock, run `run_all.py`, run the suite with sockets disabled, `git status` clean. Paste all of it.
- Tidy:
  - `grep -rn "TODO\|FIXME\|XXX"` over tracked files returns nothing;
  - remove functions no code or test calls, listing them in the review;
  - `decisions/OPEN.md` has only its pointer line;
  - `review/section_8.md` lists every tracked file with its size.
- `CLAUDE.md` `## Amendments` gains a line citing this file for `min_factor_months` and `--retry-missing`.

---

## G. Review evidence

1. `answers.csv` in full.
2. `README.md` in full, embedded in the review.
3. The tracked-file list with sizes.
4. Both `git status` outputs and the runtimes.
5. Full test output, then the fresh-clone output.

---

## H. End of session

Status file: `instructions/08_section_8.status.md`, per rule 11. Push the step commits, run the fresh-clone check against GitHub, then commit and push the review and status files. After this the reviewer writes a close-out file if any wording fixes remain.
