# instructions/09b_closeout_fixes.md — Session 9b: 3 rendering fixes

Pull `main` first. These are the last README fixes. All 3 are the reviewer's errors in instruction 09, caught by the session. No method or data changes.

---

## A. Session 9: approved

The reviewer read `README.md` at `45d02d0`. The new rows render where intended, and the BusEq and Other sentences are now correct.

Answers to the session 9 questions:

1. **Row count.** 7 is right; Section E.1's "6" was a miscount. Their position after the 75 rows is accepted.
2. **Double negatives.** Fix as in Section B.
3. **Stray comma.** Drop it.
4. **Jensen at 1.000.** Fix as in Section B.
5. **BusEq figures.** Correct as Carino-linked. The summed quarterly numbers in 09 Section A were a check, not the published figure.

---

## B. Fixes

1. **Absolute-value formats.** Add `abspct` (absolute value × 100, 1 decimal, "%") and `abspp` (absolute value × 100, 1 decimal, "pp") to `scripts/build_readme.py`. In the template, use `{akre.fico_return_2026_09:abspct}` and `{akre.active_return_2026_09:abspp}`. The sentence then reads "fell 48.4%" and "trailed IVV by 13.3 pp". The verbs already carry the sign.
2. **Comma.** In the Factors answer paragraph, "fell away, (Akre's rolling beta chart below)." becomes "fell away (Akre's rolling beta chart below)."
3. **Correlations.** Add `num4` (4 decimals) and use it for every correlation, in prose and in Table 4, instead of `num3`. Jensen then shows 0.9996 instead of a rounded 1.000. Remove `num3` if nothing else uses it.
4. Re-render `README.md`. Run the full suite. Then run `run_all.py` once and check `git status` is clean.

Commit as `step 9b.0: README formats`.

---

## C. Review evidence

The diff of `README.md` against `45d02d0`, and the test output.

---

## D. End of session

Status file: `instructions/09b_closeout_fixes.status.md`, per rule 11. Push once.
