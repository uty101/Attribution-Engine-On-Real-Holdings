from datetime import date
from pathlib import Path

import pandas as pd

from attrib.config import load_config
from attrib.edgar import holdings_dates
from attrib.returns import load_nav, monthly_returns, quarter_calendar

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")


def _calendar() -> pd.DataFrame:
    ivv = load_nav(ROOT / "data")[CFG.entities["ivv"].etf_ticker].dropna().index
    return quarter_calendar(ivv, holdings_dates(CFG))


def test_quarters_has_28_rows():
    cal = _calendar()
    print(cal.to_string())
    assert len(cal) == 28
    assert cal["t"].tolist() == list(range(1, 29))
    assert cal["holdings_date"].iloc[0] == date(2019, 9, 30)
    assert cal["holdings_date"].iloc[-1] == date(2026, 6, 30)
    assert cal["q_end"].iloc[-1] <= pd.Timestamp("2026-09-30")
    assert cal["q_end"].iloc[-1] > pd.Timestamp("2026-09-23")


def test_q_start_next_equals_q_end():
    cal = _calendar()
    assert (cal["q_start"].iloc[1:].to_numpy() == cal["q_end"].iloc[:-1].to_numpy()).all()


def test_month_end_uses_calendar_periods():
    # instructions/02, C 2.4: April's last trading day in this series is the 28th, so April's close
    # is the 28th's, not a value from May.
    idx = pd.DatetimeIndex(["2026-03-31", "2026-04-27", "2026-04-28", "2026-05-01", "2026-05-29"], name="date")
    px = pd.DataFrame({"X": [100.0, 104.0, 110.0, 200.0, 220.0]}, index=idx)
    r = monthly_returns(px)["X"]
    print(r.to_string())
    assert list(r.index) == [pd.Period(m, freq="M") for m in ("2026-03", "2026-04", "2026-05")]
    assert pd.isna(r.iloc[0])
    assert r[pd.Period("2026-04", freq="M")] == 110.0 / 100.0 - 1
    assert r[pd.Period("2026-05", freq="M")] == 220.0 / 110.0 - 1
