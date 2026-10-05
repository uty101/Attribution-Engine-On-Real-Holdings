"""Active share and ex-ante tracking error (kickoff Section 5.10; instructions/06, Section C).

Daily returns are simple returns, rows dates and columns `yf_ticker`s. A covariance is indexed by
ticker on both axes. Weights handed to the tracking-error functions are by ticker.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pc.cov import condition_cov, cov_lw_cc, window_daily

NEUTRAL = ("Unmapped", "Unpriced")  # Convention 4.6: the 2 buckets outside the FF12 industries
DAILY_TO_MONTHLY = 21  # kickoff 5.10: Sigma_m = 21 Sigma_d (config `risk.daily_to_monthly`)


def risk_weights(pos: pd.DataFrame, smap: pd.DataFrame) -> pd.Series:
    """Risk weights of 1 book (instructions/06, C; Convention 4.18): the priced, mapped rows of its
    POSITION_RETURNS, summed by `yf_ticker`, renormalised to 1. Indexed by ticker, sorted."""
    pm = pos[~pos["bucket"].isin(NEUTRAL)]
    if pm.empty:
        raise ValueError("a book has no priced, mapped position")
    tick = pm["sec_id"].map(smap.set_index("sec_id")["yf_ticker"])
    w = pm["weight"].astype("float64").groupby(tick.to_numpy()).sum().sort_index()
    w.index.name = "ticker"
    return w / w.sum()


def ticker_buckets(smap: pd.DataFrame, tickers) -> pd.Series:
    """The FF12 bucket of each ticker from SECURITY_MAP (instructions/06, C: Fill). Raises if a
    ticker is missing or has 2 buckets."""
    m = smap[smap["yf_ticker"].isin(list(tickers))]
    n = m.groupby("yf_ticker")["ff12"].nunique()
    if (n > 1).any():
        raise ValueError(f"tickers in 2 FF12 buckets: {sorted(n[n > 1].index)}")
    b = m.drop_duplicates("yf_ticker").set_index("yf_ticker")["ff12"].reindex(list(tickers))
    if b.isna().any():
        raise ValueError(f"tickers with no FF12 bucket: {sorted(b[b.isna()].index)}")
    return b


def fill_daily(returns_d: pd.DataFrame, buckets: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    """Kickoff 5.10 fill rule. A missing return of ticker i on day d becomes the equal-weight mean
    that day of the other tickers in i's bucket (`buckets`, by ticker) with a return; if there is
    none, the equal-weight mean of every ticker with a return that day. Means are taken over the
    unfilled returns. Returns the filled panel and the fill share per ticker (filled days / rows).
    Raises if a day has no return at all."""
    x = returns_d.to_numpy(dtype="float64")
    have = ~np.isnan(x)
    if not have.any(axis=1).all():
        raise ValueError(f"days with no return: {list(returns_d.index[~have.any(axis=1)])}")
    vals = np.where(have, x, 0.0)
    all_mean = vals.sum(axis=1) / have.sum(axis=1)
    b = buckets.reindex(returns_d.columns).to_numpy()
    out = x.copy()
    for bk in pd.unique(b):
        cols = np.flatnonzero(b == bk)
        n = have[:, cols].sum(axis=1)
        s = vals[:, cols].sum(axis=1)
        # a missing ticker has no return, so every ticker of its bucket with a return is an "other"
        fill = np.where(n > 0, s / np.maximum(n, 1), all_mean)
        sub = out[:, cols]
        miss = ~have[:, cols]
        sub[miss] = np.broadcast_to(fill[:, None], sub.shape)[miss]
        out[:, cols] = sub
    filled = pd.DataFrame(out, index=returns_d.index, columns=returns_d.columns)
    share = pd.Series((~have).sum(axis=0) / len(x), index=returns_d.columns, name="fill_share")
    return filled, share


def active_cov(returns_d: pd.DataFrame, q, months: int, max_cond: float) -> tuple[pd.DataFrame, dict]:
    """Monthly covariance at holdings date h (kickoff 5.10; instructions/06, C). `returns_d` is the
    filled daily panel; `q` is q_start(h). Rows from `window_daily(returns_d, q, months)`,
    Sigma_d = `cov_lw_cc(X, ddof=0)`, conditioned by `condition_cov(Sigma_d, max_cond)`, then
    Sigma_m = 21 Sigma_d. The dict carries delta_lw, ridge, ridged (ridge > 0), cond_before,
    cond_after and n_days."""
    X = window_daily(returns_d, pd.Timestamp(q), months)
    if X.isna().any().any():
        raise ValueError("active_cov needs a filled panel (fill_daily)")
    S, delta = cov_lw_cc(X, ddof=0)
    S, log = condition_cov(S, max_cond)
    info = {
        "delta_lw": float(delta),
        "ridge": float(log["ridge"]),
        "ridged": bool(log["ridge"] > 0),
        "cond_before": float(log["cond_before"]),
        "cond_after": float(log["cond_after"]),
        "n_days": len(X),
    }
    return S * DAILY_TO_MONTHLY, info
