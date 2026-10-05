"""Fama-French factors (kickoff Sections 5.7 and 5.8; instructions/05, Section C).

Monthly series are indexed by `pd.Period(freq="M")`. `factors` holds the factor columns only, in
the order of `factors.names` (mkt, smb, hml, rmw, cma, umd), in decimals.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

# instructions/02_section_2.md, C 2.3: French's column names -> the loader's
FRENCH_COLUMNS = {"Mkt-RF": "mkt", "SMB": "smb", "HML": "hml", "RMW": "rmw", "CMA": "cma", "Mom": "umd", "RF": "rf"}
ALPHA = "alpha"  # the name of the OLS constant in every output


def read_french_csv(path: str | Path) -> pd.DataFrame:
    """1 committed French monthly block, in percent, indexed by YYYYMM, headers stripped of whitespace."""
    df = pd.read_csv(path, index_col=0, skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    df.index = df.index.astype(int)
    return df.astype("float64")


def load_french(data_dir: str | Path) -> pd.DataFrame:
    """mkt, smb, hml, rmw, cma, umd, rf in decimals (Convention 4.15), indexed by `pd.Period(freq="M")`,
    on the months both files share."""
    d = Path(data_dir) / "raw" / "french"
    df = read_french_csv(d / "ff5_monthly.csv").join(read_french_csv(d / "mom_monthly.csv"), how="inner")
    df = df.rename(columns=FRENCH_COLUMNS)[list(FRENCH_COLUMNS.values())] / 100  # Convention 4.15: percent / 100
    df.index = pd.PeriodIndex([pd.Period(f"{i // 100}-{i % 100:02d}", freq="M") for i in df.index], name="month")
    return df.sort_index()


def _aligned(excess: pd.Series, factors: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    """The months both share with no missing value (instructions/05, C: missing months are dropped)."""
    data = pd.concat([excess.rename("_y"), factors], axis=1, join="inner").dropna()
    return data["_y"], data[list(factors.columns)]


def returns_based(excess: pd.Series, factors: pd.DataFrame, maxlags: int) -> dict:
    """Full-sample OLS of `excess` on the factors with HAC standard errors (kickoff 5.7), with the
    exact call of instructions/05, Section C, on the months with no missing value.

    D-24 B: keys value, se_hac, t_hac (Series indexed alpha, then the factors), r2, resid_vol_ann
    (std(resid), ddof 1, x sqrt(12)), n_months, and resid (Series indexed by month).
    """
    y, X = _aligned(excess, factors)
    fit = sm.OLS(y, sm.add_constant(X)).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    names = {"const": ALPHA}
    return {
        "value": fit.params.rename(index=names),
        "se_hac": fit.bse.rename(index=names),
        "t_hac": fit.tvalues.rename(index=names),
        "r2": float(fit.rsquared),
        "resid_vol_ann": float(fit.resid.std(ddof=1) * np.sqrt(12)),  # kickoff 5.7: std(resid) x sqrt(12)
        "n_months": int(fit.nobs),
        "resid": fit.resid.rename("resid"),
    }


def rolling_betas(excess: pd.Series, factors: pd.DataFrame, window: int) -> pd.DataFrame:
    """Factor betas from plain OLS (with a constant) on every `window` consecutive calendar months
    with no missing month, indexed by the window's last month (instructions/05, Section C)."""
    data = pd.concat([excess.rename("_y"), factors], axis=1, join="inner").sort_index()
    if data.empty:
        return pd.DataFrame(columns=list(factors.columns), index=pd.PeriodIndex([], freq="M", name="month_end"))
    data = data.reindex(pd.period_range(data.index.min(), data.index.max(), freq="M"))
    complete = data.notna().all(axis=1).to_numpy()
    rows, ends = [], []
    for i in range(window - 1, len(data)):
        if not complete[i - window + 1 : i + 1].all():
            continue
        w = data.iloc[i - window + 1 : i + 1]
        params = sm.OLS(w["_y"], sm.add_constant(w[list(factors.columns)])).fit().params
        rows.append(params[list(factors.columns)].to_numpy())
        ends.append(data.index[i])
    return pd.DataFrame(rows, columns=list(factors.columns), index=pd.PeriodIndex(ends, freq="M", name="month_end"))


def factor_contrib_by_year(excess: pd.Series, factors: pd.DataFrame, fit: dict) -> pd.DataFrame:
    """TABLE2 for 1 series from its full-sample `fit` (kickoff 5.7; instructions/05, Section C):
    year, n_months, excess_return (the year's summed excess return), contribution per factor
    (sum of beta_j f_j,t), alpha (alpha x n_months), residual (sum of resid), r2_full. Over the
    months the fit used."""
    y, X = _aligned(excess, factors)
    beta = fit["value"]
    contrib = X * beta[list(factors.columns)]
    df = contrib.assign(excess_return=y, residual=fit["resid"].reindex(y.index), n_months=1)
    g = df.groupby(df.index.year)
    out = g[["n_months", "excess_return", *factors.columns]].sum()
    out[ALPHA] = beta[ALPHA] * out["n_months"]
    out["residual"] = g["residual"].sum()
    out["r2_full"] = fit["r2"]
    out.index.name = "year"
    return out.reset_index()[["year", "n_months", "excess_return", *factors.columns, ALPHA, "residual", "r2_full"]]


def stock_betas(monthly_excess: pd.DataFrame, factors: pd.DataFrame, end_month, window: int, min_obs: int) -> pd.DataFrame:
    """Factor betas per stock (kickoff 5.8): OLS with a constant of each column of `monthly_excess`
    on the factors over the `window` calendar months ending at `end_month`, on the months the
    stock has a return. Indexed by the columns of `monthly_excess`; a stock with fewer than
    `min_obs` months has a blank row (`fallback_betas` fills it)."""
    end = pd.Period(end_month, freq="M")
    months = pd.period_range(end - (window - 1), end, freq="M")
    f = factors.reindex(months)
    if f.isna().any().any():
        raise ValueError(f"factors missing in the window ending {end}")
    Y = monthly_excess.reindex(index=months).to_numpy(dtype="float64")
    X = np.column_stack([np.ones(len(months)), f.to_numpy()])
    ok = ~np.isnan(Y)
    n = ok.sum(axis=0)
    out = np.full((Y.shape[1], f.shape[1]), np.nan)
    full = n == len(months)
    if full.any():  # stocks with every month share 1 design matrix
        out[full] = np.linalg.lstsq(X, Y[:, full], rcond=None)[0][1:].T
    for j in np.flatnonzero((n >= min_obs) & ~full):
        out[j] = np.linalg.lstsq(X[ok[:, j]], Y[ok[:, j], j], rcond=None)[0][1:]
    return pd.DataFrame(out, index=monthly_excess.columns, columns=f.columns)


def fallback_betas(betas: pd.DataFrame, buckets: pd.Series) -> pd.DataFrame:
    """Kickoff 5.8: a blank row takes the mean of the valid rows of `betas` in its bucket
    (`buckets`, indexed like `betas`); it stays blank if its bucket has none."""
    b = buckets.reindex(betas.index)
    valid = betas.notna().all(axis=1)
    means = betas[valid].groupby(b[valid]).mean()
    out = betas.copy()
    blank = ~valid
    out.loc[blank] = means.reindex(b[blank]).to_numpy()
    return out


def holdings_exposure(weights: pd.Series, betas: pd.DataFrame, buckets: pd.Series) -> pd.Series:
    """Exposure per factor of 1 side (kickoff 5.8; instructions/05, Section C): sum of w_i beta_i
    over the positions of `weights` (priced, mapped, by ticker) that have a beta, own or the
    bucket fallback among the positions of this side, with their weights renormalised to 1."""
    b = fallback_betas(betas.reindex(weights.index), buckets.reindex(weights.index))
    has = b.notna().all(axis=1)
    w = weights[has] / weights[has].sum()
    return b[has].T @ w
