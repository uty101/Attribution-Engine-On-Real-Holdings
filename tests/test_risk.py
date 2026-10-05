from pathlib import Path

import numpy as np
import pandas as pd
from real_data import real_risk_inputs

from attrib.config import load_config
from attrib.risk import active_cov, fill_daily

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
RK = CFG.risk
SYM_TOL = 1e-15  # instructions/06, D 6.1


def _real_cov():
    """Akre and IVV at h = 2026-06-30 (instructions/06, D 6.1): the window rows of the union's daily
    returns, filled, then `active_cov`."""
    r = real_risk_inputs("akre", "2026-06-30")
    from pc.cov import window_daily

    X = window_daily(r["returns_d"], pd.Timestamp(r["q_start"]), RK.cov_months)
    filled, share = fill_daily(X, r["buckets"])
    S, info = active_cov(filled, r["q_start"], RK.cov_months, RK.max_cond)
    return X, filled, share, S, info


def test_pc_imports_offline():
    """Project 3's functions import with sockets disabled (kickoff 8, step 6.1)."""
    from pc.cov import condition_cov, cov_lw_cc, window_daily
    from pc.stats import stationary_bootstrap_indices

    assert all(callable(f) for f in (condition_cov, cov_lw_cc, window_daily, stationary_bootstrap_indices))


def test_fill_rule_synthetic():
    """Kickoff 5.10 on a hand-built panel. A, B, C are BusEq; D, E are Hlth; F is Enrgy alone.
    Day 2: A is missing -> mean of B and C. Day 3: D is missing -> E. Day 4: F is missing, no other
    Enrgy ticker -> mean of all 5 tickers with a return. Day 5: A and B are missing -> C alone
    (the mean is over the unfilled returns, so A does not see B's fill). Day 6: D and E are
    missing -> no other Hlth ticker has a return -> mean of A, B, C and F."""
    idx = pd.date_range("2024-01-01", periods=6, freq="D")
    nan = np.nan
    X = pd.DataFrame(
        {
            "A": [0.01, nan, 0.03, 0.02, nan, 0.01],
            "B": [0.02, 0.04, 0.01, 0.00, nan, 0.03],
            "C": [0.03, 0.02, 0.05, -0.01, 0.06, 0.02],
            "D": [0.00, 0.01, nan, 0.04, 0.02, nan],
            "E": [0.01, 0.03, -0.02, 0.05, 0.01, nan],
            "F": [-0.01, 0.02, 0.02, nan, 0.03, 0.04],
        },
        index=idx,
    )
    buckets = pd.Series({"A": "BusEq", "B": "BusEq", "C": "BusEq", "D": "Hlth", "E": "Hlth", "F": "Enrgy"})
    filled, share = fill_daily(X, buckets)
    print(filled.to_string())
    print(share.to_string())
    hand = X.copy()
    hand.loc[idx[1], "A"] = (0.04 + 0.02) / 2
    hand.loc[idx[2], "D"] = -0.02
    hand.loc[idx[3], "F"] = (0.02 + 0.00 - 0.01 + 0.04 + 0.05) / 5
    hand.loc[idx[4], ["A", "B"]] = 0.06
    hand.loc[idx[5], ["D", "E"]] = (0.01 + 0.03 + 0.02 + 0.04) / 4
    assert filled.notna().all().all()
    assert np.allclose(filled.to_numpy(), hand.to_numpy(), rtol=0, atol=1e-15)
    assert share.to_dict() == {"A": 2 / 6, "B": 1 / 6, "C": 0.0, "D": 2 / 6, "E": 1 / 6, "F": 1 / 6}


def test_cov_symmetric_positive_definite():
    """instructions/06, D 6.1: the real covariance for Akre at h = 2026-06-30, built from the
    committed raw data, is symmetric to 1e-15 and its smallest eigenvalue is > 0."""
    X, _, _, S, info = _real_cov()
    A = S.to_numpy()
    asym = float(np.abs(A - A.T).max())
    eig = np.linalg.eigvalsh(A)
    print(f"n_tickers={A.shape[0]} n_days={info['n_days']} max|S - S'|={asym:.3e} "
          f"min eig={eig[0]:.6e} max eig={eig[-1]:.6e} info={info}")
    assert list(S.index) == list(S.columns) == list(X.columns)
    assert asym <= SYM_TOL
    assert eig[0] > 0


def test_fill_share_bounds():
    """instructions/06, D 6.1: on the real Akre 2026-06-30 window, every fill share lies in [0, 1],
    and every ticker with a return on every day of the window has share 0."""
    X, filled, share, _, _ = _real_cov()
    full = X.notna().all(axis=0)
    print(f"{len(share)} tickers, {int(full.sum())} with a full history, {int((share > 0).sum())} filled; "
          f"largest shares:\n{share.sort_values(ascending=False).head(10).to_string()}")
    assert share.between(0, 1).all()
    assert (share[full] == 0).all()
    assert (share[~full] > 0).all()
    assert filled.notna().all().all()
