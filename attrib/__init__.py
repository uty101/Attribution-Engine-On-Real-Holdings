"""Performance and risk attribution on real 13F holdings.

`attribute` is the one-function interface (kickoff 6.1; instructions/07, Section C.3): a holdings
file and a benchmark holdings file in, a 4-page PDF report out, from local data only.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from pc.cov import window_daily
from pc.stats import stationary_bootstrap_indices

from attrib.bootstrap import bootstrap_mean
from attrib.brinson import EFFECTS, brinson_fachler
from attrib.config import load_config
from attrib.edgar import sec_ids
from attrib.factors import factor_contrib_by_year, load_french, returns_based, rolling_betas
from attrib.linking import carino, menchero
from attrib.mapping import SECURITY_MAP, security_map_from_dir
from attrib.reconstruction import GATE
from attrib.report import build_report, chart_1_png, chart_2_png, chart_3_png
from attrib.returns import (
    BOOK_QUARTERLY, BUCKETS_ORDER, NEUTRAL, apply_return_overrides, book_monthly, book_quarter, book_return,
    bucket_table, daily_returns, quarter_calendar, return_overrides_with_t,
)
from attrib.risk import (
    MONTHS_PER_YEAR, active_cov, active_share, fill_daily, issuer_weights, risk_weights, te_decomposition,
    ticker_buckets,
)

ROOT = Path(__file__).resolve().parents[1]
HOLDINGS = ["entity", "period_date", "cusip", "isin", "sec_id", "name", "value_usd", "shares"]  # amendment 8
PULL_COMMAND = "python scripts/pull_data.py --holdings {h} --benchmark {b}"


def read_holdings(path: str | Path) -> pd.DataFrame:
    """A HOLDINGS CSV (amendment 8; instructions/07, C.3). `entity`, `isin` and `sec_id` may be
    absent; a blank or absent `sec_id` is the CUSIP when it is a valid CUSIP, else the ISIN when it
    is a valid ISIN (amendment 8). Rows with the same period_date and sec_id are summed (Convention
    4.3). Raises on a missing column or a row with no sec_id. Returns HOLDINGS without `entity`."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    need = ["period_date", "cusip", "name", "value_usd", "shares"]
    lack = [c for c in need if c not in df.columns]
    if lack:
        raise ValueError(f"{path}: missing columns {lack}; a holdings file needs {need}")
    for c in ("isin", "sec_id"):
        if c not in df.columns:
            df[c] = ""
    for c in ("cusip", "isin", "sec_id"):
        df[c] = df[c].str.strip().str.upper()
    df["sec_id"] = df["sec_id"].where(df["sec_id"] != "", sec_ids(df["cusip"], df["isin"]))
    bad = df[df["sec_id"] == ""]
    if not bad.empty:
        raise ValueError(f"{path}: rows with no valid CUSIP or ISIN:\n{bad.to_string()}")
    df = df.astype({"value_usd": "float64", "shares": "float64"})
    g = df.groupby(["period_date", "sec_id"], sort=True)
    out = g.agg(cusip=("cusip", "first"), isin=("isin", "first"), name=("name", "first"),
                value_usd=("value_usd", "sum"), shares=("shares", "sum")).reset_index()
    return out[HOLDINGS[1:]]


def quarter_ends(start, end) -> list[date]:
    """Every calendar quarter end from `start` to `end`, both included; both must be quarter ends."""
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    for d in (s, e):
        if d != d + pd.offsets.QuarterEnd(0):
            raise ValueError(f"{d.date()} is not a calendar quarter end")
    if e < s:
        raise ValueError(f"end {e.date()} is before start {s.date()}")
    return [d.date() for d in pd.date_range(s, e, freq="QE")]


def load_security_map(data_dir: str | Path) -> pd.DataFrame:
    """SECURITY_MAP from `data_dir/raw` and `data_dir/manual`, with the rows of
    `data_dir/extra/security_map_extra.csv` (written by `scripts/pull_data.py --holdings`) merged in
    when it exists; an extra row wins on a duplicate sec_id (instructions/07, C.3)."""
    d = Path(data_dir)
    smap = security_map_from_dir(d)
    extra = d / "extra" / "security_map_extra.csv"
    if extra.exists():
        x = pd.read_csv(extra, dtype=str, keep_default_na=False)[SECURITY_MAP]
        for c in ("cik", "sic"):
            x[c] = pd.to_numeric(x[c].replace("", None)).astype("Int64")
        smap = pd.concat([smap[~smap["sec_id"].isin(x["sec_id"])], x], ignore_index=True)
        smap = smap.sort_values("sec_id", kind="mergesort").reset_index(drop=True)
    return smap


def load_prices_dir(data_dir: str | Path) -> pd.DataFrame:
    """Adjusted closes, dates x yf_tickers: `raw/prices/adjclose.parquet`, or `raw/prices/adjclose.csv`
    (date column first) when there is no parquet file, then the columns of
    `extra/adjclose_extra.parquet` when it exists, on the dates of the first file; an extra column
    wins on a duplicate ticker (instructions/07, C.3)."""
    d = Path(data_dir)
    pq = d / "raw" / "prices" / "adjclose.parquet"
    if pq.exists():
        prices = pd.read_parquet(pq)
    else:
        prices = pd.read_csv(d / "raw" / "prices" / "adjclose.csv", index_col="date", parse_dates=["date"])
    extra = d / "extra" / "adjclose_extra.parquet"
    if extra.exists():
        x = pd.read_parquet(extra)
        x.index = pd.DatetimeIndex(x.index).astype(prices.index.dtype)
        prices = prices.drop(columns=[c for c in x.columns if c in prices.columns]).join(x, how="left")
        prices = prices[sorted(prices.columns)]
    prices.index.name = "date"
    return prices.astype("float64")


def _missing_dates(books: dict[str, pd.DataFrame], dates: list[date]) -> list[str]:
    out = []
    for path, b in books.items():
        lack = sorted({str(d) for d in dates} - set(b["period_date"]))
        if lack:
            out.append(f"{path} has no rows for {lack}")
    return out


def attribute(holdings_path, benchmark_path, start, end, data_dir="data", out_dir="outputs/reports",
              fund_name=None) -> Path:
    """Attribute a holdings file against a benchmark holdings file and write the report
    (kickoff 6.1; instructions/07, Section C.3). Local data only; no network.

    `start` and `end` are holdings dates (calendar quarter ends); every quarter end between them
    must be in both files. Return quarter t runs from q(h_t) to q(next quarter end), q(h) the last
    date <= h in the price index. Every sec_id must be in SECURITY_MAP, else a ValueError lists
    them all and names the pull command. No NAV series is supplied, so the reconstruction check is
    skipped and nothing is excluded (D-28). Writes `{out_dir}/{fund_name or holdings file stem}.pdf`
    and returns its path.
    """
    cfg = load_config(ROOT / "config.toml")
    data_dir = Path(data_dir)
    fund = fund_name or Path(holdings_path).stem
    bench = Path(benchmark_path).stem
    if fund == bench:
        raise ValueError(f"the fund and the benchmark are both named {fund!r}; pass fund_name")
    dates = quarter_ends(start, end)
    raw = {str(holdings_path): read_holdings(holdings_path), str(benchmark_path): read_holdings(benchmark_path)}
    lack = _missing_dates(raw, dates)
    if lack:
        raise ValueError("holdings dates missing between start and end:\n" + "\n".join(lack))
    keep = {str(d) for d in dates}
    hP, hB = (b[b["period_date"].isin(keep)] for b in raw.values())

    smap = load_security_map(data_dir)
    unknown = sorted((set(hP["sec_id"]) | set(hB["sec_id"])) - set(smap["sec_id"]))
    if unknown:
        raise ValueError(
            f"{len(unknown)} sec_ids are not in the data directory {data_dir}: {unknown}. Map them and pull "
            f"their prices with: {PULL_COMMAND.format(h=holdings_path, b=benchmark_path)}"
        )
    prices = load_prices_dir(data_dir)
    books = {fund: hP.assign(entity=fund), bench: hB.assign(entity=bench)}
    res = _run(cfg, data_dir, fund, bench, books, smap, prices, dates)
    return build_report(fund, res, Path(out_dir) / f"{fund}.pdf")


def _run(cfg, data_dir: Path, fund: str, bench: str, books: dict[str, pd.DataFrame], smap: pd.DataFrame,
         prices: pd.DataFrame, dates: list[date]) -> dict:
    """The results of Sections 3 to 6 for 1 fund and its benchmark, as `build_report` takes them
    (instructions/07, C.2). The same steps as `scripts/run_all.py` sections 3 to 6, with no NAV."""
    cal = quarter_calendar(prices.index, dates)
    ov = pd.read_csv(data_dir / "manual" / "overrides.csv", dtype=str, keep_default_na=False)
    ov = ov[(ov["kind"] != "quarter_return") | ov["period_date"].isin({str(d) for d in dates})]
    ov = return_overrides_with_t(ov, cal)

    # Section 3: book returns (Conventions 4.5 to 4.12), overrides between book_quarter and bucket_table (D-16)
    pos, monthly = [], []
    for eid, book in books.items():
        for _, q in cal.iterrows():
            b = book[book["period_date"] == str(q["holdings_date"])].assign(t=q["t"])
            pos.append(book_quarter(b, smap, prices, q["q_start"], q["q_end"]))
            m = book_monthly(b, smap, prices, q["q_start"], q["q_end"])
            monthly.append(pd.DataFrame({"entity": eid, "month": m.index.astype(str), "ret": m.to_numpy()}))
    pos = apply_return_overrides(pd.concat(pos, ignore_index=True), ov)
    buckets = bucket_table(pos)
    monthly = pd.concat(monthly, ignore_index=True)
    bq = []
    for (eid, t), g in pos.groupby(["entity", "t"], sort=False):
        w = g.groupby("bucket")["weight"].sum()
        bq.append([eid, t, book_return(buckets[(buckets["entity"] == eid) & (buckets["t"] == t)]),
                   w.get("Unmapped", 0.0), w.get("Unpriced", 0.0), g.loc[g["delisted_in_quarter"], "weight"].sum()])
    book_q = pd.DataFrame(bq, columns=BOOK_QUARTERLY)
    rP = book_q[book_q["entity"] == fund].set_index("t")["book_return"]
    rB = book_q[book_q["entity"] == bench].set_index("t")["book_return"]

    # Section 4: Brinson-Fachler per quarter, Carino and Menchero linking, the bootstrap of the totals
    def side(eid: str, t: int) -> tuple[pd.Series, pd.Series]:
        g = buckets[(buckets["entity"] == eid) & (buckets["t"] == t)].set_index("bucket").reindex(BUCKETS_ORDER)
        return g["weight"], g["r"]

    eff = []
    for t in cal["t"]:
        ef = brinson_fachler(*side(fund, t), *side(bench, t))
        eff.append(ef.reset_index().assign(t=t))
    eff = pd.concat(eff, ignore_index=True)[["t", "bucket", *EFFECTS]]
    linked = []
    for method, f in (("carino", carino), ("menchero", menchero)):
        lk = f(rP, rB, eff, cfg.linking.zero_tol)
        lk = pd.concat([lk, pd.DataFrame([["Total", *lk[EFFECTS].sum()]], columns=lk.columns)], ignore_index=True)
        lk["total"] = lk[EFFECTS].sum(axis=1)
        linked.append(lk.assign(fund=fund, method=method)[["fund", "method", "bucket", *EFFECTS, "total"]])
    linked = pd.concat(linked, ignore_index=True)
    b = cfg.bootstrap
    tot = eff.groupby("t")[EFFECTS].sum()
    idx = stationary_bootstrap_indices(len(tot), b.mean_block, b.reps, cfg.run.bootstrap_seed)
    boot = pd.DataFrame(
        [[fund, s, *bootstrap_mean(tot[s].to_numpy(), b.mean_block, b.reps, cfg.run.bootstrap_seed, b.lo, b.hi,
                                   idx=idx)] for s in EFFECTS],
        columns=["fund", "series", "mean", "p05", "p95"],
    )

    # Section 5: returns-based factors on the fund book, over the months with both a book return and French data;
    # not run below `report.min_factor_months` monthly returns (instructions/08, A answer 2)
    names = list(cfg.factors.names)
    ff = load_french(data_dir)
    first = pd.Period(dates[0], freq="M") + 1
    last = min(pd.Period(cal["q_end"].iloc[-1], freq="M"), ff.index.max())
    months = pd.period_range(first, last, freq="M", name="month")
    ret = monthly[monthly["entity"] == fund].set_index("month")["ret"]
    ret.index = pd.PeriodIndex(ret.index, freq="M", name="month")
    ret = ret[ret.index.isin(months)]
    excess = ret - ff["rf"].reindex(ret.index)  # Convention 4.15
    if len(excess) < cfg.report.min_factor_months:
        factor_fit, factor_by_year, chart2 = pd.DataFrame(), pd.DataFrame(), None
    else:
        fac = ff.loc[months, names]
        fit = returns_based(excess, fac, cfg.factors.hac_maxlags)
        sid = f"{fund}_book"
        factor_fit = pd.DataFrame({c: fit[c] for c in ("value", "se_hac", "t_hac")}).rename_axis("coef").reset_index()
        factor_fit = factor_fit.assign(series_id=sid, series_kind="book", r2=fit["r2"],
                                       resid_vol_ann=fit["resid_vol_ann"], n_months=fit["n_months"])
        factor_by_year = factor_contrib_by_year(excess, fac, fit).assign(series_id=sid)
        rb = rolling_betas(excess, fac, cfg.factors.rolling_window)
        chart2 = chart_2_png(fund, rb, names, cfg.factors.rolling_window, cfg.report.dpi)

    # Section 6: active share and ex-ante TE at each holdings date, realised TE over every book month
    rk = cfg.risk
    rets = daily_returns(prices)
    # issuer keys from SECURITY_MAP as text, as run_all reads security_map.csv: a blank CIK is ""
    smap_str = smap.astype(str).replace({"<NA>": ""})
    rq, last_dec = [], None
    for t, h, qs in zip(cal["t"], cal["holdings_date"], cal["q_start"]):
        posP, posB = (pos[(pos["entity"] == e) & (pos["t"] == t)] for e in (fund, bench))
        AS = active_share(issuer_weights(posP, smap_str), issuer_weights(posB, smap_str))
        wP, wB = risk_weights(posP, smap), risk_weights(posB, smap)
        union = sorted(set(wP.index) | set(wB.index))
        tb = ticker_buckets(smap, union)
        filled, share = fill_daily(window_daily(rets[union], qs, rk.cov_months), tb)
        S, info = active_cov(filled, qs, rk.cov_months, rk.max_cond)
        a = wP.reindex(union, fill_value=0.0) - wB.reindex(union, fill_value=0.0)
        dec = te_decomposition(a, S).assign(bucket=tb.to_numpy())
        te = float(np.sqrt(MONTHS_PER_YEAR * a.to_numpy() @ S.to_numpy() @ a.to_numpy()))
        excl = [float(p.loc[p["bucket"].isin(NEUTRAL), "weight"].sum()) for p in (posP, posB)]
        rq.append([fund, str(h), AS, te, *excl, len(union), float(share.max()), info["delta_lw"], info["ridged"]])
        last_dec = (dec, te, str(h))
    risk_q = pd.DataFrame(rq, columns=["fund", "holdings_date", "active_share", "te_exante", "excluded_weight_fund",
                                       "excluded_weight_bench", "n_names", "max_fill_share", "delta_lw", "ridged"])
    act = (monthly[monthly["entity"] == fund].set_index("month")["ret"]
           - monthly[monthly["entity"] == bench].set_index("month")["ret"]).dropna()
    te_real = pd.DataFrame([[fund, float(act.std(ddof=1) * np.sqrt(rk.months_per_year)),
                             float(risk_q["te_exante"].mean()), len(act)]],
                           columns=["fund", "te_realised", "te_exante_mean", "n_months"])

    fp = book_q[book_q["entity"] == fund]
    cov = pd.DataFrame({
        "entity": fund,
        "period_date": [str(h) for h in cal["holdings_date"]],
        "n_rows_kept": pos[pos["entity"] == fund].groupby("t").size().reindex(cal["t"]).to_numpy(),
        "unmapped_weight": fp["unmapped_weight"].to_numpy(),
        "unpriced_weight": fp["unpriced_weight"].to_numpy(),
    })
    dec, te, h = last_dec
    return {
        "linked": linked, "factor_by_year": factor_by_year, "factor_fit": factor_fit, "risk_quarterly": risk_q,
        "te_realised": te_real, "gate": pd.DataFrame(columns=GATE), "bootstrap": boot,
        "book_quarterly": book_q, "coverage": cov, "fund_name": fund, "benchmark_name": bench,
        "chart1": chart_1_png(fund, bench, rP, rB, eff, cal.set_index("t")["q_end"], cfg.linking.zero_tol,
                              cfg.report.dpi),
        "chart2": chart2,
        "chart3": chart_3_png(fund, bench, dec, te, h, rk.top_n_positions, cfg.report.dpi),
        "min_factor_months": cfg.report.min_factor_months,
    }
