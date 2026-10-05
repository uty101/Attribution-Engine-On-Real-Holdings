from pathlib import Path

import numpy as np
import pandas as pd

from attrib.config import load_config
from attrib.factors import fallback_betas, holdings_exposure, stock_betas

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
NAMES = list(CFG.factors.names)
WINDOW, MIN_OBS = CFG.factors.stock_beta_window, CFG.factors.stock_beta_min_obs
TOL = 1e-10


def test_min_obs_rule():
    """instructions/05, D 5.2: in 1 bucket, stocks A and B have every month of the window, C has
    min_obs - 1 = 23 and D has min_obs = 24. Returns are exact linear functions of the factors
    (default_rng(run.bootstrap_seed): factors, then each stock's betas), so an own beta is its true
    beta. C gets the mean of A, B and D; D gets its own."""
    rng = np.random.default_rng(CFG.run.bootstrap_seed)
    end = pd.Period("2020-12", freq="M")
    months = pd.period_range(end - (WINDOW - 1), end, freq="M")
    X = pd.DataFrame(rng.standard_normal((WINDOW, len(NAMES))) * 0.04, index=months, columns=NAMES)
    true = pd.DataFrame(rng.standard_normal((4, len(NAMES))), index=list("ABCD"), columns=NAMES)
    Y = pd.DataFrame(0.001 + X.to_numpy() @ true.T.to_numpy(), index=months, columns=true.index)
    Y.iloc[: WINDOW - (MIN_OBS - 1), Y.columns.get_loc("C")] = np.nan
    Y.iloc[: WINDOW - MIN_OBS, Y.columns.get_loc("D")] = np.nan
    assert Y.notna().sum().tolist() == [WINDOW, WINDOW, MIN_OBS - 1, MIN_OBS]

    betas = stock_betas(Y, X, end, WINDOW, MIN_OBS)
    print(betas.to_string())
    assert betas.loc["C"].isna().all()
    assert (betas.loc[["A", "B", "D"]] - true.loc[["A", "B", "D"]]).abs().max().max() < TOL

    filled = fallback_betas(betas, pd.Series("Hlth", index=true.index))
    print(filled.to_string())
    assert (filled.loc["C"] - true.loc[["A", "B", "D"]].mean()).abs().max() < TOL
    assert (filled.loc["D"] - true.loc["D"]).abs().max() < TOL


def test_bucket_fallback():
    """instructions/05, D 5.2: the fallback beta is the mean of the valid betas in the same bucket
    on the same side. X is held by both sides with no valid beta; the fund's other Hlth names are
    F1 and F2, the benchmark's are B1 and F1, so X takes a different beta on each side. G has no
    valid same-bucket beta on the fund side, so it is left out and the rest renormalised."""
    rows = {
        "F1": [1.0, 0.2, -0.1, 0.0, 0.3, 0.1],
        "F2": [0.8, -0.2, 0.3, 0.2, -0.1, 0.0],
        "B1": [1.3, 0.5, 0.1, -0.4, 0.0, 0.2],
        "F3": [0.9, 0.1, 0.0, 0.1, 0.1, -0.1],
        "X": [np.nan] * 6,
        "G": [np.nan] * 6,
    }
    betas = pd.DataFrame.from_dict(rows, orient="index", columns=NAMES)
    buckets = pd.Series({"F1": "Hlth", "F2": "Hlth", "B1": "Hlth", "F3": "Money", "X": "Hlth", "G": "Enrgy"})
    w_fund = pd.Series({"F1": 0.3, "F2": 0.2, "F3": 0.1, "X": 0.25, "G": 0.15})
    w_bench = pd.Series({"F1": 0.1, "B1": 0.5, "X": 0.4})

    x_fund = betas.loc[["F1", "F2"]].mean()
    x_bench = betas.loc[["B1", "F1"]].mean()
    side_f = fallback_betas(betas.loc[w_fund.index], buckets)
    side_b = fallback_betas(betas.loc[w_bench.index], buckets)
    print(pd.DataFrame({"fund_X": side_f.loc["X"], "hand_fund": x_fund, "bench_X": side_b.loc["X"],
                        "hand_bench": x_bench}).to_string())
    assert (side_f.loc["X"] - x_fund).abs().max() < TOL
    assert (side_b.loc["X"] - x_bench).abs().max() < TOL
    assert side_f.loc["G"].isna().all()

    held = ["F1", "F2", "F3", "X"]
    w = w_fund[held] / w_fund[held].sum()
    hand_f = (betas.loc[["F1", "F2", "F3"]].T @ w[["F1", "F2", "F3"]]) + w["X"] * x_fund
    hand_b = betas.loc["F1"] * 0.1 + betas.loc["B1"] * 0.5 + x_bench * 0.4
    exp_f = holdings_exposure(w_fund, betas, buckets)
    exp_b = holdings_exposure(w_bench, betas, buckets)
    print(pd.DataFrame({"fund": exp_f, "hand_fund": hand_f, "bench": exp_b, "hand_bench": hand_b}).to_string())
    assert (exp_f - hand_f).abs().max() < TOL
    assert (exp_b - hand_b).abs().max() < TOL
