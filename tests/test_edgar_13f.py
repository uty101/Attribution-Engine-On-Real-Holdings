from datetime import date
from pathlib import Path

import pandas as pd

from attrib.config import load_config
from attrib.edgar import (
    FILINGS_13F,
    equity_rows_13f,
    parse_13f_infotable,
    resolve_13f_books,
    units_check,
)

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
FIX = ROOT / "tests" / "fixtures" / "13f" / "akre"
F2023 = FIX / "2023-06-30_0001112520-23-000013.xml"
F2022 = FIX / "2022-06-30_0001112520-22-000013.xml"
FILED_2023 = date(2023, 8, 11)  # filingDate of 0001112520-23-000013
FILED_2022 = date(2022, 8, 11)  # filingDate of 0001112520-22-000013
NS = "http://www.sec.gov/edgar/document/thirteenf/informationtable"


def _xml(rows: list[tuple]) -> bytes:
    """rows: (name, cusip, value, shares, ssh_type, put_call or None)."""
    parts = []
    for name, cusip, value, shares, ssh, pc in rows:
        putcall = f"<putCall>{pc}</putCall>" if pc else ""
        parts.append(
            f"<infoTable><nameOfIssuer>{name}</nameOfIssuer><titleOfClass>COM</titleOfClass>"
            f"<cusip>{cusip}</cusip><value>{value}</value>"
            f"<shrsOrPrnAmt><sshPrnamt>{shares}</sshPrnamt><sshPrnamtType>{ssh}</sshPrnamtType></shrsOrPrnAmt>"
            f"{putcall}<investmentDiscretion>SOLE</investmentDiscretion></infoTable>"
        )
    return f'<informationTable xmlns="{NS}">{"".join(parts)}</informationTable>'.encode()


def _book(xml: bytes, filed: date, period: str) -> pd.DataFrame:
    filings = pd.DataFrame(
        [["x", 1, "A-1", "13F-HR", str(filed), period, "", "t.xml"]], columns=FILINGS_13F
    )
    return resolve_13f_books(filings, {"A-1": parse_13f_infotable(xml, filed)}, [date.fromisoformat(period)])


def test_units_thousands_2022_06_30():
    raw = parse_13f_infotable(F2022.read_bytes(), FILED_2022)
    assert FILED_2022 < CFG.edgar.units_switch_date
    assert (raw["value_usd"] == raw["value_raw"] * 1000).all()


def test_units_dollars_2023_06_30():
    raw = parse_13f_infotable(F2023.read_bytes(), FILED_2023)
    assert FILED_2023 >= CFG.edgar.units_switch_date
    assert (raw["value_usd"] == raw["value_raw"]).all()


def test_putcall_and_prn_rows_dropped():
    xml = _xml(
        [
            ("KEEP", "111111111", 100, 10, "SH", None),
            ("CALL", "222222222", 200, 20, "SH", "Call"),
            ("PUT", "333333333", 300, 30, "SH", "Put"),
            ("BOND", "444444444", 400, 40, "PRN", None),
        ]
    )
    raw = parse_13f_infotable(xml, FILED_2023)
    assert len(raw) == 4  # the parser keeps every row
    assert list(equity_rows_13f(raw)["name"]) == ["KEEP"]
    book = _book(xml, FILED_2023, "2023-06-30")
    assert list(book["cusip"]) == ["111111111"]


def test_duplicate_cusip_rows_summed():
    xml = _xml(
        [
            ("ALPHA", "abcdef123", 100, 10, "SH", None),
            ("ALPHA", "ABCDEF123", 50, 5, "SH", None),
            ("BETA", "999999999", 70, 7, "SH", None),
            ("BAD", "12345", 1, 1, "SH", None),
        ]
    )
    book = _book(xml, FILED_2023, "2023-06-30").set_index("cusip")
    assert list(book.index) == ["999999999", "ABCDEF123"]
    assert book.loc["ABCDEF123", "value_usd"] == 150
    assert book.loc["ABCDEF123", "shares"] == 15


def _filings(rows):
    return pd.DataFrame([["x", 1, *r] for r in rows], columns=FILINGS_13F)


def test_restatement_replaces_book():
    filings = _filings(
        [
            ["O-1", "13F-HR", "2021-05-10", "2021-03-31", "", "a.xml"],
            ["R-1", "13F-HR/A", "2021-06-01", "2021-03-31", "RESTATEMENT", "b.xml"],
            ["R-2", "13F-HR/A", "2021-07-09", "2021-03-31", "RESTATEMENT", "c.xml"],
        ]
    )
    fd = date(2021, 5, 10)
    tables = {
        "O-1": parse_13f_infotable(_xml([("OLD", "111111111", 1, 1, "SH", None)]), fd),
        "R-1": parse_13f_infotable(_xml([("MID", "222222222", 2, 1, "SH", None)]), fd),
        "R-2": parse_13f_infotable(_xml([("NEW", "333333333", 3, 1, "SH", None)]), fd),
    }
    book = resolve_13f_books(filings, tables, [date(2021, 3, 31)])
    assert list(book["cusip"]) == ["333333333"]
    assert book["value_usd"].tolist() == [3000]


def test_new_holdings_appends():
    filings = _filings(
        [
            ["N-0", "13F-HR/A", "2024-05-01", "2024-03-31", "NEW HOLDINGS", "z.xml"],
            ["O-1", "13F-HR", "2024-05-13", "2024-03-31", "", "a.xml"],
            ["N-1", "13F-HR/A", "2024-05-23", "2024-03-31", "NEW HOLDINGS", "b.xml"],
        ]
    )
    fd = date(2024, 5, 13)
    tables = {
        "N-0": parse_13f_infotable(_xml([("EARLY", "999999999", 9, 1, "SH", None)]), fd),
        "O-1": parse_13f_infotable(_xml([("BASE", "111111111", 100, 1, "SH", None)]), fd),
        "N-1": parse_13f_infotable(
            _xml([("ADD", "222222222", 50, 1, "SH", None), ("BASE", "111111111", 10, 1, "SH", None)]), fd
        ),
    }
    book = resolve_13f_books(filings, tables, [date(2024, 3, 31)]).set_index("cusip")
    assert list(book.index) == ["111111111", "222222222"]  # N-0 was filed before the book in use
    assert book.loc["111111111", "value_usd"] == 110
    assert book.loc["222222222", "value_usd"] == 50


def test_median_implied_price_in_range_fixtures():
    lo, hi = CFG.edgar.implied_price_lo, CFG.edgar.implied_price_hi
    for path, filed, period in [(F2022, FILED_2022, "2022-06-30"), (F2023, FILED_2023, "2023-06-30")]:
        p = units_check(_book(path.read_bytes(), filed, period))
        print(f"{path.name}: median implied price {p!r}")
        assert lo <= p <= hi


def test_akre_2023_top_rows():
    raw = parse_13f_infotable(F2023.read_bytes(), FILED_2023)
    top = equity_rows_13f(raw).sort_values("value_usd", ascending=False).head(5)
    got = list(top[["name", "cusip", "value_usd", "shares"]].itertuples(index=False, name=None))
    # literals read from the fixture XML (value in dollars, sshPrnamt)
    assert got == [
        ("MASTERCARD INCORPORATED", "57636Q104", 2308458225, 5869459.0),
        ("MOODYS CORP", "615369105", 1836386862, 5281223.0),
        ("AMERICAN TOWER CORP NEW", "03027X100", 1308115021, 6744947.0),
        ("VISA INC", "92826C839", 1168909332, 4922138.0),
        ("OREILLY AUTOMOTIVE INC", "67103H107", 1063968241, 1113753.0),
    ]
