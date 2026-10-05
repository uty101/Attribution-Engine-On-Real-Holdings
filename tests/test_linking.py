from pathlib import Path

import numpy as np
import pandas as pd
from real_data import real_buckets, side

from attrib.brinson import EFFECTS, brinson_fachler
from attrib.config import load_config
from attrib.linking import carino, menchero
from attrib.returns import BUCKETS_ORDER, book_return

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
ZT = CFG.linking.zero_tol
TOL = 1e-12  # kickoff 5.6, synthetic data
TOL_REAL = 1e-10  # kickoff 5.6, real data
TOL_SINGLE = 1e-15  # instructions/04_section_4.md, C 4.2
METHODS = {"carino": carino, "menchero": menchero}


def _random_periods(T: int, seed: int):
    """T periods of Brinson effects on random 14-bucket books, from default_rng(seed): per period,
    fund weights, benchmark weights (Dirichlet, ones), fund returns, benchmark returns (normal,
    sd 0.1). Returns (rP, rB, effects) in the D-21 B layout."""
    rng = np.random.default_rng(seed)
    n = len(BUCKETS_ORDER)
    rP, rB, eff = {}, {}, []
    for t in range(1, T + 1):
        wP, wB = (pd.Series(rng.dirichlet(np.ones(n)), index=BUCKETS_ORDER) for _ in range(2))
        sP, sB = (pd.Series(rng.normal(0.0, 0.1, n), index=BUCKETS_ORDER) for _ in range(2))
        rP[t], rB[t] = float((wP * sP).sum()), float((wB * sB).sum())
        eff.append(brinson_fachler(wP, sP, wB, sB).reset_index().assign(t=t))
    return pd.Series(rP), pd.Series(rB), pd.concat(eff, ignore_index=True)[["t", "bucket", *EFFECTS]]


def _split(rP: pd.Series, rB: pd.Series) -> pd.DataFrame:
    """Effects that sum to d_t in each period, split over 2 buckets and the 3 effects with fixed
    shares: X gets 0.3, 0.2 and 0.1 of d_t, Y gets 0.25, 0.1 and 0.05."""
    shares = {"X": (0.3, 0.2, 0.1), "Y": (0.25, 0.1, 0.05)}
    rows = [[t, b, *(s * (rP[t] - rB[t]) for s in sh)] for t in rP.index for b, sh in shares.items()]
    return pd.DataFrame(rows, columns=["t", "bucket", *EFFECTS])


def _D(rP: pd.Series, rB: pd.Series) -> float:
    return float(np.prod(1 + rP.to_numpy()) - np.prod(1 + rB.to_numpy()))


def _linked_sum(linked: pd.DataFrame) -> float:
    return float(linked[EFFECTS].to_numpy().sum())


def test_carino_sums_to_D_synthetic():
    rP, rB, eff = _random_periods(28, CFG.run.bootstrap_seed)
    err = abs(_linked_sum(carino(rP, rB, eff, ZT)) - _D(rP, rB))
    print(f"D = {_D(rP, rB):.6f}, |Carino sum - D| = {err:.3e}")
    assert err < TOL


def test_menchero_sums_to_D_synthetic():
    rP, rB, eff = _random_periods(28, CFG.run.bootstrap_seed)
    err = abs(_linked_sum(menchero(rP, rB, eff, ZT)) - _D(rP, rB))
    print(f"D = {_D(rP, rB):.6f}, |Menchero sum - D| = {err:.3e}")
    assert err < TOL


def test_linked_sums_to_D_real():
    buckets, cal = real_buckets()
    rows = []
    for fund, e in CFG.entities.items():
        if e.type != "fund":
            continue
        rP, rB, eff = {}, {}, []
        for t in cal["t"]:
            wP, sP = side(buckets, fund, t)
            wB, sB = side(buckets, e.benchmark, t)
            rP[t] = book_return(buckets[(buckets["entity"] == fund) & (buckets["t"] == t)])
            rB[t] = book_return(buckets[(buckets["entity"] == e.benchmark) & (buckets["t"] == t)])
            eff.append(brinson_fachler(wP, sP, wB, sB).reset_index().assign(t=t))
        rP, rB, eff = pd.Series(rP), pd.Series(rB), pd.concat(eff, ignore_index=True)
        D = _D(rP, rB)
        for name, f in METHODS.items():
            rows.append([fund, name, D, abs(_linked_sum(f(rP, rB, eff, ZT)) - D)])
    out = pd.DataFrame(rows, columns=["fund", "method", "D", "abs_error"])
    print(out.to_string())
    assert len(out) == 6
    assert out["abs_error"].max() < TOL_REAL


def test_carino_limit():
    """Period 2 has r_P = r_B exactly (d_2 = 0), so k_2 takes the limit 1/(1 + r_P,2)."""
    rP = pd.Series({1: 0.08, 2: 0.03, 3: -0.05})
    rB = pd.Series({1: 0.05, 2: 0.03, 3: -0.02})
    assert rP[2] - rB[2] == 0
    linked = carino(rP, rB, _split(rP, rB), ZT)
    print(linked.to_string())
    assert not linked[EFFECTS].isna().any().any()
    assert abs(_linked_sum(linked) - _D(rP, rB)) < TOL


def test_equal_period_uses_limit():
    """Period 2 has r_P = r_B exactly but nonzero effects that cancel (allocation +0.004,
    selection -0.004 in bucket X). The linked result must weight them with k_2 = 1/(1 + r_P,2),
    the kickoff 5.6 limit."""
    rP = pd.Series({1: 0.06, 2: 0.02, 3: 0.01})
    rB = pd.Series({1: 0.04, 2: 0.02, 3: 0.03})
    eff = _split(rP, rB)
    eff.loc[(eff["t"] == 2) & (eff["bucket"] == "X"), ["allocation", "selection"]] = [0.004, -0.004]
    linked = carino(rP, rB, eff, ZT).set_index("bucket")
    R_P, R_B = np.prod(1 + rP) - 1, np.prod(1 + rB) - 1
    k = (np.log1p(R_P) - np.log1p(R_B)) / (R_P - R_B)
    k_t = {1: (np.log1p(0.06) - np.log1p(0.04)) / (0.06 - 0.04), 2: 1 / 1.02,
           3: (np.log1p(0.01) - np.log1p(0.03)) / (0.01 - 0.03)}
    x = eff[eff["bucket"] == "X"].set_index("t")
    expected = {c: sum(k_t[t] / k * x.at[t, c] for t in (1, 2, 3)) for c in EFFECTS}
    print(linked.to_string())
    for c in EFFECTS:
        assert abs(linked.at["X", c] - expected[c]) < TOL
    assert abs(_linked_sum(linked.reset_index()) - _D(rP, rB)) < TOL


def test_menchero_limit():
    """D = 0 over the whole period: r_P = (0.10, 0.05, -0.10) and r_B = (-0.10, 0.05, 0.10)
    compound to the same total, and period 2 has r_P = r_B. M takes the limit
    (1 + R_P)^((T - 1)/T)."""
    rP = pd.Series({1: 0.10, 2: 0.05, 3: -0.10})
    rB = pd.Series({1: -0.10, 2: 0.05, 3: 0.10})
    assert abs(_D(rP, rB)) < ZT
    for name, f in METHODS.items():
        linked = f(rP, rB, _split(rP, rB), ZT)
        print(name)
        print(linked.to_string())
        assert np.isfinite(linked[EFFECTS].to_numpy()).all()
        assert abs(_linked_sum(linked)) < TOL


def test_single_period_unchanged():
    rP, rB, eff = _random_periods(1, CFG.run.bootstrap_seed)
    for name, f in METHODS.items():
        linked = f(rP, rB, eff, ZT).set_index("bucket")
        diff = (linked[EFFECTS] - eff.set_index("bucket")[EFFECTS]).abs().to_numpy().max()
        print(f"{name}: max |linked - input| = {diff:.3e}")
        assert diff < TOL_SINGLE
