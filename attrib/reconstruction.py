"""Reconstruction error and the fund gate (kickoff Section 5.4; amendment 11)."""

from __future__ import annotations

import numpy as np
import pandas as pd

TABLE4 = ["entity", "t", "q_start", "q_end", "book_return", "nav_return", "gap"]


def quarter_nav_return(nav: pd.DataFrame, entity: str, holdings_date) -> float:
    """Amendment 11: the compound of the 3 monthly NAV returns of the calendar months after
    `holdings_date`, blank (NaN) unless all 3 are present. `nav` has columns entity, month
    (`YYYY-MM`), ret."""
    first = pd.Period(pd.Timestamp(holdings_date), freq="M") + 1
    months = [str(first + i) for i in range(3)]
    r = nav[nav["entity"] == entity].set_index("month")["ret"].reindex(months)
    return float(np.prod(1 + r.to_numpy()) - 1) if r.notna().all() else float("nan")


def reconstruction_table(book_q: pd.DataFrame, nav: pd.DataFrame, cal: pd.DataFrame) -> pd.DataFrame:
    """TABLE4: per (entity, t) of `book_q` (entity, t, book_return), the quarterly NAV return
    (`quarter_nav_return`) and gap = book_return - nav_return (kickoff 5.4), blank when the NAV
    return is blank. `cal` is QUARTERS."""
    q = cal.set_index("t")
    rows = []
    for eid, t, br in zip(book_q["entity"], book_q["t"], book_q["book_return"]):
        nr = quarter_nav_return(nav, eid, q.at[t, "holdings_date"])
        rows.append([eid, t, q.at[t, "q_start"], q.at[t, "q_end"], br, nr, br - nr])
    out = pd.DataFrame(rows, columns=TABLE4)
    for c in ("q_start", "q_end"):
        out[c] = pd.to_datetime(out[c]).dt.strftime("%Y-%m-%d")
    return out


GATE = ["fund", "corr", "pass", "n_quarters", "mean_gap", "std_gap", "mean_abs_gap", "te_gap_ann"]


def gate(table4: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """GATE per entity of `table4` (D-19 A with amendment 11): Pearson correlation of book_return
    with nav_return over the quarters with a NAV return, pass if corr >= threshold (kickoff 5.4),
    their count, and the gap's mean, standard deviation (ddof 1), mean absolute value and
    annualised tracking error (std x 2, kickoff 5.4)."""
    rows = []
    for eid, g in table4.groupby("entity", sort=False):
        g = g.dropna(subset=["nav_return"])
        corr = float(np.corrcoef(g["book_return"], g["nav_return"])[0, 1])
        std = float(g["gap"].std(ddof=1))
        rows.append([eid, corr, corr >= threshold, len(g), float(g["gap"].mean()), std,
                     float(g["gap"].abs().mean()), std * 2])  # kickoff 5.4: quarterly std x 2 = sqrt(4)
    return pd.DataFrame(rows, columns=GATE)
