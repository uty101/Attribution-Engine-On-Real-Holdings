"""Prices, the quarter calendar and stock returns (kickoff Section 5.3; D-13)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd


def load_prices(data_dir: str | Path) -> pd.DataFrame:
    """data/raw/prices/adjclose.parquet: adjusted closes, index `date`, 1 column per yf_ticker."""
    return pd.read_parquet(Path(data_dir) / "raw" / "prices" / "adjclose.parquet")


NAV_MONTHLY = ["entity", "month", "ret", "source"]


def nport_month_series(
    months: list[pd.Period],
    class_pct: pd.Series,
    etf_class_pct: pd.Series,
    etf_month_ret: pd.Series,
    etf_first_date: date,
) -> pd.DataFrame:
    """A fund's monthly NAV return chosen month by month (instructions/02b, step 2.1b):

    1. `nport_class`: the N-PORT B.5 return of the fund's NAV class (`class_pct`, percent, by `YYYY-MM`);
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
            rows.append([key, class_pct[key] / 100, "nport_class"])  # B.5 returns are in percent
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
