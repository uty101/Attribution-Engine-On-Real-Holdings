# instructions/02c_section_2_completion.md — Session 2c: finish Section 2 from step 2.1b

Pull `main` first. `instructions/02b_section_2_completion.md` stays binding wherever this file does not change it. This file decides OPEN-33, answers the session 2b questions, and resumes. No new steps.

---

## A. Review of step 2.1b (`b8cd7e2`)

The stop was correct. The reviewer read `data/raw/edgar/nport_returns/akre_monthly.csv` with its own code.

- The Institutional class `C000080287` has 72 monthly returns, from 2019-08 to 2025-07, with no gap.
- The other 2 classes have 72 each.
- Compounded by calendar year, the class returns +20.7% in 2020, +24.5% in 2021, −22.7% in 2022, +28.7% in 2023 and +18.2% in 2024. That is the right shape for a concentrated quality-growth fund over those years. March 2020 is −10.2%.

The stop condition did what it was written for.

---

## B. Decisions

| item | decision | reason |
|---|---|---|
| OPEN-33, Akre months 2025-08 to 2025-10 | **(b) Accept the gap.** | Option (a) can back out August exactly from the N-CSR fiscal-year return, but September and October up to the conversion would need daily NAVs from an unofficial source. A blank is honest; a half-sourced fill is not. |
| Rule for quarterly NAV returns, all funds | A quarterly NAV return is the compound of its 3 monthly returns, and only when all 3 are present; otherwise it is blank. | One rule, written down, for every fund |
| What a blank quarter means downstream | The quarter keeps its row in `reconstruction.csv` with `nav_return` and `gap` blank. It is left out of the gate correlation, the gap statistics and the gap bootstrap, and the fund's row in `gate.csv` gains a column `n_quarters` giving the count used. For Akre that is t = 24 (Q3 2025) and t = 25 (Q4 2025), so 26 of 28 quarters. Monthly NAV regressions (Section 5) drop the missing months. | Book returns and attribution do not use NAV, so only the reconstruction comparison loses 2 quarters |
| Jensen B.5 gap 2024-12 to 2025-02 | Accepted. Report it beside the cross-check. | Jensen's NAV series is yfinance |
| `attrs["class_ids"]` on the 3rd frame | Accepted | Keeps the Section 1 test exact |
| Class names from EDGAR's HTML class page | Accepted. Record the URL in the manifest. | |
| Full-text search fallback not built | Accepted | Not needed |
| "ETF class in the same series" meaning the symbol `etf_successor` | Accepted. AKRE is its own series, so source 2 never fires; source 3 covers 2025-11 on. | |
| `series_resolved.csv` under `nport_returns/` | Accepted | |
| Push message `failed to push some refs` | Accepted, since `ls-remote` and the fresh clone both show the commit. If it recurs, run `git fetch` and confirm before carrying on. | |

The stop condition in 02b step 2.1b becomes: stop only if a month is missing outside 2025-08 to 2025-10, or if any later month after 2025-10 is missing.

---

## C. Steps

1. **Finish 2.1b** with the 2.3b price pull, as 02b intended. Write `nav_monthly.csv` (Akre months 2025-08 to 2025-10 absent; source `nport_b5` up to 2025-07 and `yfinance_etf` from 2025-11) and the Jensen and Polen cross-check. Commit `step 2.1b-2: NAV monthly table and B.5 cross-check`, after 2.3b.
2. **Then 2.1c, 2.3b, 2.4 and 2.5,** exactly as written in 02b Section C. The order is 2.1c, 2.3b, then 2.1b-2, then 2.4 and 2.5.
3. Add `n_quarters` to the OPEN-19 `gate.csv` schema. It is built in Section 3; note it in `CLAUDE.md` `## Amendments` as line 11, citing this file.
4. `decisions/OPEN.md` returns to its pointer line, and OPEN-33 moves to a new `decisions/section_2_review.md` with the table above.

---

## D. Review evidence

Everything in 02b Section D, plus `nav_monthly.csv` per fund: first month, last month, count by source, and every missing month.

---

## E. End of session

Status file: `instructions/02c_section_2_completion.status.md`, per rule 11. Push the step commits, run the fresh-clone check against GitHub, then commit and push the review and status files.
