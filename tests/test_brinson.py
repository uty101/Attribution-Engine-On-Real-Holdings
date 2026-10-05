from pathlib import Path

import numpy as np
import pandas as pd
from real_data import real_buckets, side

from attrib.brinson import EFFECTS, brinson_fachler
from attrib.config import load_config
from attrib.returns import BUCKETS_ORDER, book_return

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
TOL = 1e-10  # kickoff 5.5 and Section 8, step 4.1
TOL_HAND = 1e-12  # instructions/04_section_4.md, C 4.1


def _s(values, index=("A", "B", "C")) -> pd.Series:
    return pd.Series(values, index=list(index), dtype="float64")


def _identity_gap(wP, rP, wB, rB) -> float:
    """|sum of the 3 effects over buckets - (r_P - r_B)|, the book returns over held buckets."""
    eff = brinson_fachler(wP, rP, wB, rB)
    r_P = float((wP[wP > 0] * rP[wP > 0]).sum())
    r_B = float((wB[wB > 0] * rB[wB > 0]).sum())
    return abs(float(eff[EFFECTS].to_numpy().sum()) - (r_P - r_B))


def test_identity_random_1000():
    """1000 synthetic cases over the 14 buckets, drawn in this order per case from
    default_rng(run.bootstrap_seed): fund weights, benchmark weights (Dirichlet, ones), then for
    each side a mask leaving each bucket held with probability 0.7 (at least 1 bucket held), then
    fund and benchmark bucket returns (normal, sd 0.1). Weights are renormalised over held buckets
    and returns are blank where a side holds 0."""
    rng = np.random.default_rng(CFG.run.bootstrap_seed)
    n = len(BUCKETS_ORDER)
    worst = 0.0
    for _ in range(1000):
        w = [rng.dirichlet(np.ones(n)) for _ in range(2)]
        masks = [rng.random(n) < 0.7 for _ in range(2)]
        r = [rng.normal(0.0, 0.1, n) for _ in range(2)]
        sides = []
        for wi, mi, ri in zip(w, masks, r):
            mi[np.argmax(wi)] = True
            wi = np.where(mi, wi, 0.0)
            wi = wi / wi.sum()
            sides.append((_s(wi, BUCKETS_ORDER), _s(np.where(mi, ri, np.nan), BUCKETS_ORDER)))
        (wP, rP), (wB, rB) = sides
        worst = max(worst, _identity_gap(wP, rP, wB, rB))
    print(f"1000 cases, max |sum of effects - (r_P - r_B)| = {worst:.3e}")
    assert worst < TOL


def test_identity_every_real_fund_quarter():
    buckets, cal = real_buckets()
    rows = []
    for fund, e in CFG.entities.items():
        if e.type != "fund":
            continue
        for t in cal["t"]:
            wP, rP = side(buckets, fund, t)
            wB, rB = side(buckets, e.benchmark, t)
            eff = brinson_fachler(wP, rP, wB, rB)
            d = book_return(buckets[(buckets["entity"] == fund) & (buckets["t"] == t)]) - book_return(
                buckets[(buckets["entity"] == e.benchmark) & (buckets["t"] == t)]
            )
            rows.append([fund, t, d, abs(float(eff[EFFECTS].to_numpy().sum()) - d)])
    out = pd.DataFrame(rows, columns=["fund", "t", "r_P - r_B", "abs_error"])
    print(out.groupby("fund")["abs_error"].max().to_string())
    assert len(out) == 3 * 28
    assert out["abs_error"].max() < TOL


def test_hand_worked_three_sector():
    """3 sectors A, B, C.

    Weights: fund (0.5, 0.3, 0.2); benchmark (0.4, 0.4, 0.2).
    Returns: fund (0.10, 0.02, -0.05); benchmark (0.08, 0.03, -0.04).
    r_B = 0.4 * 0.08 + 0.4 * 0.03 + 0.2 * -0.04 = 0.032 + 0.012 - 0.008 = 0.036.
    r_P = 0.5 * 0.10 + 0.3 * 0.02 + 0.2 * -0.05 = 0.050 + 0.006 - 0.010 = 0.046.
    Allocation = (w_P - w_B)(r_s^B - r_B):
        A: 0.1 * (0.08 - 0.036) = 0.0044; B: -0.1 * (0.03 - 0.036) = 0.0006; C: 0 * ... = 0.
    Selection = w_B (r_s^P - r_s^B):
        A: 0.4 * 0.02 = 0.008; B: 0.4 * -0.01 = -0.004; C: 0.2 * -0.01 = -0.002.
    Interaction = (w_P - w_B)(r_s^P - r_s^B):
        A: 0.1 * 0.02 = 0.002; B: -0.1 * -0.01 = 0.001; C: 0 * -0.01 = 0.
    Sum = 0.0050 + 0.0020 + 0.0030 = 0.010 = 0.046 - 0.036.
    """
    wP, wB = _s([0.5, 0.3, 0.2]), _s([0.4, 0.4, 0.2])
    rP, rB = _s([0.10, 0.02, -0.05]), _s([0.08, 0.03, -0.04])
    eff = brinson_fachler(wP, rP, wB, rB)
    print(eff.to_string())
    assert np.allclose(eff["allocation"], [0.0044, 0.0006, 0.0], rtol=0, atol=TOL_HAND)
    assert np.allclose(eff["selection"], [0.008, -0.004, -0.002], rtol=0, atol=TOL_HAND)
    assert np.allclose(eff["interaction"], [0.002, 0.001, 0.0], rtol=0, atol=TOL_HAND)
    assert abs(float(eff.to_numpy().sum()) - 0.010) < TOL_HAND
    assert abs((0.046 - 0.036) - 0.010) < TOL_HAND


def test_empty_bucket_rules():
    """A is held by both sides, B only by the benchmark, C only by the fund, D by neither.

    r_B = 0.6 * 0.05 + 0.4 * 0.10 = 0.07. B: r^P := r^B (Convention 4.11), so selection and
    interaction are 0 and allocation is (0 - 0.4)(0.10 - 0.07) = -0.012. C: r^B := r_B, so
    allocation is (0.3 - 0)(r_B - r_B) = 0, selection 0 and interaction 0.3 (0.20 - 0.07) = 0.039.
    D contributes nothing.
    """
    idx = ["A", "B", "C", "D"]
    wP, rP = _s([0.7, 0.0, 0.3, 0.0], idx), _s([0.04, np.nan, 0.20, np.nan], idx)
    wB, rB = _s([0.6, 0.4, 0.0, 0.0], idx), _s([0.05, 0.10, np.nan, np.nan], idx)
    eff = brinson_fachler(wP, rP, wB, rB)
    print(eff.to_string())
    r_B = 0.07
    assert eff.loc["B", "selection"] == 0 and eff.loc["B", "interaction"] == 0
    assert abs(eff.loc["B", "allocation"] - (0 - 0.4) * (0.10 - r_B)) < TOL_HAND
    assert eff.loc["C", "allocation"] == 0 and eff.loc["C", "selection"] == 0
    assert abs(eff.loc["C", "interaction"] - 0.3 * (0.20 - r_B)) < TOL_HAND
    assert (eff.loc["D"] == 0).all()
    assert not eff.isna().any().any()
    assert _identity_gap(wP, rP, wB, rB) < TOL_HAND
