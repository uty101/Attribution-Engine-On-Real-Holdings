"""Prices, the quarter calendar and stock returns (kickoff Section 5.3; D-13)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

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
