"""Prices, the quarter calendar and stock returns (kickoff Section 5.3; D-13)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd


def load_prices(data_dir: str | Path) -> pd.DataFrame:
    """data/raw/prices/adjclose.parquet: adjusted closes, index `date`, 1 column per yf_ticker."""
    return pd.read_parquet(Path(data_dir) / "raw" / "prices" / "adjclose.parquet")


def load_nav(data_dir: str | Path) -> pd.DataFrame:
    """data/raw/prices/nav_adjclose.csv: adjusted closes of the NAV and ETF tickers, index `date`."""
    df = pd.read_csv(Path(data_dir) / "raw" / "prices" / "nav_adjclose.csv", index_col="date", parse_dates=["date"])
    return df.astype("float64")
