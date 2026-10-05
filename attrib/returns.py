"""Prices, the quarter calendar and stock returns (kickoff Section 5.3; D-13)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd


def load_prices(data_dir: str | Path) -> pd.DataFrame:
    """data/raw/prices/adjclose.parquet: adjusted closes, index `date`, 1 column per yf_ticker."""
    return pd.read_parquet(Path(data_dir) / "raw" / "prices" / "adjclose.parquet")


NAV_MONTHLY = ["entity", "month", "ret", "source"]


def month_end_closes(prices: pd.DataFrame) -> pd.DataFrame:
    """Convention 4.13: the last available adjusted close in each calendar month, per column,
    indexed by `pd.Period(freq="M")`."""
    return prices.groupby(prices.index.to_period("M")).last()


def monthly_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Calendar-month returns from month-end closes (Convention 4.13; instructions/02, C 2.4). The
    first month of each column's series has no return, nor has a month after one with no close."""
    return month_end_closes(prices).pct_change(fill_method=None)


def nport_month_series(
    months: list[pd.Period],
    class_pct: pd.Series,
    etf_class_pct: pd.Series,
    etf_month_ret: pd.Series,
    etf_first_date: date,
) -> pd.DataFrame:
    """A fund's monthly NAV return chosen month by month (instructions/02b, step 2.1b):

    1. `nport_b5`: the N-PORT B.5 return of the fund's NAV class (`class_pct`, percent, by `YYYY-MM`);
    2. `nport_etf_class`: else the B.5 return of an ETF class in the same series (`etf_class_pct`);
    3. `yfinance_etf`: else the ETF successor's yfinance month return (`etf_month_ret`, decimal, by
       `pd.Period`), for months whose first day is after `etf_first_date`;
    4. `missing`: else no return.

    Returns columns month (`YYYY-MM`), ret (decimal), source.
    """
    rows = []
    for m in months:
        key = str(m)
        if key in class_pct.index and pd.notna(class_pct[key]):
            rows.append([key, class_pct[key] / 100, "nport_b5"])  # B.5 returns are in percent
        elif key in etf_class_pct.index and pd.notna(etf_class_pct[key]):
            rows.append([key, etf_class_pct[key] / 100, "nport_etf_class"])
        elif m.start_time.date() > etf_first_date and m in etf_month_ret.index and pd.notna(etf_month_ret[m]):
            rows.append([key, float(etf_month_ret[m]), "yfinance_etf"])
        else:
            rows.append([key, None, "missing"])
    return pd.DataFrame(rows, columns=["month", "ret", "source"]).astype({"ret": "float64"})


def load_nav(data_dir: str | Path) -> pd.DataFrame:
    """data/raw/prices/nav_adjclose.csv: adjusted closes of the NAV and ETF tickers, index `date`."""
    df = pd.read_csv(Path(data_dir) / "raw" / "prices" / "nav_adjclose.csv", index_col="date", parse_dates=["date"])
    return df.astype("float64")


QUARTERS = ["t", "holdings_date", "q_start", "q_end"]


def _next_quarter_end(d: date) -> date:
    """The next calendar quarter end after the quarter end `d`."""
    return (pd.Timestamp(d) + pd.offsets.QuarterEnd(1)).date()


def q(price_index: pd.DatetimeIndex, d: date) -> pd.Timestamp:
    """Kickoff 3.3: the last date <= d in `price_index` (the IVV price index)."""
    idx = price_index[price_index <= pd.Timestamp(d)]
    if idx.empty:
        raise ValueError(f"no price date on or before {d}")
    return idx.max()


def quarter_calendar(price_index: pd.DatetimeIndex, dates: list[date]) -> pd.DataFrame:
    """QUARTERS: t from 1, holdings_date h_t, q_start = q(h_t), q_end = q(next calendar quarter end)
    (kickoff 3.3; instructions/02, C 2.4)."""
    idx = pd.DatetimeIndex(price_index).sort_values()
    rows = [[t, d, q(idx, d), q(idx, _next_quarter_end(d))] for t, d in enumerate(sorted(dates), start=1)]
    return pd.DataFrame(rows, columns=QUARTERS)


def daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Daily simple returns per column, each from the previous available close of that column.
    A date with no close has no return; the first close of each column has none."""
    out = {c: prices[c].dropna().pct_change() for c in prices.columns}
    return pd.DataFrame(out, index=prices.index)[list(prices.columns)]


# Convention 4.6: the 14 buckets, the 12 FF12 industries in French's order, then Unmapped and Unpriced
BUCKETS_ORDER = [
    "NoDur", "Durbl", "Manuf", "Enrgy", "Chems", "BusEq", "Telcm", "Utils", "Shops", "Hlth", "Money", "Other",
    "Unmapped", "Unpriced",
]
# Kickoff 6.2 with `sec_id` after `cusip`: ISIN-only rows have no CUSIP (amendment 8)
POSITION_RETURNS = [
    "entity", "t", "cusip", "sec_id", "issuer6", "ticker", "bucket", "weight", "r", "delisted_in_quarter",
    "last_price_date",
]
BUCKETS = ["entity", "t", "bucket", "weight", "r"]
BOOK_QUARTERLY = ["entity", "t", "book_return", "unmapped_weight", "unpriced_weight", "delisted_weight"]
BOOK_MONTHLY = ["entity", "month", "ret"]
NEUTRAL = ("Unmapped", "Unpriced")


def _positions(book: pd.DataFrame, smap: pd.DataFrame, prices: pd.DataFrame, q_start) -> pd.DataFrame:
    """The book's rows with weight (Convention 4.5), ticker, yf_ticker, `p0` the adjusted close on
    q_start, `priced`, and the bucket: Unmapped for `no_match`, Unpriced for a ticker with no close
    on q_start, else its FF12 industry (instructions/02, B)."""
    b = book.copy()
    v = b["value_usd"].astype("float64")
    b["weight"] = v / v.sum()
    m = smap.set_index("sec_id")[["ticker", "yf_ticker", "ff12", "map_status"]]
    b = b.join(m, on="sec_id")
    if b["map_status"].isna().any():
        raise ValueError(f"sec_ids not in SECURITY_MAP: {sorted(b.loc[b['map_status'].isna(), 'sec_id'])}")
    q_start = pd.Timestamp(q_start)
    row = prices.loc[q_start] if q_start in prices.index else pd.Series(dtype="float64")
    b["p0"] = [row.get(t, float("nan")) if t else float("nan") for t in b["yf_ticker"].fillna("")]
    mapped = b["map_status"] != "no_match"
    b["priced"] = mapped & b["p0"].notna()
    b["bucket"] = b["ff12"].where(b["priced"], "Unpriced").where(mapped, "Unmapped")
    return b


def _neutral(pos: pd.DataFrame) -> pd.DataFrame:
    """Convention 4.9: Unmapped and Unpriced rows earn the priced, mapped return of their book."""
    pm = ~pos["bucket"].isin(NEUTRAL)
    if not pm.any():
        raise ValueError("a book has no priced, mapped position, so its neutral return is undefined")
    w = pos.loc[pm, "weight"]
    pos = pos.copy()
    pos.loc[~pm, "r"] = float((w * pos.loc[pm, "r"]).sum() / w.sum())
    return pos


def book_quarter(book: pd.DataFrame, smap: pd.DataFrame, prices: pd.DataFrame, q_start, q_end) -> pd.DataFrame:
    """POSITION_RETURNS for 1 book over the return quarter from q_start to q_end (Conventions 4.5 to 4.9).

    `book` is the HOLDINGS rows of 1 entity and 1 period; `t` is copied from a `t` column of `book`
    when it has one, else left blank. A priced, mapped position earns P(end) / P(q_start) - 1, with
    P(end) the last close on or before q_end; `delisted_in_quarter` is True when that close is
    before q_end (Convention 4.8). Unmapped and Unpriced rows earn the book's priced, mapped return
    (Convention 4.9) and have no last_price_date.
    """
    b = _positions(book, smap, prices, q_start)
    q_start, q_end = pd.Timestamp(q_start), pd.Timestamp(q_end)
    cols = sorted(set(b.loc[b["priced"], "yf_ticker"]))
    window = prices.loc[(prices.index >= q_start) & (prices.index <= q_end), cols]
    arr = window.to_numpy()
    last_i = len(arr) - 1 - np.argmax(~np.isnan(arr[::-1]), axis=0)  # each column's last close (p0 exists)
    p_end = pd.Series(arr[last_i, np.arange(arr.shape[1])], index=cols)
    last_date = pd.Series(window.index[last_i], index=cols)
    ok = b["priced"]
    tick = b["yf_ticker"].where(ok)
    b["r"] = (tick.map(p_end) / b["p0"] - 1).where(ok)
    last = tick.map(last_date)
    b["last_price_date"] = last.dt.strftime("%Y-%m-%d").where(ok, "")
    b["delisted_in_quarter"] = (last < q_end).where(ok, False).astype(bool)
    b = _neutral(b)
    b["cusip"] = b["cusip"].fillna("").astype(str)
    b["issuer6"] = b["cusip"].str[:6]
    b["t"] = book["t"].to_numpy() if "t" in book else pd.NA
    return b[POSITION_RETURNS].reset_index(drop=True)


def return_overrides_with_t(overrides: pd.DataFrame, cal: pd.DataFrame) -> pd.DataFrame:
    """The `quarter_return` rows of overrides.csv with `t` added: `period_date` is the holdings
    date h_t of the return quarter (QUARTERS)."""
    ov = overrides.fillna("").astype(str)
    ov = ov[ov["kind"] == "quarter_return"].copy()
    t_of = {str(h): t for t, h in zip(cal["t"], cal["holdings_date"])}
    bad = sorted(set(ov["period_date"]) - set(t_of))
    if bad:
        raise ValueError(f"quarter_return period_date not a holdings date: {bad}")
    ov["t"] = [t_of[p] for p in ov["period_date"]]
    return ov


def apply_return_overrides(pos: pd.DataFrame, overrides: pd.DataFrame) -> pd.DataFrame:
    """D-16 (instructions/01, B OPEN-16): applied after `book_quarter`, before `bucket_table`.

    Every `quarter_return` row of `overrides` (with `t`, from `return_overrides_with_t`) sets `r`
    to `value` on the POSITION_RETURNS rows with its sec_id and t, in every entity. The Unmapped
    and Unpriced rows of a changed book then take the book's new priced, mapped return
    (Convention 4.9). An override naming an Unmapped or Unpriced row raises: that row has no
    return of its own to replace.
    """
    ov = overrides[overrides["kind"] == "quarter_return"]
    if ov.empty:
        return pos
    out = pos.copy()
    changed = set()
    for sid, t, value in zip(ov["sec_id"], ov["t"], ov["value"]):
        hit = (out["sec_id"] == sid) & (out["t"] == int(t))
        if out.loc[hit, "bucket"].isin(NEUTRAL).any():
            raise ValueError(f"quarter_return override for {sid} t={t} names an Unmapped or Unpriced row")
        out.loc[hit, "r"] = float(value)
        changed |= set(zip(out.loc[hit, "entity"], out.loc[hit, "t"]))
    parts = [_neutral(g) if k in changed else g for k, g in out.groupby(["entity", "t"], sort=False)]
    return pd.concat(parts).loc[out.index, POSITION_RETURNS]


def bucket_table(pos: pd.DataFrame) -> pd.DataFrame:
    """BUCKETS: 14 rows per (entity, t) in Convention 4.6 order. weight = the sum of position
    weights; r = their weighted mean return (Convention 4.10), blank for a bucket with 0 weight."""
    rows = []
    for (eid, t), g in pos.groupby(["entity", "t"], sort=True):
        by = g.assign(wr=g["weight"] * g["r"]).groupby("bucket")[["weight", "wr"]].sum()
        for bk in BUCKETS_ORDER:
            w = float(by.at[bk, "weight"]) if bk in by.index else 0.0
            rows.append([eid, t, bk, w, float(by.at[bk, "wr"]) / w if w > 0 else float("nan")])
    return pd.DataFrame(rows, columns=BUCKETS)


def book_return(buckets: pd.DataFrame) -> float:
    """r = the sum of w_s r_s over the buckets of 1 (entity, t) with positive weight (Convention 4.9)."""
    b = buckets[buckets["weight"] > 0]
    return float((b["weight"] * b["r"]).sum())


def month_end_dates(index: pd.DatetimeIndex, q_start, q_end) -> list[pd.Timestamp]:
    """Convention 4.12: q_start, then the last date of `index` in each calendar month after q_start
    up to q_end; the last of them must be q_end."""
    q_start, q_end = pd.Timestamp(q_start), pd.Timestamp(q_end)
    idx = pd.DatetimeIndex(index)
    idx = idx[(idx > q_start) & (idx <= q_end)]
    ends = pd.Series(idx, index=idx).groupby(idx.to_period("M")).max()
    out = [q_start, *ends.tolist()]
    if out[-1] != q_end:
        raise ValueError(f"q_end {q_end.date()} is not the last month-end date {out[-1].date()}")
    return out


def book_monthly(book: pd.DataFrame, smap: pd.DataFrame, prices: pd.DataFrame, q_start, q_end) -> pd.Series:
    """Monthly book returns within 1 quarter (Convention 4.12), indexed by `pd.Period(freq="M")`.

    V_d = sum_i w_i P_i(d) / P_i(q_start) over priced, mapped positions, divided by their weight
    sum, with P_i(d) the last close on or before d, so a delisted name is flat after its last
    close. Each month's return is the change in V between month-end dates of the prices index,
    q_start standing in for the first month's start.
    """
    b = _positions(book, smap, prices, q_start)
    b = b[b["priced"]]
    q_start, q_end = pd.Timestamp(q_start), pd.Timestamp(q_end)
    window = prices.loc[(prices.index >= q_start) & (prices.index <= q_end), sorted(set(b["yf_ticker"]))].ffill()
    dates = month_end_dates(window.index, q_start, q_end)
    rel = window.loc[dates, b["yf_ticker"]].to_numpy() / b["p0"].to_numpy()
    w = b["weight"].to_numpy()
    v = rel @ w / w.sum()
    months = pd.PeriodIndex([d.to_period("M") for d in dates[1:]], name="month")
    return pd.Series(v[1:] / v[:-1] - 1, index=months, name="ret")
