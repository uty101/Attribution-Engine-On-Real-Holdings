# instructions/09_closeout.md — Session 9: close-out wording fixes

Pull `main` first. This file holds wording and sourcing fixes to the README only, plus the decisions on the session 8 questions. No method changes. Precedence (rule 13): this file beats everything before it.

---

## A. Section 8: approved, with fixes below

What the reviewer checked, from a clone of `8c546bc`:

1. **The README, read line by line** against `answers.csv` and the tables. Every number matches its source.
2. **Section placement of the named holdings.** The reviewer checked `security_map.csv`:
   - ROP and DHR (SIC 3823) and VRSK (7374) are in BusEq;
   - FICO, CSGP, MA and V (7389) and MCO (7320) are in Other.
   - Akre's summed quarterly BusEq effects are −0.603 selection and +0.376 interaction, against 0.000 selection in Other.

**The session was right on question 1 and instruction 08 was wrong.** D.3 named FICO and CoStar as BusEq names. They are SIC 7389, so they sit in Other. The README's choice to name Roper, Danaher, CCC and Verisk was correct, and refusing to print the reviewer's error was the right call.

Answers to the session 8 questions:

1. **BusEq names.** Keep Roper, Danaher, CCC and Verisk. In the Other sentence, name Mastercard, Visa, Moody's, FICO and CoStar.
2. **Akre's Other weight.** Add the 2 `answers.csv` rows in Section B and use them.
3. **FICO.** Add the 3 sourced rows in Section B and use them. Keep "the FHFA's September 2026 order letting every GSE lender use VantageScore" without a day, since no repo file sources the day.
4. **Correlation format.** Add `num3` (3 decimals). Use it for every correlation in the prose and in Table 4's Correlation column.
5. **Deviations 1 to 9.** All accepted. Signed `largest_cte` is the right reading: it names the largest contributor to TE, and a hedge-like negative CTE is not "the largest contribution".

---

## B. New answers.csv rows (Akre only, question 1 or 3 as shown)

| question | figure | value | source |
|---|---|---|---|
| 1 | `selection_BusEq` | Carino BusEq selection | `linked`, fund=akre, method=carino, bucket=BusEq |
| 1 | `interaction_BusEq` | Carino BusEq interaction | the same row |
| 1 | `other_weight_min`, `other_weight_max` | min and max of Akre's Other bucket weight over the 28 quarters | `buckets`, entity=akre, bucket=Other |
| 3 | `fico_weight_2026_06_30` | FICO's weight in the Akre book at 2026-06-30 | `position_returns` (rebuilt by `run_all.py`, so the test recomputes it from `holdings_akre.csv` and `security_map.csv`) |
| 3 | `fico_return_2026_09` | FICO's month return, 2026-08 to 2026-09, from month-end adjusted closes | `adjclose.parquet` |
| 3 | `active_return_2026_09` | Akre book monthly return minus the IVV book's, for 2026-09 | `book_monthly` |

`test_answers_trace_to_source` covers the new rows.

---

## C. README template fixes (`docs/README_template.md`)

1. **Interaction sentence (Results, after Table 1).** Replace the current interaction sentence with:
   - "Its large positive interaction sits in BusEq too: Akre held far less BusEq than IVV, and an underweight in a bucket where the fund's own picks lost gives a positive interaction ({akre.interaction_BusEq:pp}, against {akre.selection_BusEq:pp} of selection)."
   - Then add a new sentence: "Its weight in FF12 Other, {akre.other_weight_min:pct} to {akre.other_weight_max:pct} of the book, is Mastercard, Visa, Moody's, FICO and CoStar."
2. **Exposures callout (Results, before the exposures chart).** Replace "…so the drift comes from what Akre holds." with "…which is what you would expect, since both use the same 36 months of returns (see Data and method limits)."
3. **Factors answer paragraph.** Replace "in both its returns and its holdings (Akre's rolling beta and exposure charts below)" with "(Akre's rolling beta chart below)".
4. **Active risk answer paragraph.** Replace the FICO sentence with: "The reason is September 2026, the largest active month in the sample: FICO, {akre.fico_weight_2026_06_30:pct} of Akre's book at 2026-06-30, fell {akre.fico_return_2026_09:pct} in the month after the FHFA's September 2026 order letting every GSE lender use VantageScore, and the book trailed IVV by {akre.active_return_2026_09:pp} that month."
5. **Correlations.** Apply `num3` in the "book against the NAV" paragraph and in Table 4.
6. Re-render with `scripts/build_readme.py`. Both README tests must pass.

---

## D. Steps

- **9.0** Commit `step 9.0: closeout answers rows and README wording`, covering Sections B and C.
- **9.1** Commit `step 9.1: final run and fresh clone`:
  - `run_all.py` twice, with `git status` clean;
  - a fresh clone against GitHub with the suite under disabled sockets;
  - update `docs/METHODS.md` only if a format or row definition it states has changed.

---

## E. Review evidence

1. The 6 new `answers.csv` rows.
2. The diff of `README.md` against `8c546bc`, in full.
3. Full test output, then the fresh-clone output.

---

## F. End of session

Status file: `instructions/09_closeout.status.md`, per rule 11. This is the last session of project 4.
