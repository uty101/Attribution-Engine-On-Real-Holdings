"""Multi-period linking of Brinson effects, Carino and Menchero (kickoff Section 5.6; D-21 B).

`rP` and `rB` are the per-period book returns indexed by t. `effects` is long: columns t, bucket,
allocation, selection, interaction. The result has columns bucket, allocation, selection,
interaction, 1 row per bucket in order of first appearance in `effects`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from attrib.brinson import EFFECTS

# kickoff 5.6: the Menchero alpha is 0 when sum_t d_t^2 < 1e-24
SUM_D2_TOL = 1e-24


def _totals(rP: pd.Series, rB: pd.Series) -> tuple[pd.Series, pd.Series, float, float, float]:
    """(r_P,t and r_B,t sorted by t, R_P, R_B, D) per kickoff 5.6."""
    rP, rB = rP.sort_index().astype("float64"), rB.sort_index().astype("float64")
    if not rP.index.equals(rB.index):
        raise ValueError("rP and rB must share their periods")
    R_P, R_B = float(np.prod(1 + rP.to_numpy()) - 1), float(np.prod(1 + rB.to_numpy()) - 1)
    return rP, rB, R_P, R_B, R_P - R_B


def _link(effects: pd.DataFrame, factor: pd.Series) -> pd.DataFrame:
    """Sum over t of factor_t x effect_t per bucket."""
    missing = sorted(set(effects["t"]) - set(factor.index))
    if missing:
        raise ValueError(f"effects have periods with no return: {missing}")
    f = effects["t"].map(factor)
    out = effects[EFFECTS].mul(f, axis=0).groupby(effects["bucket"], sort=False).sum()
    return out.reset_index()[["bucket", *EFFECTS]]


def carino_factors(rP: pd.Series, rB: pd.Series, zero_tol: float = 1e-12) -> pd.Series:
    """k_t / k by t (kickoff 5.6, with the limits k_t = 1/(1 + r_P,t) when |d_t| < zero_tol and
    k = 1/(1 + R_P) when |D| < zero_tol; zero_tol is `linking.zero_tol`)."""
    rP, rB, R_P, R_B, D = _totals(rP, rB)
    d = rP - rB
    k_t = pd.Series(
        np.where(d.abs() < zero_tol, 1 / (1 + rP), (np.log1p(rP) - np.log1p(rB)) / d.where(d.abs() >= zero_tol, 1.0)),
        index=rP.index,
    )
    k = 1 / (1 + R_P) if abs(D) < zero_tol else (np.log1p(R_P) - np.log1p(R_B)) / D
    return k_t / k


def menchero_factors(rP: pd.Series, rB: pd.Series, zero_tol: float = 1e-12) -> pd.Series:
    """M + alpha_t by t (kickoff 5.6, with the limits M = (1 + R_P)^((T - 1)/T) when
    |D| < zero_tol and alpha_t = 0 when sum_t d_t^2 < 1e-24; zero_tol is `linking.zero_tol`)."""
    rP, rB, R_P, R_B, D = _totals(rP, rB)
    T = len(rP)
    d = rP - rB
    if abs(D) < zero_tol:
        M = (1 + R_P) ** ((T - 1) / T)
    else:
        M = (D / T) / ((1 + R_P) ** (1 / T) - (1 + R_B) ** (1 / T))
    sd2 = float((d**2).sum())
    alpha = d * 0.0 if sd2 < SUM_D2_TOL else (D - M * float(d.sum())) / sd2 * d
    return M + alpha


def carino(rP: pd.Series, rB: pd.Series, effects: pd.DataFrame, zero_tol: float = 1e-12) -> pd.DataFrame:
    """Carino-linked effects: sum_t (k_t / k) effect_t per bucket (kickoff 5.6)."""
    return _link(effects, carino_factors(rP, rB, zero_tol))


def menchero(rP: pd.Series, rB: pd.Series, effects: pd.DataFrame, zero_tol: float = 1e-12) -> pd.DataFrame:
    """Menchero-linked effects: sum_t (M + alpha_t) effect_t per bucket (kickoff 5.6)."""
    return _link(effects, menchero_factors(rP, rB, zero_tol))
