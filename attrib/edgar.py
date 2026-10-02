"""EDGAR HTTP client and the 13F and N-PORT parsers (kickoff Section 5.1).

Only `scripts/pull_data.py` constructs an `EdgarClient` (rule 8); tests drive it
with a fake session object.
"""

from __future__ import annotations

import re
import time
from collections.abc import Sequence
from datetime import date
from functools import lru_cache
from pathlib import Path

import pandas as pd
import requests
from lxml import etree

from attrib.config import Config, load_config

SUBMISSIONS = "https://data.sec.gov/submissions"
ARCHIVES = "https://www.sec.gov/Archives/edgar/data"

FILINGS_13F = ["entity", "cik", "accession", "form", "filing_date", "period_date", "amendment_type", "infotable_name"]
HOLDINGS_RAW_13F = ["name", "title_class", "cusip", "value_raw", "value_usd", "shares", "ssh_type", "put_call"]
HOLDINGS = ["entity", "period_date", "cusip", "name", "value_usd", "shares"]
FILINGS_NPORT = ["entity", "series_id", "accession", "filing_date", "period_date"]
HOLDINGS_RAW_NPORT = [
    "entity", "accession", "period_date", "name", "title", "cusip", "isin", "balance", "units",
    "val_usd", "pct_val", "asset_cat", "issuer_cat", "inv_country",
]
NPORT_FEED = (
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={series_id}"
    "&type=NPORT-P&dateb=&owner=include&count=100&output=atom"
)

_CUSIP_RE = re.compile(r"^[0-9A-Z]{9}$")
_PARSER = etree.XMLParser(huge_tree=True, resolve_entities=False)


@lru_cache(maxsize=1)
def _config() -> Config:
    return load_config(Path(__file__).resolve().parents[1] / "config.toml")


def holdings_dates(cfg: Config) -> list[date]:
    """The calendar quarter ends H from `first_holdings_date` to `last_holdings_date` (kickoff 3.3)."""
    out, y, m = [], cfg.sample.first_holdings_date.year, cfg.sample.first_holdings_date.month
    while True:
        d = (pd.Timestamp(year=y, month=m, day=1) + pd.offsets.MonthEnd(0)).date()
        if d > cfg.sample.last_holdings_date:
            return out
        out.append(d)
        m += 3
        if m > 12:
            y, m = y + 1, m - 12


def filing_base_url(cik: int | str, accession: str) -> str:
    return f"{ARCHIVES}/{int(cik)}/{accession.replace('-', '')}"


def _text(el, path: str) -> str:
    v = el.findtext(path)
    return "" if v is None else v.strip()


class EdgarClient:
    """Rate-limited GET with retries on HTTP 429 and 5xx.

    A request counts towards `min_interval` when it is sent, not when it returns.
    """

    def __init__(
        self,
        user_agent: str,
        min_interval: float,
        retries: int,
        backoff: Sequence[float],
        session=None,
    ) -> None:
        if len(backoff) != retries:
            raise ValueError(f"len(backoff) = {len(backoff)} must equal retries = {retries}")
        self.user_agent = user_agent
        self.min_interval = min_interval
        self.retries = retries
        self.backoff = list(backoff)
        self.session = session if session is not None else requests.Session()
        self._last_sent: float | None = None

    def _send(self, url: str):
        if self._last_sent is not None:
            wait = self.min_interval - (time.monotonic() - self._last_sent)
            if wait > 0:
                time.sleep(wait)
        self._last_sent = time.monotonic()
        return self.session.get(url, headers={"User-Agent": self.user_agent})

    def _get(self, url: str):
        for attempt in range(self.retries + 1):
            resp = self._send(url)
            status = resp.status_code
            if status == 200:
                return resp
            if status != 429 and not 500 <= status <= 599:
                raise RuntimeError(f"HTTP {status} for {url}")
            if attempt == self.retries:
                raise RuntimeError(f"HTTP {status} for {url} after {self.retries} retries")
            time.sleep(self.backoff[attempt])
        raise AssertionError("unreachable")

    def get_json(self, url: str) -> dict:
        return self._get(url).json()

    def get_bytes(self, url: str) -> bytes:
        return self._get(url).content


# ---------------------------------------------------------------- 13F


def find_infotable_name(index_json: dict) -> str:
    """The information table: the 1 XML file in the filing index other than `primary_doc.xml`."""
    names = [i["name"] for i in index_json["directory"]["item"]]
    xml = [n for n in names if n.lower().endswith(".xml") and n != "primary_doc.xml"]
    if len(xml) != 1:
        raise ValueError(f"expected 1 information table XML in {index_json['directory'].get('name')}, found {xml}")
    return xml[0]


def _amendment_type(primary_doc: bytes) -> str:
    root = etree.fromstring(primary_doc, _PARSER)
    for el in root.iter("{*}amendmentType"):
        return (el.text or "").strip()
    return ""


def list_13f_filings(client: EdgarClient, cik: int) -> pd.DataFrame:
    """FILINGS_13F for forms 13F-HR and 13F-HR/A, from the submissions JSON and every `filings.files` page.

    `entity` is left blank for the caller. Text-era filings (no `primary_doc.xml` in the
    index, all before 2013) carry no XML information table: `infotable_name` and
    `amendment_type` stay blank for them.
    """
    sub = client.get_json(f"{SUBMISSIONS}/CIK{cik:010d}.json")
    blocks = [sub["filings"]["recent"]]
    blocks += [client.get_json(f"{SUBMISSIONS}/{f['name']}") for f in sub["filings"]["files"]]
    rows = []
    for b in blocks:
        for acc, form, fdate, pdate in zip(b["accessionNumber"], b["form"], b["filingDate"], b["reportDate"]):
            if form not in ("13F-HR", "13F-HR/A"):
                continue
            base = filing_base_url(cik, acc)
            index = client.get_json(f"{base}/index.json")
            names = {i["name"] for i in index["directory"]["item"]}
            info = amend = ""
            if "primary_doc.xml" in names:
                info = find_infotable_name(index)
                if form == "13F-HR/A":
                    amend = _amendment_type(client.get_bytes(f"{base}/primary_doc.xml"))
            rows.append(["", cik, acc, form, fdate, pdate, amend, info])
    df = pd.DataFrame(rows, columns=FILINGS_13F)
    return df.sort_values(["filing_date", "accession"], kind="mergesort").reset_index(drop=True)


def parse_13f_infotable(xml: bytes, filing_date: date) -> pd.DataFrame:
    """HOLDINGS_RAW_13F: every `infoTable` row, unfiltered."""
    root = etree.fromstring(xml, _PARSER)
    # kickoff 5.1: value_usd = value x 1000 if filing date < units_switch_date, else value
    mult = 1000 if filing_date < _config().edgar.units_switch_date else 1
    rows = []
    for it in root.iter("{*}infoTable"):
        value_raw = int(_text(it, "{*}value"))
        rows.append(
            [
                _text(it, "{*}nameOfIssuer"),
                _text(it, "{*}titleOfClass"),
                _text(it, "{*}cusip"),
                value_raw,
                value_raw * mult,
                float(_text(it, "{*}shrsOrPrnAmt/{*}sshPrnamt")),
                _text(it, "{*}shrsOrPrnAmt/{*}sshPrnamtType"),
                _text(it, "{*}putCall"),
            ]
        )
    df = pd.DataFrame(rows, columns=HOLDINGS_RAW_13F)
    return df.astype({"value_raw": "int64", "value_usd": "int64", "shares": "float64"})


def equity_rows_13f(raw: pd.DataFrame) -> pd.DataFrame:
    """Convention 4.2: `sshPrnamtType` = SH and no `putCall`."""
    return raw[(raw["ssh_type"] == "SH") & (raw["put_call"].fillna("") == "")]


def aggregate_book(rows: pd.DataFrame, value: str, shares: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convention 4.3: upper-case CUSIPs, drop any not 9 alphanumeric characters, sum by CUSIP.

    Returns (cusip, name, value_usd, shares sorted by cusip; the dropped rows).
    """
    r = rows.assign(cusip=rows["cusip"].fillna("").astype(str).str.strip().str.upper())
    ok = r["cusip"].str.match(_CUSIP_RE)
    g = r[ok].groupby("cusip", sort=True)
    book = pd.DataFrame(
        {"name": g["name"].first(), "value_usd": g[value].sum(), "shares": g[shares].sum()}
    ).reset_index()
    return book, r[~ok]


def select_13f_filings(filings: pd.DataFrame, period: str) -> tuple[pd.Series | None, list[pd.Series]]:
    """Convention 4.4 for 1 period: (filing the book starts from, NEW HOLDINGS amendments appended)."""
    f = filings[filings["period_date"] == period].sort_values(["filing_date", "accession"], kind="mergesort")
    amend = f["amendment_type"].fillna("")
    originals = f[f["form"] == "13F-HR"]
    restated = f[(f["form"] == "13F-HR/A") & (amend == "RESTATEMENT")]
    if len(restated):
        base = restated.iloc[-1]
    elif len(originals):
        base = originals.iloc[-1]
    else:
        return None, []
    new = f[(f["form"] == "13F-HR/A") & (amend == "NEW HOLDINGS")]
    after = [r for _, r in new.iterrows() if (r["filing_date"], r["accession"]) > (base["filing_date"], base["accession"])]
    return base, after


def resolve_13f_books(filings: pd.DataFrame, tables: dict[str, pd.DataFrame], dates: list[date]) -> pd.DataFrame:
    """HOLDINGS for every date in `dates` that has a filing. `tables` is keyed by accession."""
    out = []
    for d in dates:
        period = str(d)
        base, after = select_13f_filings(filings, period)
        if base is None:
            continue
        rows = pd.concat([equity_rows_13f(tables[r["accession"]]) for r in [base, *after]], ignore_index=True)
        book, _ = aggregate_book(rows, "value_usd", "shares")
        book.insert(0, "period_date", period)
        book.insert(0, "entity", base["entity"])
        out.append(book)
    if not out:
        return pd.DataFrame(columns=HOLDINGS)
    return pd.concat(out, ignore_index=True)[HOLDINGS]


def units_check(book: pd.DataFrame) -> float:
    """Median implied price value_usd / shares over rows with shares > 0."""
    b = book[book["shares"] > 0]
    return float((b["value_usd"] / b["shares"]).median())


# ---------------------------------------------------------------- N-PORT


def list_nport_filings(client: EdgarClient, series_id: str) -> pd.DataFrame:
    """FILINGS_NPORT for form NPORT-P from the series atom feed, paged with `&start=` in steps of 100.

    `entity` and `period_date` are blank; the caller fills them (period from `repPdDate`).
    """
    rows, start = [], 0
    while True:
        url = NPORT_FEED.format(series_id=series_id) + (f"&start={start}" if start else "")
        root = etree.fromstring(client.get_bytes(url), _PARSER)
        entries = list(root.iter("{*}entry"))
        if not entries:
            break
        for e in entries:
            if _text(e, "{*}content/{*}filing-type") != "NPORT-P":
                continue
            rows.append(["", series_id, _text(e, "{*}content/{*}accession-number"),
                         _text(e, "{*}content/{*}filing-date"), ""])
        start += len(entries)
    df = pd.DataFrame(rows, columns=FILINGS_NPORT)
    return df.sort_values(["filing_date", "accession"], kind="mergesort").reset_index(drop=True)


def parse_nport(xml: bytes) -> tuple[dict, pd.DataFrame]:
    """(header with seriesId and repPdDate, HOLDINGS_RAW_NPORT with entity and accession blank)."""
    root = etree.fromstring(xml, _PARSER)
    header = {
        "seriesId": next((el.text or "").strip() for el in root.iter("{*}seriesId")),
        "repPdDate": next((el.text or "").strip() for el in root.iter("{*}repPdDate")),
    }
    rows = []
    for it in root.iter("{*}invstOrSec"):
        cusip = _text(it, "{*}cusip")
        if cusip == "000000000":
            cusip = ""
        isin = it.find("{*}identifiers/{*}isin")
        rows.append(
            [
                "", "", header["repPdDate"],
                _text(it, "{*}name"),
                _text(it, "{*}title"),
                cusip,
                "" if isin is None else isin.get("value", "").strip(),
                float(_text(it, "{*}balance")),
                _text(it, "{*}units"),
                float(_text(it, "{*}valUSD")),
                float(_text(it, "{*}pctVal")),
                _text(it, "{*}assetCat"),
                _text(it, "{*}issuerCat"),
                _text(it, "{*}invCountry"),
            ]
        )
    return header, pd.DataFrame(rows, columns=HOLDINGS_RAW_NPORT)


def equity_rows_nport(raw: pd.DataFrame) -> pd.DataFrame:
    """Convention 4.2: `assetCat` = EC and `units` = NS, then rows with a blank CUSIP dropped."""
    r = raw[(raw["asset_cat"] == "EC") & (raw["units"] == "NS")]
    return r[r["cusip"].fillna("").astype(str).str.strip() != ""]


def select_nport_filing(filings: pd.DataFrame, period: str) -> pd.Series | None:
    """Convention 4.4: the latest NPORT-P by filing date for the period."""
    f = filings[filings["period_date"] == period].sort_values(["filing_date", "accession"], kind="mergesort")
    return None if f.empty else f.iloc[-1]


def resolve_nport_books(filings: pd.DataFrame, raw: pd.DataFrame, dates: list[date]) -> pd.DataFrame:
    """HOLDINGS for every date in `dates` that has an NPORT-P; periods outside `dates` are ignored."""
    out = []
    for d in dates:
        period = str(d)
        f = select_nport_filing(filings, period)
        if f is None:
            continue
        rows = equity_rows_nport(raw[raw["accession"] == f["accession"]])
        book, _ = aggregate_book(rows, "val_usd", "balance")
        book.insert(0, "period_date", period)
        book.insert(0, "entity", f["entity"])
        out.append(book)
    if not out:
        return pd.DataFrame(columns=HOLDINGS)
    return pd.concat(out, ignore_index=True)[HOLDINGS]
