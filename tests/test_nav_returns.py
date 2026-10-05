from datetime import date

import pandas as pd

from attrib.edgar import NPORT_RETURNS, latest_monthly_returns, parse_nport
from attrib.returns import nport_month_series

NS = "http://www.sec.gov/edgar/nport"


def _xml(period: str, returns: str) -> bytes:
    return (
        f'<edgarSubmission xmlns="{NS}"><headerData><filerInfo><seriesClassInfo><seriesId>S000000009</seriesId>'
        f"<classId>C000000001</classId><classId>C000000002</classId></seriesClassInfo></filerInfo></headerData>"
        f"<formData><genInfo><seriesId>S000000009</seriesId><repPdDate>{period}</repPdDate></genInfo>"
        f"<returnInfo><monthlyTotReturns>{returns}</monthlyTotReturns></returnInfo>"
        f"<invstOrSecs></invstOrSecs></formData></edgarSubmission>"
    ).encode()


def test_parse_monthly_returns():
    header, raw, rets = parse_nport(
        _xml(
            "2025-02-28",
            '<monthlyTotReturn classId="C000000001" rtn1="1.5" rtn2="-2.25" rtn3="3.0"/>'
            '<monthlyTotReturn classId="C000000002" rtn1="0.1" rtn2="0.2" rtn3="0.3"/>',
        )
    )
    print(rets.to_string())
    assert header == {"seriesId": "S000000009", "repPdDate": "2025-02-28"}
    assert raw.empty
    assert rets.attrs["class_ids"] == ["C000000001", "C000000002"]
    got = rets.set_index(["class_id", "month"])["rtn_pct"]
    # rtn3 is the month of repPdDate, rtn2 the month before, rtn1 the month before that (across a year end)
    assert got[("C000000001", "2024-12")] == 1.5
    assert got[("C000000001", "2025-01")] == -2.25
    assert got[("C000000001", "2025-02")] == 3.0
    assert got[("C000000002", "2024-12")] == 0.1
    assert got[("C000000002", "2025-02")] == 0.3
    assert len(rets) == 6


def test_latest_filing_wins_for_month():
    rows = pd.DataFrame(
        [
            ["akre", "S9", "C1", "A-OLD", "2025-03-30", "2025-01-31", "2025-01", 1.0],
            ["akre", "S9", "C1", "A-NEW", "2025-04-02", "2025-01-31", "2025-01", 1.5],
            ["akre", "S9", "C1", "A-OLD", "2025-03-30", "2025-01-31", "2024-12", 2.0],
            ["akre", "S9", "C2", "A-OLD", "2025-03-30", "2025-01-31", "2025-01", 9.0],
        ],
        columns=NPORT_RETURNS,
    )
    out = latest_monthly_returns(rows).set_index(["class_id", "month"])
    assert len(out) == 3
    assert out.loc[("C1", "2025-01"), "rtn_pct"] == 1.5
    assert out.loc[("C1", "2025-01"), "accession"] == "A-NEW"
    assert out.loc[("C1", "2024-12"), "rtn_pct"] == 2.0
    assert out.loc[("C2", "2025-01"), "rtn_pct"] == 9.0


def test_akre_month_source_order():
    months = [pd.Period(m, freq="M") for m in ("2025-08", "2025-09", "2025-10", "2025-11", "2025-12")]
    class_pct = pd.Series({"2025-08": 1.0, "2025-09": None})
    etf_class_pct = pd.Series({"2025-08": 7.0, "2025-09": 2.0})
    etf_month_ret = pd.Series({pd.Period("2025-10", freq="M"): 0.05, pd.Period("2025-11", freq="M"): 0.03})
    out = nport_month_series(months, class_pct, etf_class_pct, etf_month_ret, date(2025, 10, 27))
    print(out.to_string())
    assert out["source"].tolist() == ["nport_b5", "nport_etf_class", "missing", "yfinance_etf", "missing"]
    assert out["ret"].iloc[0] == 1.0 / 100
    assert out["ret"].iloc[1] == 2.0 / 100
    assert out["ret"].iloc[3] == 0.03
    assert out["ret"].iloc[[2, 4]].isna().all()
