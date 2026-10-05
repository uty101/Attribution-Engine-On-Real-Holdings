from pathlib import Path

import pandas as pd

from attrib.mapping import FALLBACK, OVERRIDES, build_security_map, judge_results, parse_siccodes12, sic_to_ff12, us_isin

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


def _fallback(rows=()):
    return pd.DataFrame(list(rows), columns=FALLBACK).astype(str)


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
    smap = build_security_map(figi, _fallback(), _overrides(), _tickers([[1067983, "BRK-B", "BERKSHIRE HATHAWAY INC"]]),
        _sic([[1067983, "BERKSHIRE HATHAWAY INC", "6331", "Fire, Marine & Casualty Insurance"]]), FF12,
    )
    row = smap.iloc[0]
    assert (row["ticker"], row["yf_ticker"], row["cik"], row["map_status"]) == ("BRK/B", "BRK-B", 1067983, "mapped")


def test_overrides_beat_openfigi():
    figi = _figi([["123456789", "cusip", "ok", "1", "F1", "", "OLD", "OLD CO", "US", "Equity", "Common Stock"]])
    smap = build_security_map(figi, _fallback(), _overrides([["ticker", "123456789", "", "NEW", "reviewer"]]),
        _tickers([[1, "OLD", "OLD CO"], [2, "NEW", "NEW CO"]]),
        _sic([[1, "OLD CO", "2834", ""], [2, "NEW CO", "3571", ""]]), FF12,
    )
    row = smap.iloc[0]
    assert (row["ticker"], row["cik"], row["ff12"], row["source"]) == ("NEW", 2, "BusEq", "openfigi;override_ticker")


def test_isin_sec_id_maps():
    figi = _figi([
        ["G1151C101", "cusip", "ok", "1", "BBG000D9D830", "BBG000D9D830", "ACN", "ACCENTURE PLC-CL A", "US",
         "Equity", "Common Stock"],
        ["IE00B4BNMY34", "isin", "ok", "1", "BBG000D9D830", "BBG000D9D830", "ACN", "ACCENTURE PLC-CL A", "US",
         "Equity", "Common Stock"],
    ])
    smap = build_security_map(figi, _fallback(), _overrides(), _tickers([[1467373, "ACN", "Accenture plc"]]),
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
    before = build_security_map(figi, _fallback(), _overrides(), tickers, sic, FF12).iloc[0]
    assert (before["cik"] is pd.NA or pd.isna(before["cik"])) and before["map_status"] == "no_cik"
    assert before["ff12"] == "Other"
    after = build_security_map(figi, _fallback(), _overrides([["cik", "987654321", "", "42", "Gone Co"]]), tickers, sic, FF12
    ).iloc[0]
    assert (after["cik"], after["sic"], after["ff12"]) == (42, 6021, "Money")
    assert (after["map_status"], after["source"]) == ("mapped", "openfigi;override_cik")


def _fb_row(sec_id, pass_no, ticker, name, accepted):
    return [sec_id, str(pass_no), "ID_ISIN", "X", "1", ticker, name, "US", "Equity", "Common Stock",
            str(accepted), "" if accepted else "rejected"]


def test_fallback_precedence():
    figi = _figi(
        [[f"00000000{c}", "cusip", "ok", "1", f"F{c}", "", f"P1{c}", f"{c} CO", "US", "Equity", "Common Stock"]
         for c in ["A", "E"]]
        + [[f"00000000{c}", "cusip", "No identifier found.", "", "", "", "", "", "", "", ""] for c in ["B", "C", "D"]]
    )
    fb = _fallback(
        [_fb_row("00000000A", 2, "P2A", "A CO", True)]  # pass 1 beats 2
        + [_fb_row("00000000B", p, f"P{p}B", "B CO", True) for p in (2, 3, 4)]  # 2 beats 3 beats 4
        + [_fb_row("00000000C", 3, "P3C", "C CO", True), _fb_row("00000000C", 4, "P4C", "C CO", True)]
        + [_fb_row("00000000D", 3, "P3D", "D CO", False), _fb_row("00000000D", 4, "P4D", "D CO", True)]
        + [_fb_row("00000000E", 2, "P2E", "E CO", True)]
    )
    tickers = _tickers([[i, t, t] for i, t in enumerate(["P1A", "P2B", "P3C", "P4D", "OVR"], start=1)])
    sic = _sic([[i, "", "3571", ""] for i in range(1, 6)])
    ov = _overrides([["ticker", "00000000E", "", "OVR", "reviewer"]])  # an override beats all
    smap = build_security_map(figi, fb, ov, tickers, sic, FF12).set_index("sec_id")
    print(smap[["ticker", "source", "map_status"]].to_string())
    assert smap["ticker"].tolist() == ["P1A", "P2B", "P3C", "P4D", "OVR"]
    assert smap["source"].tolist() == ["openfigi", "figi_isin", "figi_noexch", "yahoo_isin", "openfigi;override_ticker"]
    assert (smap["map_status"] == "mapped").all()


def test_name_check_rejects():
    rows = judge_results(
        "G1151C101", 4, "yahoo_search", "IE00B4BNMY34",
        [
            {"ticker": "ACNB", "name": "ACNB Corporation", "exch_code": "NMS", "market_sector": "",
             "security_type": "EQUITY"},
            {"ticker": "ACN", "name": "Accenture plc", "exch_code": "NYQ", "market_sector": "",
             "security_type": "EQUITY"},
        ],
        "Accenture plc Class A",
    )
    df = pd.DataFrame(rows, columns=FALLBACK)
    print(df.to_string())
    assert df["accepted"].tolist() == [False, True]
    assert df["reject_reason"].iloc[0] == "name check: ACCENTURE != ACNB"
    other = pd.DataFrame(
        judge_results("123456789", 4, "yahoo_search", "US1234567893",
                      [{"ticker": "ZZZ", "name": "Zeta Holdings", "exch_code": "NYQ", "security_type": "EQUITY"}],
                      "The Alpha Company"),
        columns=FALLBACK,
    )
    assert other["accepted"].tolist() == [False]
    assert other["reject_reason"].iloc[0] == "name check: ALPHA != ZETA"


def test_us_isin_from_cusip():
    assert us_isin("30231G102") == "US30231G1022"
    assert us_isin("037833100") == "US0378331005"

def test_cik_override_beats_ticker_lookup():
    # instructions/03, Section B: a reused ticker (STI) maps to the wrong CIK in today's
    # company_tickers.json; the cik override wins over the ticker -> CIK match.
    figi = _figi([["867914103", "cusip", "ok", "1", "F3", "", "STI", "SUNTRUST BANKS INC", "US", "Equity",
                   "Common Stock"]])
    tickers = _tickers([[999, "STI", "SOLIDION TECHNOLOGY INC"]])
    sic = _sic([[999, "Solidion Technology Inc.", "3571", ""], [750556, "SUNTRUST BANKS INC", "6021", ""]])
    before = build_security_map(figi, _fallback(), _overrides(), tickers, sic, FF12).iloc[0]
    assert (before["cik"], before["ff12"], before["source"]) == (999, "BusEq", "openfigi")
    ov = _overrides([["cik", "867914103", "", "750556", "SunTrust Banks"]])
    after = build_security_map(figi, _fallback(), ov, tickers, sic, FF12).iloc[0]
    print(pd.DataFrame([before, after]).to_string())
    assert (after["cik"], after["sic"], after["ff12"]) == (750556, 6021, "Money")
    assert (after["map_status"], after["source"]) == ("mapped", "openfigi;override_cik")


def test_cik_override_name_mismatch_not_applied():
    # instructions/03, Section B: the override's source_note names a different company from the
    # CIK's submissions name, so the row is not applied and the ticker -> CIK match stands.
    from attrib.mapping import cik_override_check

    figi = _figi([["867914103", "cusip", "ok", "1", "F3", "", "STI", "SUNTRUST BANKS INC", "US", "Equity",
                   "Common Stock"]])
    tickers = _tickers([[999, "STI", "SOLIDION TECHNOLOGY INC"]])
    sic = _sic([[999, "Solidion Technology Inc.", "3571", ""], [750556, "TRUIST FINANCIAL CORP", "6021", ""]])
    ov = _overrides([["cik", "867914103", "", "750556", "SunTrust Banks"]])
    chk = cik_override_check(ov, sic)
    print(chk.to_string())
    assert chk[["sec_id", "cik", "submissions_name", "note_name", "match"]].values.tolist() == [
        ["867914103", 750556, "TRUIST FINANCIAL CORP", "SunTrust Banks", False]
    ]
    row = build_security_map(figi, _fallback(), ov, tickers, sic, FF12).iloc[0]
    assert (row["cik"], row["ff12"], row["source"]) == (999, "BusEq", "openfigi")
