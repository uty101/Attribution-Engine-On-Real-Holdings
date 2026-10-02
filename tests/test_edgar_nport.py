from datetime import date
from pathlib import Path

import pandas as pd

from attrib.edgar import FILINGS_NPORT, equity_rows_nport, parse_nport, resolve_nport_books

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "nport" / "ivv_2023-06-30_0001752724-23-191503.xml"
NS = "http://www.sec.gov/edgar/nport"


def _xml(period: str, rows: list[tuple]) -> bytes:
    """rows: (name, cusip, balance, units, val_usd, pct_val, asset_cat)."""
    parts = []
    for name, cusip, bal, units, val, pct, cat in rows:
        cus = f"<cusip>{cusip}</cusip>" if cusip is not None else ""
        parts.append(
            f"<invstOrSec><name>{name}</name><lei>N/A</lei><title>{name} COM</title>{cus}"
            f'<identifiers><isin value="US0000000000"/></identifiers>'
            f"<balance>{bal}</balance><units>{units}</units><curCd>USD</curCd>"
            f"<valUSD>{val}</valUSD><pctVal>{pct}</pctVal><payoffProfile>Long</payoffProfile>"
            f"<assetCat>{cat}</assetCat><issuerCat>CORP</issuerCat><invCountry>US</invCountry></invstOrSec>"
        )
    return (
        f'<edgarSubmission xmlns="{NS}"><formData><genInfo><seriesId>S000000001</seriesId>'
        f"<repPdDate>{period}</repPdDate></genInfo><invstOrSecs>{''.join(parts)}</invstOrSecs>"
        f"</formData></edgarSubmission>"
    ).encode()


def _raw(accession: str, xml: bytes) -> pd.DataFrame:
    _, raw = parse_nport(xml)
    return raw.assign(entity="ivv", accession=accession)


def test_only_ec_ns_rows_kept():
    xml = _xml(
        "2023-06-30",
        [
            ("KEEP", "111111111", 10, "NS", 100.0, 50.0, "EC"),
            ("BOND", "222222222", 10, "PA", 100.0, 10.0, "DBT"),
            ("PRINC", "333333333", 10, "PA", 100.0, 10.0, "EC"),
            ("CASHFUND", "444444444", 10, "NS", 100.0, 10.0, "STIV"),
            ("FUTURE", None, 1, "NC", 5.0, 0.1, "DE"),
            ("NOCUSIP", "000000000", 10, "NS", 100.0, 10.0, "EC"),
        ],
    )
    raw = _raw("A-1", xml)
    assert raw.loc[raw["name"] == "NOCUSIP", "cusip"].item() == ""
    assert list(equity_rows_nport(raw)["name"]) == ["KEEP"]
    filings = pd.DataFrame([["ivv", "S000000001", "A-1", "2023-08-25", "2023-06-30"]], columns=FILINGS_NPORT)
    book = resolve_nport_books(filings, raw, [date(2023, 6, 30)])
    assert list(book["cusip"]) == ["111111111"]
    assert book["value_usd"].tolist() == [100.0]
    assert book["shares"].tolist() == [10.0]


def test_header_series_and_period():
    header, raw = parse_nport(FIX.read_bytes())
    print(header)
    assert header == {"seriesId": "S000004310", "repPdDate": "2023-06-30"}
    assert (raw["period_date"] == "2023-06-30").all()


def test_latest_filing_wins_duplicate_period():
    old = _raw("A-OLD", _xml("2023-06-30", [("OLD", "111111111", 1, "NS", 1.0, 100.0, "EC")]))
    new = _raw("A-NEW", _xml("2023-06-30", [("NEW", "222222222", 1, "NS", 2.0, 100.0, "EC")]))
    other = _raw("A-OUT", _xml("2023-05-31", [("OUT", "333333333", 1, "NS", 3.0, 100.0, "EC")]))
    filings = pd.DataFrame(
        [
            ["ivv", "S000000001", "A-NEW", "2023-09-01", "2023-06-30"],
            ["ivv", "S000000001", "A-OLD", "2023-08-25", "2023-06-30"],
            ["ivv", "S000000001", "A-OUT", "2023-07-25", "2023-05-31"],
        ],
        columns=FILINGS_NPORT,
    )
    raw = pd.concat([old, new, other], ignore_index=True)
    book = resolve_nport_books(filings, raw, [date(2023, 6, 30)])
    assert list(book["cusip"]) == ["222222222"]
    assert list(book["period_date"]) == ["2023-06-30"]


def test_ivv_fixture_shape():
    _, raw = parse_nport(FIX.read_bytes())
    kept = equity_rows_nport(raw)
    n, pct = len(kept), kept["pct_val"].sum()
    print(f"kept rows {n}, kept pctVal sum {pct!r}")
    assert 495 <= n <= 510
    assert 98 <= pct <= 100.5
