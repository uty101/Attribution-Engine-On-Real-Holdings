from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from attrib.config import load_config
from attrib.factors import ALPHA, factor_contrib_by_year, returns_based

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
NAMES = list(CFG.factors.names)
N_MONTHS = 120  # instructions/05_section_5.md, D 5.1
TRUE_ALPHA = 0.002
TRUE_BETAS = [1.0, 0.3, -0.2, 0.1, 0.05, -0.15]
FACTOR_SCALE, NOISE_SCALE = 0.04, 0.01
TOL_BETAS = 1e-10  # instructions/05, D 5.1
TOL_SE = 1e-12
TOL_YEAR = 1e-12


def _synthetic(noise: bool, start: str = "2010-01") -> tuple[pd.Series, pd.DataFrame]:
    """instructions/05, D 5.1: factors from default_rng(run.bootstrap_seed), standard normal x 0.04;
    y = 0.002 + X b; with `noise`, standard normal x 0.01 from the same generator, drawn after the
    factors."""
    rng = np.random.default_rng(CFG.run.bootstrap_seed)
    idx = pd.period_range(start, periods=N_MONTHS, freq="M", name="month")
    X = pd.DataFrame(rng.standard_normal((N_MONTHS, len(NAMES))) * FACTOR_SCALE, index=idx, columns=NAMES)
    y = TRUE_ALPHA + X.to_numpy() @ np.array(TRUE_BETAS)
    if noise:
        y = y + rng.standard_normal(N_MONTHS) * NOISE_SCALE
    return pd.Series(y, index=idx, name="excess"), X


def test_recovers_known_betas():
    y, X = _synthetic(noise=False)
    fit = returns_based(y, X, CFG.factors.hac_maxlags)
    expected = pd.Series([TRUE_ALPHA, *TRUE_BETAS], index=[ALPHA, *NAMES])
    err = (fit["value"] - expected).abs()
    print(pd.DataFrame({"value": fit["value"], "expected": expected, "abs_err": err}).to_string())
    assert list(fit["value"].index) == [ALPHA, *NAMES]
    assert fit["n_months"] == N_MONTHS
    assert err.max() < TOL_BETAS


def test_hac_matches_statsmodels():
    y, X = _synthetic(noise=True)
    fit = returns_based(y, X, CFG.factors.hac_maxlags)
    # instructions/05, Section C: the exact call
    direct = sm.OLS(y, sm.add_constant(X)).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    se = direct.bse.rename(index={"const": ALPHA})
    err = (fit["se_hac"] - se).abs()
    print(pd.DataFrame({"se_hac": fit["se_hac"], "direct": se, "abs_err": err}).to_string())
    assert list(fit["se_hac"].index) == [ALPHA, *NAMES]
    assert err.max() < TOL_SE
    assert (fit["t_hac"] - direct.tvalues.rename(index={"const": ALPHA})).abs().max() < TOL_SE


def test_year_rows_sum():
    """Starts in April, so the first and last years are partial (9 and 3 months)."""
    y, X = _synthetic(noise=True, start="2015-04")
    fit = returns_based(y, X, CFG.factors.hac_maxlags)
    t2 = factor_contrib_by_year(y, X, fit).set_index("year")
    parts = t2[[*NAMES, ALPHA, "residual"]].sum(axis=1)
    summed = y.groupby(y.index.year).sum()
    print(t2.assign(parts=parts, summed=summed, abs_err=(parts - summed).abs()).to_string())
    assert list(t2.index) == list(range(2015, 2026))
    assert t2["n_months"].tolist() == [9, *[12] * 9, 3]
    assert (t2["excess_return"] - summed).abs().max() < TOL_YEAR
    assert (parts - summed).abs().max() < TOL_YEAR
