# Session 4 status

## Outcome

Completed. Section 4 is finished.

- `python scripts/run_all.py --section 4` passes every check, and 2 runs give byte-identical CSVs and PNGs.
- All 62 tests pass, both locally and in a fresh clone of GitHub at `1ac3cb7`.
- In that clone, `run_all.py --section 4` regenerated every committed output with `git status` clean.

## Last step reached

Step 4.3 (`1ac3cb7`). Session 4 commits:

- 4.0 (`f732a39`), the reused-ticker test from Section A, answer 8;
- 4.1 (`970094c`);
- 4.2 (`0b41765`);
- 4.3 (`1ac3cb7`).

## Stop reason

None. No rule 4 condition was hit:

- no earlier test failed;
- the Brinson identity held on all 84 real fund-quarters, the worst error being 6.6e-17 against 1e-10;
- both linked sets sum to D for each fund, the worst error being 1.6e-15 against 1e-10.

## Results

Linked Totals over the 28 quarters, Carino, in percentage points. The Menchero values are in `review/section_4.md`, D.2.

| fund | benchmark | D | allocation | selection | interaction |
|---|---|---|---|---|---|
| Akre | IVV | −124.9 | −55.1 | −130.4 | +60.6 |
| Jensen | IVV | −84.2 | +2.4 | −68.0 | −18.6 |
| Polen | IWF | −141.5 | −23.2 | −135.6 | +17.3 |

Mean quarterly effect, with its bootstrap 5% to 95% interval:

| fund | allocation | selection | interaction |
|---|---|---|---|
| Akre | −0.86% (−1.63% to −0.15%) | −2.25% (−3.74% to −0.95%) | +1.05% (+0.28% to +1.80%) |
| Jensen | +0.03% (−0.26% to +0.32%) | −1.10% (−2.32% to +0.11%) | −0.25% (−0.62% to +0.09%) |
| Polen | −0.39% (−0.84% to +0.04%) | −1.88% (−2.74% to −0.97%) | +0.23% (−0.16% to +0.62%) |

Carino minus Menchero is at most 5.3 pp in any Total effect, for Akre's selection.

## Questions for the reviewer

1. **`bootstrap_mean` gained an optional `idx` keyword** (Deviation 2). This makes Section B's "1 call to `stationary_bootstrap_indices` per fund" literal while keeping D-20's return values. The gap rows are unchanged. Is that acceptable?
2. **`zero_tol` is an optional keyword on `carino` and `menchero`** (Deviation 3). `run_all` passes `linking.zero_tol`. The Menchero limit 1e-24 is a module constant citing kickoff 5.6.
3. **`brinson_quarterly.csv` carries `rP` and `rB` after Convention 4.11's fill** (Deviation 5). The alternative is to leave them blank, as `buckets.csv` does. Which do you want?
4. **Chart 1 choices** (Deviation 8):
   - the names are "Akre vs IVV": the fund id capitalised and the benchmark's ETF ticker;
   - the x axis is `q_end` of quarter k;
   - the y label is "Cumulative linked effect (%)".
5. **The step 4.0 commit** (Deviation 1) puts the Section A test in its own commit, following the 3.0 precedent.
6. **`test_equal_period_uses_limit` is kept from PLAN 4.2 beside `test_carino_limit`** (Deviation 9). The second test cannot tell whether the limit was used, because the equal quarter's effects are 0.
7. **For the write-up:**
   - Akre has 56% in FF12 Other at t = 28, mostly MA, MCO, FICO, V and CSGP on SIC 7389 and 7320 (D.6). At t = 12, Other is 39%: MA 14.8%, MCO 12.4%, V 8.3% and CSGP 3.4%. So the guess in Section D, item 6 is confirmed.
   - Jensen's 13F holds its own ETF, JGRW, at 0.36%, which is `no_cik` and so in Other.

## git log origin/main --oneline -3

Captured after the push of the step commits, before this file and the review were committed:

```
1ac3cb7 step 4.3: brinson_quarterly, linked, effect bootstrap rows and Chart 1 per fund
0b41765 step 4.2: Carino and Menchero linking with their zero limits and tests
970094c step 4.1: Brinson-Fachler with the empty-bucket rules and its tests
```
