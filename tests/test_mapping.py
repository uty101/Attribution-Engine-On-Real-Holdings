from pathlib import Path

import pandas as pd

from attrib.mapping import OVERRIDES, build_security_map, parse_siccodes12, sic_to_ff12

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
FF12 = parse_siccodes12((RAW / "french" / "Siccodes12.txt").read_text(encoding="latin-1"))

FIGI_COLS = [
    "sec_id", "id_type", "status", "result_rank", "figi", "composite_figi", "ticker", "name", "exch_code",
    "market_sector", "security_type",
]


def _figi(rows):
    return pd.DataFrame(rows, columns=FIGI_COLS).astype(str)


def _tickers(rows):
    return pd.DataFrame(rows, columns=["cik", "ticker", "title"])


def _sic(rows):
    return pd.DataFrame(rows, columns=["cik", "name", "sic", "sic_description"]).astype(str)


def _overrides(rows=()):
    return pd.DataFrame(list(rows), columns=OVERRIDES).astype(str)


def test_ff12_known_codes():
    got = {s: sic_to_ff12(s, FF12) for s in (3571, 2834, 6021, 1311, 4911, 9999)}
    print(got)
    assert got == {3571: "BusEq", 2834: "Hlth", 6021: "Money", 1311: "Enrgy", 4911: "Utils", 9999: "Other"}


def test_ff12_ranges_land_in_one_industry():
    overlaps = []
    for sic in range(100, 10000):
        hit = FF12[(FF12["sic_lo"] <= sic) & (sic <= FF12["sic_hi"])]
        if len(hit) > 1:
            overlaps.append((sic, hit.to_string()))
    for sic, rows in overlaps:
        print(sic, rows, sep="\n")
    assert overlaps == []


def test_ticker_normalisation_brk():
    figi = _figi([["084670702", "cusip", "ok", "1", "BBG000DWG505", "BBG000DWG505", "BRK/B",
                   "BERKSHIRE HATHAWAY INC-CL B", "US", "Equity", "Common Stock"]])
    smap = build_security_map(
        figi, _overrides(), _tickers([[1067983, "BRK-B", "BERKSHIRE HATHAWAY INC"]]),
        _sic([[1067983, "BERKSHIRE HATHAWAY INC", "6331", "Fire, Marine & Casualty Insurance"]]), FF12,
    )
    row = smap.iloc[0]
    assert (row["ticker"], row["yf_ticker"], row["cik"], row["map_status"]) == ("BRK/B", "BRK-B", 1067983, "mapped")


def test_overrides_beat_openfigi():
    figi = _figi([["123456789", "cusip", "ok", "1", "F1", "", "OLD", "OLD CO", "US", "Equity", "Common Stock"]])
    smap = build_security_map(
        figi, _overrides([["ticker", "123456789", "", "NEW", "reviewer"]]),
        _tickers([[1, "OLD", "OLD CO"], [2, "NEW", "NEW CO"]]),
        _sic([[1, "OLD CO", "2834", ""], [2, "NEW CO", "3571", ""]]), FF12,
    )
    row = smap.iloc[0]
    assert (row["ticker"], row["cik"], row["ff12"], row["source"]) == ("NEW", 2, "BusEq", "override_ticker")


def test_isin_sec_id_maps():
    figi = _figi([
        ["G1151C101", "cusip", "ok", "1", "BBG000D9D830", "BBG000D9D830", "ACN", "ACCENTURE PLC-CL A", "US",
         "Equity", "Common Stock"],
        ["IE00B4BNMY34", "isin", "ok", "1", "BBG000D9D830", "BBG000D9D830", "ACN", "ACCENTURE PLC-CL A", "US",
         "Equity", "Common Stock"],
    ])
    smap = build_security_map(
        figi, _overrides(), _tickers([[1467373, "ACN", "Accenture plc"]]),
        _sic([[1467373, "Accenture plc", "7389", "Services-Business Services, NEC"]]), FF12,
    ).set_index("sec_id")
    cols = ["ticker", "cik", "sic", "ff12", "map_status"]
    assert smap.loc["IE00B4BNMY34", "id_type"] == "isin"
    assert smap.loc["G1151C101", "id_type"] == "cusip"
    assert smap.loc["IE00B4BNMY34", cols].tolist() == smap.loc["G1151C101", cols].tolist()
    assert smap.loc["IE00B4BNMY34", "map_status"] == "mapped"


def test_cik_override():
    figi = _figi([["987654321", "cusip", "ok", "1", "F2", "", "GONE", "GONE CO", "US", "Equity", "Common Stock"]])
    tickers = _tickers([[7, "OTHER", "OTHER CO"]])
    sic = _sic([[42, "GONE CO", "6021", "National Commercial Banks"]])
    before = build_security_map(figi, _overrides(), tickers, sic, FF12).iloc[0]
    assert (before["cik"] is pd.NA or pd.isna(before["cik"])) and before["map_status"] == "no_cik"
    assert before["ff12"] == "Other"
    after = build_security_map(
        figi, _overrides([["cik", "987654321", "", "42", "reviewer"]]), tickers, sic, FF12
    ).iloc[0]
    assert (after["cik"], after["sic"], after["ff12"]) == (42, 6021, "Money")
    assert (after["map_status"], after["source"]) == ("mapped", "override_cik")
