from datetime import date
from pathlib import Path

import pandas as pd

from attrib.edgar import FILINGS_NPORT, equity_rows_nport, list_nport_filings, parse_nport, resolve_nport_books

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "nport" / "ivv_2023-06-30_0001752724-23-191503.xml"
NS = "http://www.sec.gov/edgar/nport"


def _xml(period: str, rows: list[tuple]) -> bytes:
    """rows: (name, cusip, balance, units, val_usd, pct_val, asset_cat[, isin]).

    `cusip` or `isin` None leaves that element out; `isin` defaults to US0000000000, which
    fails the ISIN check digit.
    """
    parts = []
    for name, cusip, bal, units, val, pct, cat, *rest in rows:
        isin = rest[0] if rest else "US0000000000"
        cus = f"<cusip>{cusip}</cusip>" if cusip is not None else ""
        ids = f'<isin value="{isin}"/>' if isin is not None else ""
        parts.append(
            f"<invstOrSec><name>{name}</name><lei>N/A</lei><title>{name} COM</title>{cus}"
            f"<identifiers>{ids}</identifiers>"
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
    by_isin = kept[kept["sec_id"] == kept["isin"]]
    n_isin, pct_isin = len(by_isin), by_isin["pct_val"].sum()
    print(f"kept rows with an ISIN sec_id {n_isin}, their pctVal sum {pct_isin!r}")
    assert n_isin == 25
    assert 3.0 <= pct_isin <= 3.3


def test_isin_only_row_kept():
    xml = _xml(
        "2023-06-30",
        [
            ("DOMESTIC", "111111111", 10, "NS", 100.0, 50.0, "EC"),
            ("ACCENTURE", None, 5, "NS", 60.0, 30.0, "EC", "IE00B4BNMY34"),
        ],
    )
    raw = _raw("A-1", xml)
    filings = pd.DataFrame([["ivv", "S000000001", "A-1", "2023-08-25", "2023-06-30"]], columns=FILINGS_NPORT)
    book = resolve_nport_books(filings, raw, [date(2023, 6, 30)]).set_index("sec_id")
    assert list(book.index) == ["111111111", "IE00B4BNMY34"]
    assert book.loc["IE00B4BNMY34", "cusip"] == ""
    assert book.loc["IE00B4BNMY34", "isin"] == "IE00B4BNMY34"
    assert book.loc["IE00B4BNMY34", "value_usd"] == 60.0
    assert book.loc["IE00B4BNMY34", "shares"] == 5.0


def test_row_with_no_ids_dropped():
    xml = _xml(
        "2023-06-30",
        [
            ("KEEP", "111111111", 10, "NS", 100.0, 50.0, "EC"),
            ("NOIDS", None, 10, "NS", 40.0, 20.0, "EC", None),
            ("NA_CUSIP", "N/A", 10, "NS", 30.0, 15.0, "EC", None),
        ],
    )
    raw = _raw("A-1", xml)
    assert list(equity_rows_nport(raw)["name"]) == ["KEEP"]
    filings = pd.DataFrame([["ivv", "S000000001", "A-1", "2023-08-25", "2023-06-30"]], columns=FILINGS_NPORT)
    book = resolve_nport_books(filings, raw, [date(2023, 6, 30)])
    assert list(book["sec_id"]) == ["111111111"]
    assert raw["val_usd"].sum() - book["value_usd"].sum() == 70.0  # dropped_value_usd


class FakeFeedClient:
    """Serves atom feed pages in order; the last page has no entries."""

    def __init__(self, pages: list[bytes]):
        self.pages = list(pages)
        self.urls: list[str] = []

    def get_bytes(self, url: str) -> bytes:
        self.urls.append(url)
        return self.pages.pop(0)


def _feed(entries: list[tuple[str, str, str]]) -> bytes:
    """entries: (filing_type, accession, filing_date)."""
    body = "".join(
        f"<entry><content type=\"text/xml\"><accession-number>{acc}</accession-number>"
        f"<filing-date>{fd}</filing-date><filing-type>{ft}</filing-type></content></entry>"
        for ft, acc, fd in entries
    )
    return f'<feed xmlns="http://www.w3.org/2005/Atom">{body}</feed>'.encode()


def test_amendment_supersedes_original():
    client = FakeFeedClient(
        [
            _feed(
                [
                    ("NPORT-P/A", "A-AMEND", "2023-10-02"),
                    ("NPORT-P", "A-ORIG", "2023-08-25"),
                    ("N-CSR", "A-OTHER", "2023-08-01"),
                ]
            ),
            _feed([]),
        ]
    )
    filings = list_nport_filings(client, "S000000001")
    assert list(filings["accession"]) == ["A-ORIG", "A-AMEND"]
    filings["period_date"] = "2023-06-30"  # filled from repPdDate by the caller
    orig = _raw("A-ORIG", _xml("2023-06-30", [("ORIG", "111111111", 1, "NS", 1.0, 100.0, "EC")]))
    amend = _raw("A-AMEND", _xml("2023-06-30", [("AMEND", "222222222", 1, "NS", 2.0, 100.0, "EC")]))
    book = resolve_nport_books(filings.assign(entity="ivv"), pd.concat([orig, amend], ignore_index=True),
                               [date(2023, 6, 30)])
    assert list(book["name"]) == ["AMEND"]
    assert list(book["sec_id"]) == ["222222222"]
