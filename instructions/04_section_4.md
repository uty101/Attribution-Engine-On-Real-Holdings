# instructions/04_section_4.md — Session 4: Section 4, Brinson and linking

Pull `main` first. Precedence (rule 13): this file beats `CLAUDE.md` amendments and `PLAN.md`, which beat the kickoff. Read 28 wherever 30 quarters is written (amendment 7).

---

## A. Section 3: approved

What the reviewer checked independently, from a clone of `dc1ce1c`, on Linux with Python 3.12:

1. **Suite and regeneration.** 50 tests pass. `run_all.py --section 3` passes every check, and `git status` is clean afterwards.
2. **All 140 book returns recomputed.** The reviewer's own loop started from `holdings_{entity}.csv`, `security_map.csv` and `adjclose.parquet`. It used its own quarter calendar (the last IVV trading day on or before each quarter end) and buy-and-hold to the last available close. It treated priced positions only, with the neutral rule implied. Every one of the 140 entity-quarters matches `book_quarterly.csv`, the largest difference being 1.4e-16.
3. **Spin-offs.** Yahoo's adjusted closes already absorb spin-offs. RTX moves −7.8% on 2020-04-03, the day United Technologies distributed Carrier and Otis; that is the market move, not a 35% fake loss. GE on the GE HealthCare and GE Vernova dates, 3M on the Solventum date, and J&J on the Kenvue exchange all show ordinary daily moves. Every row in both D.4 large-move lists is a real earnings-day move (Meta Feb 2022, Netflix Apr 2022, Oracle Sep 2025, Salesforce Aug 2020, Align, FICO, Gartner, IDEXX). **So no `quarter_return` overrides are needed**, and none are set.
4. **Benchmark gaps.** Over 28 quarters the IVV gap has mean +2.9 bp and standard deviation 15 bp; IWF has +6.9 bp and 32 bp. The 2 outliers are IWF Q3 2024 (+86 bp) and Q2 2026 (−116 bp). Unmapped weight is 0.09% and unpriced 0% in the second, so it is not a data hole. Buy-and-hold from a quarter-start book cannot follow index changes made inside the quarter, and Russell's growth index turns over most around reconstitution. Accepted as genuine reconstruction error, reported, not tuned away.
5. **The gate.** All 3 funds pass: Akre 0.990 (26 quarters), Jensen 0.9996, Polen 0.998. Polen passing with a 219-name 13F book against a 25-name fund is itself a finding for the write-up. Every mean gap is positive (book above NAV by 16 to 39 bp a quarter), which is the sign fees and cash drag predict.

Answers to the session 3 questions:

1. **`test_cik_override` input.** Accepted. The input changed to fit a rule an instruction file changed, and no assertion changed. That is not loosening a test.
2. **`sec_id` in POSITION_RETURNS.** Keep both columns as you have them.
3. **Gap standard deviation.** Keep ddof 1. With 26 to 28 observations it is the right estimator, and the column is labelled.
4. **Deviations 3 to 11, 13 and 14.** All accepted as listed.
5. **IWF t = 27.** Point 4 above.
6. **`quarter_return` candidates.** Point 3 above. None set.
7. **Delisted names all Unpriced.** Accepted. It is a limit of free price data, and the write-up must state it with the unpriced weights.
8. **Reused tickers `INFO` and `STI`.** Accepted, since neither prices a position. Add a test, `test_reused_ticker_never_prices_before_its_start`: no position is priced on a column whose first valid date is after the position's `q_start`.

---

## B. Decisions for Section 4

| item | decision | reason |
|---|---|---|
| Funds in scope | Akre, Jensen and Polen, all passing the gate | Section A point 5 |
| Inputs | `buckets.csv` for the fund and its benchmark, and `book_quarterly.csv` for `r_P` and `r_B`. Nothing is recomputed from positions. | One source of book numbers |
| Empty buckets | Convention 4.11, applied inside `brinson_fachler` to the blank `r` values in `buckets.csv` | The blanks are there by design |
| Neutral buckets | Unmapped and Unpriced enter Brinson like any bucket, with their book's neutral return | Convention 4.9; this keeps the identity exact |
| Linking input layout | D-21 B (long) | Already decided |
| Linked output | `linked.csv` per kickoff 6.2, 14 bucket rows plus a row with bucket `Total`, per fund and method (`carino`, `menchero`) | The table the README prints |
| Chart 1 | For each k from 1 to 28, link quarters 1 to k with Carino and take the Total allocation and Total selection. Plot both against the quarter-end date of k, in percent, with a zero line. Title: "{Fund} vs {benchmark}: cumulative allocation and selection (Carino)". Subtitle naming interaction as excluded from the chart and shown in Table 1. Figure 8 × 4.5 inches at config dpi, `metadata={"Software": None}`. | Re-linking each prefix makes every point a proper linked effect, not a running sum |
| Bootstrap | One call to `stationary_bootstrap_indices(n=28, mean_block, reps, seed)` per fund. The same index draws are used for that fund's quarterly total allocation, selection and interaction series (each the sum over buckets for the quarter, unlinked). `bootstrap_mean` returns mean, p05 and p95. | Shared draws keep the 3 intervals comparable |
| Carino against Menchero | Reported, not tested (kickoff 5.6) | |

---

## C. Amendments to Section 4 steps

### 4.1 Brinson-Fachler
- `test_identity_every_real_fund_quarter`: 84 cases (3 funds × 28 quarters), built from the committed raw data through the Section 3 functions, identity to 1e-10.
- `test_hand_worked_three_sector`. Docstring and asserted values to 1e-12:
  - weights: fund (0.5, 0.3, 0.2); benchmark (0.4, 0.4, 0.2);
  - returns: fund (0.10, 0.02, −0.05); benchmark (0.08, 0.03, −0.04);
  - r_B = 0.036 and r_P = 0.046;
  - allocation = (0.0044, 0.0006, 0);
  - selection = (0.008, −0.004, −0.002);
  - interaction = (0.002, 0.001, 0).
  - The sum is 0.010, which equals 0.046 − 0.036.
- `test_empty_bucket_rules`: a bucket held only by the benchmark has selection 0 and interaction 0; a bucket held only by the fund uses r_B in allocation.

### 4.2 Linking
- `test_carino_limit`: a synthetic series where 1 quarter has r_P = r_B exactly; the linked sum equals D to 1e-12 and no NaN appears.
- `test_menchero_limit`: the same with D = 0 over the whole period; the linked effects are finite and sum to 0 to 1e-12.
- `test_single_period_unchanged`: T = 1 gives the input effects to 1e-15 for both methods.

### 4.3 Per fund
- `brinson_quarterly.csv` rows are ordered fund (config order), t, then bucket (Convention 4.6 order).
- `run_all.py --section 4` produces everything.

---

## D. Review evidence

1. `linked.csv` in full.
2. Per fund: D, R_P and R_B, and the Total row of each method side by side with their difference.
3. Per fund: the 5 buckets with the largest |Carino minus Menchero| in any effect.
4. The bootstrap rows for allocation, selection and interaction.
5. Per fund: the 3 largest single-quarter selection totals and the 3 most negative, with t and quarter-end date.
6. Per fund at t = 28: the 5 largest holdings in FF12 `Other`, with weight. Akre has 39% in Other at t = 12, which is presumably Mastercard and Visa under SIC 7389. The write-up has to explain that this is FF12 classification, not "miscellaneous", so the reviewer needs the names.
7. Chart 1 for each fund, embedded as a PNG.
8. Full test output, then the fresh-clone check against GitHub.

---

## E. End of session

Status file: `instructions/04_section_4.status.md`, per rule 11. Push the step commits, run the fresh-clone check against GitHub, then commit and push the review and status files.
