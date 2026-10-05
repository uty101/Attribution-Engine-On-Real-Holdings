from pathlib import Path

import numpy as np
import pandas as pd
from real_data import real_risk_inputs

from attrib.config import load_config
from attrib.risk import active_cov, active_share, fill_daily, issuer_weights, te_decomposition

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


EULER_TOL = 1e-12  # kickoff 5.10
DIRECT_TOL = 1e-12  # instructions/06, D 6.2


def _pos(rows):
    """POSITION_RETURNS-like rows (sec_id, weight)."""
    return pd.DataFrame(rows, columns=["sec_id", "weight"])


def _smap(rows):
    """SECURITY_MAP-like rows (sec_id, cik); '' is no CIK."""
    return pd.DataFrame(rows, columns=["sec_id", "cik"])


def test_euler_identity():
    """Kickoff 5.10: sum CTE = TE to 1e-12, on a random positive definite Sigma_m and an active
    vector summing to 0 (default_rng(run.bootstrap_seed): the factor loadings, then a)."""
    rng = np.random.default_rng(CFG.run.bootstrap_seed)
    n = 40
    L = rng.standard_normal((n, n)) * 0.02
    tick = [f"T{i:02d}" for i in range(n)]
    S = pd.DataFrame(L @ L.T + np.eye(n) * 1e-4, index=tick, columns=tick)
    a = pd.Series(rng.standard_normal(n) * 0.01, index=tick)
    a -= a.mean()
    dec = te_decomposition(a, S)
    te = float(np.sqrt(12 * a.to_numpy() @ S.to_numpy() @ a.to_numpy()))
    print(f"TE={te!r} sum CTE={dec['cte'].sum()!r} diff={abs(dec['cte'].sum() - te):.3e}")
    assert list(dec.columns) == ["ticker", "a", "mcte", "cte"]
    assert abs(dec["cte"].sum() - te) < EULER_TOL


def test_active_share_identical_is_zero():
    pos = _pos([("A1", 0.5), ("B1", 0.3), ("C1", 0.2)])
    smap = _smap([("A1", "1"), ("B1", "2"), ("C1", "")])
    w = issuer_weights(pos, smap)
    assert active_share(w, w) == 0.0


def test_active_share_disjoint_is_one():
    smap = _smap([("A1", "1"), ("B1", "2"), ("C1", ""), ("D1", "")])
    wP = issuer_weights(_pos([("A1", 0.6), ("C1", 0.4)]), smap)
    wB = issuer_weights(_pos([("B1", 0.7), ("D1", 0.3)]), smap)
    assert abs(active_share(wP, wB) - 1.0) < EULER_TOL


def test_share_classes_net():
    """instructions/06, D 6.2: GOOG and GOOGL share 1 CIK. The fund holds them 0.30 / 0.10 (issuer
    0.40), the benchmark 0.05 / 0.25 (issuer 0.30); MSFT is 0.60 in the fund and 0.70 in the
    benchmark. Issuer-level AS = 1/2 (|0.40 - 0.30| + |0.60 - 0.70|) = 0.10; at sec_id level it
    would be 1/2 (0.25 + 0.15 + 0.10) = 0.25."""
    smap = _smap([("38259P508", "1652044"), ("38259P706", "1652044"), ("594918104", "789019")])
    wP = issuer_weights(_pos([("38259P706", 0.30), ("38259P508", 0.10), ("594918104", 0.60)]), smap)
    wB = issuer_weights(_pos([("38259P706", 0.05), ("38259P508", 0.25), ("594918104", 0.70)]), smap)
    print(pd.DataFrame({"fund": wP, "bench": wB}).to_string())
    assert abs(wP["cik:1652044"] - 0.40) < EULER_TOL and abs(wB["cik:1652044"] - 0.30) < EULER_TOL
    assert abs(active_share(wP, wB) - 0.10) < EULER_TOL


def test_te_matches_direct_quadratic():
    """instructions/06, D 6.2: TE from `te_decomposition` equals sqrt(12 * a @ S @ a) computed
    directly, to 1e-12, on the real Akre 2026-06-30 inputs."""
    r = real_risk_inputs("akre", "2026-06-30")
    _, _, _, S, _ = _real_cov()
    a = r["wP"].reindex(S.index, fill_value=0.0) - r["wB"].reindex(S.index, fill_value=0.0)
    dec = te_decomposition(a, S)
    direct = float(np.sqrt(12 * a.to_numpy() @ S.to_numpy() @ a.to_numpy()))
    print(f"TE (sum CTE)={dec['cte'].sum()!r} direct={direct!r} sum a={a.sum():.3e} n={len(a)}")
    assert abs(dec["cte"].sum() - direct) < DIRECT_TOL
