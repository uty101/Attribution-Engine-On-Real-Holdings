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
