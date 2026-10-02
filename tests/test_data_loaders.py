from pathlib import Path

import pandas as pd

from attrib.factors import load_french, read_french_csv
from attrib.returns import load_prices

DATA = Path(__file__).resolve().parents[1] / "data"


def test_french_loader_decimals():
    raw = read_french_csv(DATA / "raw" / "french" / "ff5_monthly.csv").join(
        read_french_csv(DATA / "raw" / "french" / "mom_monthly.csv"), how="inner"
    )
    pct = raw.loc[202003]
    dec = load_french(DATA).loc[pd.Period("2020-03", freq="M")]
    print("raw file, percent:", pct.to_dict(), sep="\n")
    print("loader, decimal:", dec.to_dict(), sep="\n")
    pairs = {"mkt": "Mkt-RF", "smb": "SMB", "hml": "HML", "rmw": "RMW", "cma": "CMA", "umd": "Mom", "rf": "RF"}
    assert list(dec.index) == list(pairs)
    for col, name in pairs.items():
        assert abs(dec[col] * 100 - pct[name]) <= 1e-12, (col, dec[col], pct[name])


def test_price_index_sorted_unique():
    px = load_prices(DATA)
    assert px.index.name == "date"
    assert isinstance(px.index, pd.DatetimeIndex)
    assert px.index.is_monotonic_increasing
    assert px.index.is_unique
    assert list(px.columns) == sorted(px.columns)
    assert (px.dtypes == "float64").all()
