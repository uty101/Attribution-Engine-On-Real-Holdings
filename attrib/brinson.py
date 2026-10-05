"""Brinson-Fachler single-period attribution (kickoff Section 5.5; Convention 4.11)."""

from __future__ import annotations

import pandas as pd

EFFECTS = ["allocation", "selection", "interaction"]


def fill_empty(wP: pd.Series, rP: pd.Series, wB: pd.Series, rB: pd.Series) -> tuple[pd.Series, pd.Series, float]:
    """Convention 4.11 on 1 period: (r_s^P, r_s^B, r_B) with the empty-bucket rules applied.

    r_B = sum of w_s^B r_s^B over the buckets the benchmark holds. Where the benchmark has 0
    weight, r_s^B := r_B; where the fund has 0 weight, r_s^P := r_s^B (after that fill). A bucket
    with 0 weight on both sides then has r_s^P = r_s^B = r_B and contributes nothing.
    """
    held_B = wB > 0
    r_B = float((wB[held_B] * rB[held_B]).sum())
    rB_f = rB.where(held_B, r_B)
    rP_f = rP.where(wP > 0, rB_f)
    return rP_f, rB_f, r_B


def brinson_fachler(wP: pd.Series, rP: pd.Series, wB: pd.Series, rB: pd.Series) -> pd.DataFrame:
    """Allocation, selection and interaction per bucket (kickoff 5.5), indexed by bucket in the
    order of `wP`. The 4 inputs share 1 index; `rP` and `rB` may be blank where their weight is 0
    (Convention 4.11, `fill_empty`). With both weight vectors summing to 1, the 3 effects summed
    over buckets equal r_P - r_B."""
    wB, rP, rB = wB.reindex(wP.index), rP.reindex(wP.index), rB.reindex(wP.index)
    rP_f, rB_f, r_B = fill_empty(wP, rP, wB, rB)
    out = pd.DataFrame(
        {
            "allocation": (wP - wB) * (rB_f - r_B),
            "selection": wB * (rP_f - rB_f),
            "interaction": (wP - wB) * (rP_f - rB_f),
        },
        index=wP.index,
    )
    out.index.name = "bucket"
    return out
