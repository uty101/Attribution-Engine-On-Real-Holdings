"""The only network code in the repo (rule 8).

    python scripts/pull_data.py --stage fixtures
    python scripts/pull_data.py --stage edgar
    python scripts/pull_data.py --stage figi
    python scripts/pull_data.py --stage sec
    python scripts/pull_data.py --stage sec --overrides-only
    python scripts/pull_data.py --stage french
    python scripts/pull_data.py --stage prices
    python scripts/pull_data.py --stage prices --new-only
    python scripts/pull_data.py --stage navret
    python scripts/pull_data.py --stage figi2
    python scripts/pull_data.py --holdings <path> --benchmark <path>

Every stage but `fixtures` writes under data/raw/ and updates data/raw/MANIFEST.json.
`--holdings` writes only under data/extra/ (gitignored) and leaves the manifest alone.
`--stage figi` runs before `--stage sec`, which needs the OpenFIGI tickers.

Reads SEC_USER_AGENT from the environment; stops if it is unset (rule 15). Reads the
optional OPENFIGI_API_KEY from the environment.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import platform
import re
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import lxml
import numpy
import pandas as pd
import pyarrow
import requests
import yfinance
import yfinance.shared
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import run_all  # noqa: E402  (scripts/ is sys.path[0] when this file runs)
from attrib.config import load_config  # noqa: E402
from attrib import load_prices_dir, load_security_map, read_holdings  # noqa: E402
from attrib.mapping import (  # noqa: E402
    FALLBACK,
    build_security_map,
    cik_override_check,
    judge_results,
    load_company_tickers,
    norm_ticker,
    parse_siccodes12,
    security_map_from_dir,
    us_isin,
)  # noqa: E402
from attrib.edgar import (  # noqa: E402
    HOLDINGS_RAW_NPORT,
    NPORT_RETURNS,
    EdgarClient,
    filing_base_url,
    find_infotable_name,
    holdings_dates,
    latest_monthly_returns,
    list_13f_filings,
    list_nport_filings,
    parse_nport,
    valid_isin,
)

FIXTURES = ROOT / "tests" / "fixtures"
RAW = ROOT / "data" / "raw"
MANIFEST = RAW / "MANIFEST.json"

# instructions/01_section_1.md, D 1.5: NPORT-P filings downloaded by filing date
NPORT_FILED_FROM = "2019-04-01"
NPORT_FILED_TO = "2026-09-30"

# instructions/01_section_1.md, D 1.3: the 2 Akre fixtures
AKRE_DOLLARS = ("2023-06-30", "0001112520-23-000013")
AKRE_THOUSANDS_PERIOD = "2022-06-30"
# instructions/01_section_1.md, D 1.4 and B OPEN-07: the IVV fixture period
IVV_PERIOD = "2023-06-30"
MF_TICKERS_URL = "https://www.sec.gov/files/company_tickers_mf.json"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
OPENFIGI_URL = "https://api.openfigi.com/v3/mapping"
OVERRIDES = ROOT / "data" / "manual" / "overrides.csv"
CLASS_PAGE_URL = (
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={class_id}&type=NPORT-P&dateb=&owner=include&count=1"
)
# instructions/02b_section_2_completion.md, step 2.1b: fund N-PORT filings by filing date
NAVRET_FILED_FROM = "2019-11-01"
NAVRET_FILED_TO = "2026-12-31"
NAVRET_SERIES = [
    "entity", "nav_ticker", "cik", "series_id", "class_id", "class_name", "found_by", "series_classes", "etf_class_ids",
]

# instructions/02_section_2.md, C 2.1
OPENFIGI_MAPPING = [
    "sec_id", "id_type", "status", "result_rank", "figi", "composite_figi", "ticker", "name", "exch_code",
    "market_sector", "security_type",
]
SIC_CSV = ["cik", "name", "sic", "sic_description"]
FRENCH_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
FRENCH_FILES = {"F-F_Research_Data_5_Factors_2x3_CSV.zip": "ff5_monthly.csv", "F-F_Momentum_Factor_CSV.zip": "mom_monthly.csv"}
# Not SEC_USER_AGENT: that header carries the owner's email and is for EDGAR only (rule 15)
FRENCH_USER_AGENT = "attrib-data-pull"
# instructions/02_section_2.md, B: yfinance batches of 50 tickers in sorted order
PRICE_BATCH = 50


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write_bytes(path: Path, b: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b)


def write_json(path: Path, obj) -> None:
    write_bytes(path, (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def submission_type(xml: bytes) -> str:
    """The form as filed (NPORT-P or NPORT-P/A), from the `submissionType` header element."""
    root = etree.fromstring(xml, etree.XMLParser(huge_tree=True, resolve_entities=False))
    return next(((el.text or "").strip() for el in root.iter("{*}submissionType")), "")


def write_csv(df: pd.DataFrame, path: Path) -> None:
    """Rule 9 as amended by instructions/01b: %.17g floats, LF, UTF-8, no index."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, float_format="%.17g", lineterminator="\n", encoding="utf-8")


def client_from_env(cfg) -> EdgarClient:
    ua = os.environ.get("SEC_USER_AGENT", "").strip()
    if not ua:
        sys.exit("SEC_USER_AGENT is unset: stop under rule 4 (kickoff rule 15)")
    e = cfg.edgar
    return EdgarClient(ua, e.min_interval_s, e.retries, e.backoff_s, e.timeout_s)


def infotable_url(client: EdgarClient, cik: int, accession: str) -> str:
    base = filing_base_url(cik, accession)
    return f"{base}/{find_infotable_name(client.get_json(f'{base}/index.json'))}"


class OpenFigiClient:
    """POST to the OpenFIGI mapping API under the EDGAR failure rules (instructions/02, B).

    Timeout `edgar.timeout_s`; retries and backoff from `[edgar]` on HTTP 429, 5xx, timeouts and
    connection errors; any other non-200 stops at once. At least `min_interval` between requests,
    counted when a request is sent. `X-OPENFIGI-APIKEY` only when a key is given.
    """

    def __init__(self, api_key: str, min_interval: float, retries: int, backoff, timeout: float) -> None:
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-OPENFIGI-APIKEY"] = api_key
        self.min_interval, self.retries, self.backoff, self.timeout = min_interval, retries, list(backoff), timeout
        self.session = requests.Session()
        self._last_sent: float | None = None
        self.n_retries = 0

    def _send(self, jobs: list[dict]):
        if self._last_sent is not None:
            wait = self.min_interval - (time.monotonic() - self._last_sent)
            if wait > 0:
                time.sleep(wait)
        self._last_sent = time.monotonic()
        return self.session.post(OPENFIGI_URL, json=jobs, headers=self.headers, timeout=self.timeout)

    def map(self, jobs: list[dict]) -> list[dict]:
        for attempt in range(self.retries + 1):
            try:
                resp = self._send(jobs)
            except (requests.Timeout, requests.ConnectionError) as exc:
                failure = f"{type(exc).__name__} ({exc})"
            else:
                if resp.status_code == 200:
                    out = resp.json()
                    if len(out) != len(jobs):
                        sys.exit(f"stop under rule 4: OpenFIGI returned {len(out)} results for {len(jobs)} jobs")
                    return out
                if resp.status_code != 429 and not 500 <= resp.status_code <= 599:
                    sys.exit(f"stop under rule 4: OpenFIGI HTTP {resp.status_code}: {resp.text[:500]}")
                failure = f"HTTP {resp.status_code}"
            if attempt == self.retries:
                sys.exit(f"stop under rule 4: OpenFIGI {failure} after {self.retries} retries")
            self.n_retries += 1
            print(f"  OpenFIGI {failure}, retry {attempt + 1} after {self.backoff[attempt]} s", flush=True)
            time.sleep(self.backoff[attempt])
        raise AssertionError("unreachable")


def book_sec_ids(cfg) -> list[str]:
    """Every distinct `sec_id` in any of the books in H, rebuilt from data/raw/ (instructions/02, B)."""
    H = holdings_dates(cfg)
    failures: list[str] = []
    ids: set[str] = set()
    for eid, e in cfg.entities.items():
        if e.type == "fund":
            book, _ = run_all.fund_books(eid, H, cfg.edgar.implied_price_lo, cfg.edgar.implied_price_hi, failures)
        else:
            book, _ = run_all.benchmark_books(eid, H, failures)
        ids |= set(book["sec_id"])
    if failures:
        sys.exit("stop under rule 4: section 1 checks failed:\n" + "\n".join(failures))
    return sorted(ids)


def id_type(sec_id: str) -> str:
    """`cusip` for a 9-character `sec_id`, `isin` for a 12-character one (CLAUDE.md amendment 8)."""
    return {9: "cusip", 12: "isin"}[len(sec_id)]


def stage_figi(cfg) -> None:
    """data/raw/openfigi/mapping.csv: every OpenFIGI result for every `sec_id`, ranked (instructions/02, C 2.1)."""
    key = os.environ.get("OPENFIGI_API_KEY", "").strip()
    o, e = cfg.openfigi, cfg.edgar
    batch, interval = (o.batch_with_key, o.min_interval_with_key_s) if key else (o.batch_no_key, o.min_interval_no_key_s)
    client = OpenFigiClient(key, interval, e.retries, e.backoff_s, e.timeout_s)
    ids = book_sec_ids(cfg)
    print(f"{len(ids)} sec_ids, batches of {batch} every {interval} s ({'with' if key else 'no'} API key)")
    rows = []
    for i in range(0, len(ids), batch):
        chunk = ids[i : i + batch]
        jobs = [{"idType": f"ID_{id_type(s).upper()}", "idValue": s, "exchCode": "US"} for s in chunk]
        for sid, res in zip(chunk, client.map(jobs)):
            data = res.get("data") or []
            status = "ok" if "data" in res else res.get("warning") or res.get("error") or ""
            if not data:
                rows.append([sid, id_type(sid), status, None, *[""] * 7])
            for rank, d in enumerate(data, start=1):
                rows.append([
                    sid, id_type(sid), status, rank, d.get("figi") or "", d.get("compositeFIGI") or "",
                    d.get("ticker") or "", d.get("name") or "", d.get("exchCode") or "",
                    d.get("marketSector") or "", d.get("securityType") or "",
                ])
        if (i // batch) % 20 == 0:
            print(f"  {i + len(chunk)} / {len(ids)}", flush=True)
    df = pd.DataFrame(rows, columns=OPENFIGI_MAPPING).astype({"result_rank": "Int64"})
    write_csv(df, RAW / "openfigi" / "mapping.csv")
    print(df["status"].value_counts().to_string())
    print(f"{client.n_retries} retries")


def holding_names(cfg) -> dict[str, str]:
    """Per sec_id, the name on the book row with the largest weight (instructions/02b, step 2.1c)."""
    H = holdings_dates(cfg)
    failures: list[str] = []
    books = []
    for eid, e in cfg.entities.items():
        if e.type == "fund":
            book, _ = run_all.fund_books(eid, H, cfg.edgar.implied_price_lo, cfg.edgar.implied_price_hi, failures)
        else:
            book, _ = run_all.benchmark_books(eid, H, failures)
        books.append(book)
    b = pd.concat(books, ignore_index=True).astype({"value_usd": float})
    b["weight"] = b["value_usd"] / b.groupby(["entity", "period_date"])["value_usd"].transform("sum")
    b = b.sort_values(["sec_id", "weight", "entity", "period_date"], ascending=[True, False, True, True],
                      kind="mergesort").drop_duplicates("sec_id")
    return dict(zip(b["sec_id"], b["name"]))


def isin_candidates(sec_id: str, nport: pd.DataFrame) -> list[str]:
    """Pass 2's ISINs for a sec_id (instructions/02b, step 2.1c): (i) the valid ISINs of N-PORT rows
    whose cusip or other_id equals it; (ii) else, for a CUSIP starting with a digit, the US ISIN.
    An ISIN sec_id is its own ISIN."""
    if len(sec_id) == 12:
        return [sec_id]
    hit = nport[(nport["cusip"] == sec_id) | (nport["other_id"] == sec_id)]
    found = sorted({i for i in hit["isin"] if valid_isin(i)})
    if found:
        return found
    return [us_isin(sec_id)] if sec_id[0].isdigit() else []


def _figi_results(res: dict) -> tuple[list[dict], str]:
    data = res.get("data") or []
    out = [{"ticker": d.get("ticker") or "", "name": d.get("name") or "", "exch_code": d.get("exchCode") or "",
            "market_sector": d.get("marketSector") or "", "security_type": d.get("securityType") or ""} for d in data]
    return out, res.get("warning") or res.get("error") or "no result"


def stage_figi2(cfg) -> None:
    """data/raw/openfigi/fallback.csv: passes 2 to 4 for every sec_id with no pass-1 equity result
    (instructions/02b, step 2.1c). Every result seen is written, accepted or not."""
    key = os.environ.get("OPENFIGI_API_KEY", "").strip()
    o, e = cfg.openfigi, cfg.edgar
    batch, interval = (o.batch_with_key, o.min_interval_with_key_s) if key else (o.batch_no_key, o.min_interval_no_key_s)
    client = OpenFigiClient(key, interval, e.retries, e.backoff_s, e.timeout_s)

    figi = pd.read_csv(RAW / "openfigi" / "mapping.csv", dtype=str, keep_default_na=False)
    has_eq = set(figi.loc[figi["market_sector"] == "Equity", "sec_id"])
    targets = sorted(set(figi["sec_id"]) - has_eq)
    names = holding_names(cfg)
    nport = pd.concat(
        [pd.read_csv(RAW / "edgar" / "nport" / f"holdings_{eid}.csv", dtype=str, keep_default_na=False)
         for eid, ent in cfg.entities.items() if ent.type == "benchmark"],
        ignore_index=True,
    )
    isins = {s: isin_candidates(s, nport) for s in targets}
    print(f"{len(targets)} sec_ids without a pass-1 equity result; {sum(bool(v) for v in isins.values())} have an ISIN")
    rows: list[list] = []
    accepted: set[str] = set()

    def run_figi(pass_no: int, queries: list[tuple[str, str, dict]]) -> None:
        """queries: (sec_id, query_value, job), in order; a sec_id's later queries are skipped once 1 is accepted."""
        results = []
        for i in range(0, len(queries), batch):
            chunk = queries[i : i + batch]
            results += client.map([q[2] for q in chunk])
        for (sid, value, job), res in zip(queries, results):
            if sid in accepted:
                continue
            found, why = _figi_results(res)
            out = judge_results(sid, pass_no, job["idType"], value, found, names[sid], why)
            rows.extend(out)
            if any(r[10] for r in out):
                accepted.add(sid)

    q2 = [(s, i, {"idType": "ID_ISIN", "idValue": i, "exchCode": "US"}) for s in targets for i in isins[s]]
    run_figi(2, q2)
    print(f"pass 2: {len(q2)} queries, {len(accepted)} accepted", flush=True)
    n = len(accepted)
    q3 = [(s, s, {"idType": f"ID_{id_type(s).upper()}", "idValue": s}) for s in targets if s not in accepted]
    run_figi(3, q3)
    print(f"pass 3: {len(q3)} queries, {len(accepted) - n} accepted", flush=True)
    n = len(accepted)
    q4 = [(s, i) for s in targets if s not in accepted for i in isins[s]]
    for k, (sid, isin) in enumerate(q4):
        if sid in accepted:
            continue
        try:
            quotes = yfinance.Search(isin, max_results=8).quotes
        except Exception as exc:  # noqa: BLE001 - a failed search is a pull failure
            sys.exit(f"stop under rule 4: yfinance.Search({isin!r}) raised {type(exc).__name__}: {exc}")
        found = [{"ticker": q.get("symbol") or "", "name": q.get("longname") or q.get("shortname") or "",
                  "exch_code": q.get("exchange") or "", "market_sector": "", "security_type": q.get("quoteType") or ""}
                 for q in quotes]
        out = judge_results(sid, 4, "yahoo_search", isin, found, names[sid])
        rows.extend(out)
        if any(r[10] for r in out):
            accepted.add(sid)
        if k % 50 == 0:
            print(f"  pass 4: {k + 1} / {len(q4)}", flush=True)
    print(f"pass 4: {len(q4)} queries, {len(accepted) - n} accepted; {len(targets) - len(accepted)} still unmatched")
    df = pd.DataFrame(rows, columns=FALLBACK).astype({"rank": "Int64"})
    df = df.sort_values(["sec_id", "pass", "query_value", "rank"], kind="mergesort")
    write_csv(df, RAW / "openfigi" / "fallback.csv")


def stage_sec(cfg, client: EdgarClient) -> None:
    """company_tickers.json as downloaded, and sic.csv for every CIK reachable by ticker -> CIK.

    The tickers are every OpenFIGI equity result's ticker plus every override `ticker` value;
    override `cik` values are added as CIKs.
    """
    b = client.get_bytes(TICKERS_URL)
    write_bytes(RAW / "sec" / "company_tickers.json", b)
    by_ticker: dict[str, set[int]] = {}
    for r in json.loads(b).values():
        by_ticker.setdefault(norm_ticker(r["ticker"]), set()).add(int(r["cik_str"]))

    figi = pd.read_csv(RAW / "openfigi" / "mapping.csv", dtype=str, keep_default_na=False)
    ov = pd.read_csv(OVERRIDES, dtype=str, keep_default_na=False)
    tickers = set(figi.loc[figi["market_sector"] == "Equity", "ticker"]) | set(ov.loc[ov["kind"] == "ticker", "value"])
    fb_path = RAW / "openfigi" / "fallback.csv"
    if fb_path.exists():  # instructions/02b, step 2.1c: tickers of accepted fallback results
        fb = pd.read_csv(fb_path, dtype=str, keep_default_na=False)
        tickers |= set(fb.loc[fb["accepted"] == "True", "ticker"])
    tickers.discard("")
    ciks = {c for t in tickers for c in by_ticker.get(norm_ticker(t), ())}
    ciks |= {int(v) for v in ov.loc[ov["kind"] == "cik", "value"]}
    print(f"{len(tickers)} tickers, {len(ciks)} CIKs reachable")

    rows = []
    for n, cik in enumerate(sorted(ciks)):
        sub = client.get_json(SUBMISSIONS_URL.format(cik=cik))
        rows.append([cik, sub.get("name") or "", sub.get("sic") or "", sub.get("sicDescription") or ""])
        if n % 250 == 0:
            print(f"  {n + 1} / {len(ciks)}", flush=True)
    write_csv(pd.DataFrame(rows, columns=SIC_CSV), RAW / "sec" / "sic.csv")


def stage_sec_overrides(cfg, client: EdgarClient) -> None:
    """`--stage sec --overrides-only` (instructions/03, step 3.0): the submissions JSON of every
    override CIK, and of every CIK an override ticker reaches in the committed company_tickers.json
    that sic.csv lacks. Those rows are written into sic.csv; every other row is left as it is, and
    company_tickers.json is not downloaded again. Then the `cik` override name check goes to
    data/raw/sec/cik_override_check.csv.
    """
    by_ticker: dict[str, set[int]] = {}
    for r in json.loads((RAW / "sec" / "company_tickers.json").read_bytes()).values():
        by_ticker.setdefault(norm_ticker(r["ticker"]), set()).add(int(r["cik_str"]))
    ov = pd.read_csv(OVERRIDES, dtype=str, keep_default_na=False)
    sic = pd.read_csv(RAW / "sec" / "sic.csv", dtype=str, keep_default_na=False)
    have = set(sic["cik"].astype(int))
    override_ciks = {int(v) for v in ov.loc[ov["kind"] == "cik", "value"]}
    ticker_ciks = {c for t in ov.loc[ov["kind"] == "ticker", "value"] for c in by_ticker.get(norm_ticker(t), ())}
    fetch = sorted(override_ciks | (ticker_ciks - have))
    print(f"{len(override_ciks)} override CIKs, {len(ticker_ciks - have)} new CIKs from override tickers")
    rows = []
    for cik in fetch:
        sub = client.get_json(SUBMISSIONS_URL.format(cik=cik))
        rows.append([str(cik), sub.get("name") or "", str(sub.get("sic") or ""), sub.get("sicDescription") or ""])
    new = pd.DataFrame(rows, columns=SIC_CSV)
    prev = sic.set_index("cik")
    for _, r in new.iterrows():
        if r["cik"] in prev.index and tuple(prev.loc[r["cik"], ["name", "sic"]]) != (r["name"], r["sic"]):
            print(f"  sic.csv row changed for CIK {r['cik']}: {tuple(prev.loc[r['cik'], ['name', 'sic']])} -> "
                  f"{(r['name'], r['sic'])}")
    old = sic[~sic["cik"].astype(int).isin(fetch)]
    out = pd.concat([old, new], ignore_index=True)
    out = out.assign(_k=out["cik"].astype(int)).sort_values("_k", kind="mergesort").drop(columns="_k")
    write_csv(out[SIC_CSV], RAW / "sec" / "sic.csv")
    write_csv(cik_override_check(ov, out), RAW / "sec" / "cik_override_check.csv")


def monthly_block(text: str) -> str:
    """The monthly block of a French CSV: its column header line (starting with `,`) and the
    YYYYMM rows under it, up to the first line that is not one. Lines kept as filed, LF endings."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(","))
    out = [lines[start]]
    for line in lines[start + 1 :]:
        if not re.match(r"^\s*\d{6}\s*,", line):
            break
        out.append(line)
    return "\n".join(out) + "\n"


def unzip_one(b: bytes) -> tuple[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        names = z.namelist()
        if len(names) != 1:
            sys.exit(f"stop under rule 4: expected 1 file in the zip, found {names}")
        return names[0], z.read(names[0])


def stage_french(cfg) -> None:
    """Kickoff 3.2: the monthly blocks of the 5-factor and momentum files, and Siccodes12.txt."""
    e = cfg.edgar
    client = EdgarClient(FRENCH_USER_AGENT, e.min_interval_s, e.retries, e.backoff_s, e.timeout_s)
    for zname, out in FRENCH_FILES.items():
        name, b = unzip_one(client.get_bytes(FRENCH_URL + zname))
        block = monthly_block(b.decode("latin-1"))
        write_bytes(RAW / "french" / out, block.encode("utf-8"))
        rows = block.splitlines()
        print(f"{zname} -> {name} -> {out}: header {rows[0]!r}, {len(rows) - 1} months, {rows[1][:6]} to {rows[-1][:6]}")
    name, b = unzip_one(client.get_bytes(FRENCH_URL + "Siccodes12.zip"))
    write_bytes(RAW / "french" / "Siccodes12.txt", b)
    print(f"Siccodes12.zip -> {name} -> Siccodes12.txt, {len(b)} bytes")


def yf_close(tickers: list[str], cfg) -> tuple[pd.DataFrame, dict]:
    """1 yfinance `download` call for `tickers` (instructions/02, B), retried once if it raises.

    Returns the adjusted close (`auto_adjust=True` puts it in `Close`), 1 column per ticker, and
    yfinance's per-ticker error messages.
    """
    yf = yfinance

    for attempt in (1, 2):
        try:
            df = yf.download(
                tickers, start=str(cfg.sample.price_start), end=str(cfg.sample.price_end_exclusive),
                auto_adjust=True, actions=False, threads=False, progress=False,
            )
            break
        except Exception as exc:  # noqa: BLE001 - any failure of the batch counts (instructions/02, B)
            print(f"batch {tickers[0]}..{tickers[-1]} raised on try {attempt}: {type(exc).__name__}: {exc}")
            if attempt == 2:
                sys.exit("stop under rule 4: a yfinance batch raised twice")
    errors = dict(yfinance.shared._ERRORS)
    close = df["Close"] if df is not None and not df.empty else pd.DataFrame()
    return close, errors


def _series(close: pd.DataFrame, t: str) -> pd.Series:
    if t not in close.columns:
        return pd.Series(dtype="float64")
    s = close[t].dropna().astype("float64")
    s.index = pd.DatetimeIndex(s.index).tz_localize(None).normalize()
    return s.rename(t)


def stage_prices(cfg) -> None:
    """adjclose.parquet for every yf_ticker in SECURITY_MAP, missing.csv, nav_adjclose.csv (kickoff 3.2)."""
    smap = security_map_from_dir(ROOT / "data")
    smap = smap[smap["yf_ticker"] != ""]
    sec_ids = smap.groupby("yf_ticker")["sec_id"].agg(lambda s: ";".join(sorted(s)))
    tickers = sorted(sec_ids.index)
    print(f"{len(tickers)} yf_tickers in batches of {PRICE_BATCH}")
    got, missing = [], []
    for i in range(0, len(tickers), PRICE_BATCH):
        batch = tickers[i : i + PRICE_BATCH]
        close, errors = yf_close(batch, cfg)
        for t in batch:
            s = _series(close, t)
            if s.empty:
                missing.append(t)
                print(f"  no rows: {t} ({errors.get(t, 'no yfinance error recorded')})")
            else:
                got.append(s)
        print(f"  {i + len(batch)} / {len(tickers)}", flush=True)
    panel = pd.concat(got, axis=1).sort_index()
    panel = panel[sorted(panel.columns)].astype("float64")
    panel.index.name = "date"
    path = RAW / "prices" / "adjclose.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(path, engine="pyarrow", index=True)
    write_csv(pd.DataFrame({"yf_ticker": missing, "sec_ids": [sec_ids[t] for t in missing]}),
              RAW / "prices" / "missing.csv")
    print(f"panel {panel.shape}, {panel.index[0].date()} to {panel.index[-1].date()}, {len(missing)} missing")

    # instructions/02b, step 2.3b: columns JENIX, POLIX, IVV, IWF, AKRE; AKRIX (nav_source nport) is not requested
    ents = cfg.entities.values()
    nav_tickers = [e.nav_ticker for e in ents if e.type == "fund" and e.nav_source == "yfinance"]
    nav_tickers += [e.etf_ticker for e in ents if e.type == "benchmark"]
    nav_tickers += [e.etf_successor for e in ents if e.type == "fund" and e.etf_successor]
    close, errors = yf_close(nav_tickers, cfg)
    cols = [_series(close, t) for t in nav_tickers]
    empty = [t for t, s in zip(nav_tickers, cols) if s.empty]
    if empty:
        sys.exit(f"stop under rule 4: yfinance returned no data for {empty}: {errors}")
    nav = pd.concat(cols, axis=1).sort_index()[nav_tickers]
    nav.index = nav.index.strftime("%Y-%m-%d")
    nav.index.name = "date"
    write_csv(nav.reset_index(), RAW / "prices" / "nav_adjclose.csv")
    print(nav.apply(lambda s: pd.Series({"first": s.first_valid_index(), "last": s.last_valid_index(),
                                         "n": s.notna().sum()})).to_string())


def stage_prices_new(cfg) -> None:
    """`--stage prices --new-only` (instructions/03, step 3.0): every yf_ticker in SECURITY_MAP that
    is not already a column of adjclose.parquet is pulled and merged in as a new column; existing
    columns are left untouched, because a full re-pull would restate adjusted closes as of a new
    date. nav_adjclose.csv is not touched. missing.csv lists every SECURITY_MAP yf_ticker with no
    column afterwards."""
    smap = security_map_from_dir(ROOT / "data")
    smap = smap[smap["yf_ticker"] != ""]
    sec_ids = smap.groupby("yf_ticker")["sec_id"].agg(lambda s: ";".join(sorted(s)))
    path = RAW / "prices" / "adjclose.parquet"
    panel = pd.read_parquet(path)
    tickers = sorted(set(sec_ids.index) - set(panel.columns))
    print(f"{len(tickers)} new yf_tickers in batches of {PRICE_BATCH}: {tickers}")
    got = []
    for i in range(0, len(tickers), PRICE_BATCH):
        batch = tickers[i : i + PRICE_BATCH]
        close, errors = yf_close(batch, cfg)
        for t in batch:
            s = _series(close, t)
            if s.empty:
                print(f"  no rows: {t} ({errors.get(t, 'no yfinance error recorded')})")
            else:
                got.append(s)
    n_dates = len(panel.index)
    if got:
        merged = panel.join(pd.concat(got, axis=1), how="outer").sort_index()
        merged.index.name = "date"
        merged = merged[sorted(merged.columns)].astype("float64")
        if not merged.loc[panel.index, panel.columns].equals(panel):
            sys.exit("stop under rule 4: merging new columns changed an existing column")
        panel = merged
        panel.to_parquet(path, engine="pyarrow", index=True)
    missing = sorted(set(sec_ids.index) - set(panel.columns))
    write_csv(pd.DataFrame({"yf_ticker": missing, "sec_ids": [sec_ids[t] for t in missing]}),
              RAW / "prices" / "missing.csv")
    print(f"panel {panel.shape} ({len(panel.index) - n_dates} new dates), {len(got)} added, {len(missing)} missing")


def class_name(client: EdgarClient, class_id: str) -> tuple[str, dict]:
    """The class name EDGAR shows on the class's company page ("Class/Contract: C... <name>"), and
    the page's url and sha256 for the manifest (instructions/02c, Section B)."""
    url = CLASS_PAGE_URL.format(class_id=class_id)
    b = client.get_bytes(url)
    m = re.search(rf"Class/Contract:\s*(?:<[^>]+>\s*)*{class_id}\s*(?:<[^>]+>|&nbsp;|\s)*([^<&]+)", b.decode("latin-1"))
    return (m.group(1).strip() if m else ""), {"url": url, "sha256": sha256(b), "form": "class page (HTML)"}


def stage_navret(cfg, client: EdgarClient) -> dict:
    """Each fund's N-PORT B.5 monthly total returns (instructions/02b, step 2.1b).

    Series and class come from the committed company_tickers_mf.json. Writes
    data/raw/edgar/nport_returns/{fund}_monthly.csv and data/raw/edgar/nport_returns/series_resolved.csv,
    and returns the url, sha256 and form of every N-PORT XML read, for the manifest.
    """
    mf = json.loads((RAW / "sec" / "company_tickers_mf.json").read_text(encoding="utf-8"))
    rows_mf = [dict(zip(mf["fields"], r)) for r in mf["data"]]
    resolved, uncommitted = [], {}
    for eid, e in cfg.entities.items():
        if e.type != "fund":
            continue
        hits = [r for r in rows_mf if r["symbol"] == e.nav_ticker]
        if len(hits) != 1:
            sys.exit(f"stop under rule 4: {e.nav_ticker} has {len(hits)} rows in company_tickers_mf.json; "
                     "instructions/02b says to resolve it with EDGAR full-text search, which is not built")
        h = hits[0]
        series, cls = h["seriesId"], h["classId"]
        series_classes = sorted((r["classId"], r["symbol"]) for r in rows_mf if r["seriesId"] == series)
        etf = [c for c, s in series_classes if e.etf_successor and s == e.etf_successor]
        cname, page = class_name(client, cls)
        uncommitted[f"edgar/nport_returns/class_pages/{cls}.html"] = page
        resolved.append([eid, e.nav_ticker, h["cik"], series, cls, cname, "company_tickers_mf.json",
                         ";".join(f"{c}:{s}" for c, s in series_classes), ";".join(etf)])

        filings = list_nport_filings(client, series)
        out = []
        for _, f in filings.iterrows():
            if not NAVRET_FILED_FROM <= f["filing_date"] <= NAVRET_FILED_TO:
                continue
            url = f"{filing_base_url(h['cik'], f['accession'])}/primary_doc.xml"
            b = client.get_bytes(url)
            header, _, rets = parse_nport(b)
            if header["seriesId"] != series:
                sys.exit(f"stop under rule 4: {url} has seriesId {header['seriesId']}, expected {series}")
            uncommitted[f"edgar/nport_returns/{eid}/{header['repPdDate']}_{f['accession']}.xml"] = {
                "url": url, "sha256": sha256(b), "form": submission_type(b),
            }
            out.append(rets.assign(entity=eid, series_id=series, accession=f["accession"],
                                   filing_date=f["filing_date"], period_date=header["repPdDate"]))
        monthly = latest_monthly_returns(pd.concat(out, ignore_index=True))[NPORT_RETURNS]
        write_csv(monthly, RAW / "edgar" / "nport_returns" / f"{eid}_monthly.csv")
        own = monthly[monthly["class_id"] == cls]
        print(f"{eid}: {len(out)} N-PORT filings, {len(monthly)} class-months, {cls}: {own['month'].min()} to "
              f"{own['month'].max()} ({own['rtn_pct'].notna().sum()} months)", flush=True)
    res = pd.DataFrame(resolved, columns=NAVRET_SERIES)
    write_csv(res, RAW / "edgar" / "nport_returns" / "series_resolved.csv")
    print(res.to_string())
    return uncommitted


def resolve_series(mf: dict, ticker: str) -> dict:
    """The 1 row of company_tickers_mf.json for `ticker` (fields cik, seriesId, classId, symbol)."""
    hits = [dict(zip(mf["fields"], r)) for r in mf["data"] if r[mf["fields"].index("symbol")] == ticker]
    if len(hits) != 1:
        sys.exit(f"expected 1 company_tickers_mf.json row for {ticker}, found {hits}")
    return hits[0]


def stage_fixtures(cfg, client: EdgarClient) -> None:
    record: dict[str, dict] = {}
    cik = cfg.entities["akre"].cik

    def save(rel: str, url: str) -> None:
        b = client.get_bytes(url)
        write_bytes(FIXTURES / rel, b)
        record[rel] = {"url": url, "sha256": sha256(b)}
        print(f"{rel}  {len(b)} bytes")

    period, acc = AKRE_DOLLARS
    save(f"13f/akre/{period}_{acc}.xml", infotable_url(client, cik, acc))

    filings = list_13f_filings(client, cik)
    orig = filings[(filings["form"] == "13F-HR") & (filings["period_date"] == AKRE_THOUSANDS_PERIOD)]
    if len(orig) != 1:
        sys.exit(f"expected 1 original 13F-HR for {AKRE_THOUSANDS_PERIOD}, found:\n{orig.to_string()}")
    row = orig.iloc[0]
    print(orig.to_string())
    save(
        f"13f/akre/{AKRE_THOUSANDS_PERIOD}_{row['accession']}.xml",
        f"{filing_base_url(cik, row['accession'])}/{row['infotable_name']}",
    )

    ivv = resolve_series(client.get_json(MF_TICKERS_URL), cfg.entities["ivv"].etf_ticker)
    nport = list_nport_filings(client, ivv["seriesId"])
    for _, f in nport[nport["filing_date"] > IVV_PERIOD].iterrows():
        url = f"{filing_base_url(ivv['cik'], f['accession'])}/primary_doc.xml"
        b = client.get_bytes(url)
        header, _, _ = parse_nport(b)
        if header["repPdDate"] == IVV_PERIOD:
            rel = f"nport/ivv_{IVV_PERIOD}_{f['accession']}.xml"
            write_bytes(FIXTURES / rel, b)
            record[rel] = {"url": url, "sha256": sha256(b)}
            print(f"{rel}  {len(b)} bytes  header {header}")
            break
    else:
        sys.exit(f"no IVV NPORT-P with repPdDate {IVV_PERIOD}")

    path = FIXTURES / "FIXTURES.json"
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    existing.update(record)
    write_json(path, existing)


def stage_edgar(cfg, client: EdgarClient) -> dict:
    """Filings lists, 13F information tables and N-PORT holdings for all 5 entities.

    Returns the url, sha256 and form of every downloaded but uncommitted N-PORT XML, keyed by
    its path as if it were under data/raw/.
    """
    H = {str(d) for d in holdings_dates(cfg)}
    mf_bytes = client.get_bytes(MF_TICKERS_URL)
    write_bytes(RAW / "sec" / "company_tickers_mf.json", mf_bytes)
    mf = json.loads(mf_bytes)

    series = []
    for eid, e in cfg.entities.items():
        if e.type == "benchmark":
            r = resolve_series(mf, e.etf_ticker)
            series.append([eid, e.etf_ticker, r["cik"], r["seriesId"], r["classId"]])
    series = pd.DataFrame(series, columns=["entity", "ticker", "cik", "series_id", "class_id"])
    write_csv(series, RAW / "sec" / "series_resolved.csv")
    print(series.to_string())

    for eid, e in cfg.entities.items():
        if e.type != "fund":
            continue
        filings = list_13f_filings(client, e.cik).assign(entity=eid)
        write_csv(filings, RAW / "edgar" / "13f" / f"filings_{eid}.csv")
        need = filings[filings["period_date"].isin(H)]
        print(f"{eid}: {len(filings)} 13F filings, {len(need)} with period_date in H")
        for _, f in need.iterrows():
            if not f["infotable_name"]:
                sys.exit(f"stop under rule 4: no XML information table for\n{f.to_string()}")
            b = client.get_bytes(f"{filing_base_url(e.cik, f['accession'])}/{f['infotable_name']}")
            write_bytes(RAW / "edgar" / "13f" / eid / f"{f['period_date']}_{f['accession']}.xml", b)

    uncommitted = {}
    for _, sr in series.iterrows():
        eid = sr["entity"]
        filings = list_nport_filings(client, sr["series_id"]).assign(entity=eid)
        if filings.empty:
            sys.exit(
                f"stop under rule 4: the atom feed for {sr['series_id']} returned no NPORT-P entries. Options: "
                "(a) the EDGAR full-text search API; (b) the trust's submissions JSON filtered by "
                "downloading each NPORT-P header"
            )
        raws = []
        for i, f in filings.iterrows():
            if not NPORT_FILED_FROM <= f["filing_date"] <= NPORT_FILED_TO:
                continue
            url = f"{filing_base_url(sr['cik'], f['accession'])}/primary_doc.xml"
            b = client.get_bytes(url)
            header, raw, _ = parse_nport(b)
            if header["seriesId"] != sr["series_id"]:
                sys.exit(f"stop under rule 4: {url} has seriesId {header['seriesId']}, expected {sr['series_id']}")
            filings.loc[i, "period_date"] = header["repPdDate"]
            rel = f"edgar/nport/{eid}/{header['repPdDate']}_{f['accession']}.xml"
            uncommitted[rel] = {"url": url, "sha256": sha256(b), "form": submission_type(b)}
            if uncommitted[rel]["form"] != "NPORT-P":
                print(f"{eid}: {uncommitted[rel]['form']} {f['accession']} filed {f['filing_date']} "
                      f"for period {header['repPdDate']}")
            if header["repPdDate"] in H:
                raws.append(raw.assign(entity=eid, accession=f["accession"]))
        write_csv(filings, RAW / "edgar" / "nport" / f"filings_{eid}.csv")
        holdings = pd.concat(raws, ignore_index=True) if raws else pd.DataFrame(columns=HOLDINGS_RAW_NPORT)
        write_csv(holdings, RAW / "edgar" / "nport" / f"holdings_{eid}.csv")
        print(f"{eid}: {len(filings)} NPORT-P filings, {holdings['accession'].nunique()} with period_date in H")
    return uncommitted


EXTRA = ROOT / "data" / "extra"


def stage_holdings(cfg, holdings: str, benchmark: str, retry_missing: bool = False) -> None:
    """`--holdings <path> --benchmark <path>` (step 7.3; instructions/07, C.3): every sec_id of the 2
    files that is not in the data directory's SECURITY_MAP is mapped through OpenFIGI (pass 1, as
    `--stage figi`), ticker -> CIK on the committed company_tickers.json and CIK -> SIC from the
    EDGAR submissions JSON (for CIKs sic.csv lacks), with `build_security_map`; the rows go to
    data/extra/security_map_extra.csv. Every yf_ticker the 2 files need that has no price column
    is pulled as in `--stage prices` into data/extra/adjclose_extra.parquet, except those already
    listed in data/raw/prices/missing.csv, which `retry_missing` (`--retry-missing`) asks for again
    (instructions/08, A answer 4). data/extra/ is gitignored, and data/raw/ and its manifest are not
    touched."""
    ids = sorted(set(read_holdings(holdings)["sec_id"]) | set(read_holdings(benchmark)["sec_id"]))
    smap = load_security_map(ROOT / "data")
    new = [s for s in ids if s not in set(smap["sec_id"])]
    print(f"{len(ids)} sec_ids in the 2 files, {len(new)} not in the data directory: {new}")
    if new:
        key = os.environ.get("OPENFIGI_API_KEY", "").strip()
        o, e = cfg.openfigi, cfg.edgar
        batch, interval = (o.batch_with_key, o.min_interval_with_key_s) if key else (o.batch_no_key, o.min_interval_no_key_s)
        figi_client = OpenFigiClient(key, interval, e.retries, e.backoff_s, e.timeout_s)
        rows = []
        for i in range(0, len(new), batch):
            chunk = new[i : i + batch]
            jobs = [{"idType": f"ID_{id_type(s).upper()}", "idValue": s, "exchCode": "US"} for s in chunk]
            for sid, res in zip(chunk, figi_client.map(jobs)):
                data = res.get("data") or []
                status = "ok" if "data" in res else res.get("warning") or res.get("error") or ""
                if not data:
                    rows.append([sid, id_type(sid), status, None, *[""] * 7])
                for rank, d in enumerate(data, start=1):
                    rows.append([
                        sid, id_type(sid), status, rank, d.get("figi") or "", d.get("compositeFIGI") or "",
                        d.get("ticker") or "", d.get("name") or "", d.get("exchCode") or "",
                        d.get("marketSector") or "", d.get("securityType") or "",
                    ])
        figi = pd.DataFrame(rows, columns=OPENFIGI_MAPPING).astype({"result_rank": "Int64"}).astype(str)
        figi = figi.replace({"<NA>": ""})
        print("OpenFIGI results:")
        print(figi.to_string())

        tickers = load_company_tickers(RAW / "sec" / "company_tickers.json")
        by_ticker = tickers.assign(key=tickers["ticker"].map(norm_ticker)).groupby("key")["cik"].agg(set)
        sic = pd.read_csv(RAW / "sec" / "sic.csv", dtype=str, keep_default_na=False)
        eq = figi[figi["market_sector"] == "Equity"].drop_duplicates("sec_id")
        ciks = {c for t in eq["ticker"] if t for c in by_ticker.get(norm_ticker(t), ())}
        fetch = sorted(ciks - set(sic["cik"].astype(int)))
        print(f"CIKs reached: {sorted(ciks)}; not in sic.csv, fetched from EDGAR: {fetch}")
        if fetch:
            client = client_from_env(cfg)
            got = []
            for cik in fetch:
                sub = client.get_json(SUBMISSIONS_URL.format(cik=cik))
                got.append([str(cik), sub.get("name") or "", str(sub.get("sic") or ""), sub.get("sicDescription") or ""])
            got = pd.DataFrame(got, columns=SIC_CSV)
            print(got.to_string())
            sic = pd.concat([sic, got], ignore_index=True)
        empty_fb = pd.DataFrame(columns=FALLBACK)
        ff12 = parse_siccodes12((RAW / "french" / "Siccodes12.txt").read_text(encoding="latin-1"))
        rows_new = build_security_map(figi, empty_fb, pd.read_csv(OVERRIDES, dtype=str, keep_default_na=False),
                                      tickers, sic, ff12)
        path = EXTRA / "security_map_extra.csv"
        if path.exists():
            old = pd.read_csv(path, dtype=str, keep_default_na=False)
            rows_new = pd.concat([old[~old["sec_id"].isin(rows_new["sec_id"])], rows_new.astype(str)], ignore_index=True)
        rows_new = rows_new.replace({"<NA>": ""}).sort_values("sec_id", kind="mergesort")
        write_csv(rows_new, path)
        print(f"wrote {path.relative_to(ROOT).as_posix()}:")
        print(rows_new.to_string())

    smap = load_security_map(ROOT / "data")
    prices = load_prices_dir(ROOT / "data")
    yf = smap.set_index("sec_id").loc[ids, "yf_ticker"]
    need = sorted(set(yf[yf != ""]) - set(prices.columns))
    print(f"yf_tickers with no price column: {need}")
    if not retry_missing:  # instructions/08, A answer 4: known-missing tickers are skipped unless asked for
        known = set(pd.read_csv(RAW / "prices" / "missing.csv", dtype=str, keep_default_na=False)["yf_ticker"])
        skip = [t for t in need if t in known]
        need = [t for t in need if t not in known]
        print(f"skipped, already in data/raw/prices/missing.csv (pass --retry-missing to retry): {skip}")
    if not need:
        return
    got = []
    for i in range(0, len(need), PRICE_BATCH):
        batch_t = need[i : i + PRICE_BATCH]
        close, errors = yf_close(batch_t, cfg)
        for t in batch_t:
            s = _series(close, t)
            if s.empty:
                print(f"  no rows: {t} ({errors.get(t, 'no yfinance error recorded')})")
            else:
                got.append(s)
    if not got:
        return
    panel = pd.concat(got, axis=1).sort_index()
    path = EXTRA / "adjclose_extra.parquet"
    if path.exists():
        old = pd.read_parquet(path)
        panel = old.drop(columns=[c for c in panel.columns if c in old.columns]).join(panel, how="outer").sort_index()
    panel = panel[sorted(panel.columns)].astype("float64")
    panel.index.name = "date"
    path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(path, engine="pyarrow", index=True)
    print(f"wrote {path.relative_to(ROOT).as_posix()}: {panel.shape}, {panel.index[0].date()} to {panel.index[-1].date()}")
    print(panel.apply(lambda s: pd.Series({"first": s.first_valid_index(), "last": s.last_valid_index(),
                                           "n": s.notna().sum()})).to_string())


def update_manifest(stage: str, uncommitted: dict | None = None) -> None:
    """Pull time, library versions, CSV row counts and sha256 of every committed file under data/raw/."""
    m = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    m.setdefault("pulled_at_utc", {})[stage] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    m["libraries"] = {
        "python": platform.python_version(),
        "lxml": lxml.__version__,
        "numpy": numpy.__version__,
        "pandas": pd.__version__,
        "requests": requests.__version__,
        "pyarrow": pyarrow.__version__,
        "yfinance": yfinance.__version__,
    }
    files = sorted(p for p in RAW.rglob("*") if p.is_file() and p.name not in ("MANIFEST.json", ".gitkeep"))
    m["sha256"] = {p.relative_to(RAW).as_posix(): sha256(p.read_bytes()) for p in files}
    m["row_counts"] = {
        p.relative_to(RAW).as_posix(): len(pd.read_csv(p, dtype=str)) for p in files if p.suffix == ".csv"
    }
    if uncommitted is not None:
        m.setdefault("uncommitted_sha256", {}).update(uncommitted)
    write_json(MANIFEST, m)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["fixtures", "edgar", "figi", "sec", "french", "prices", "navret", "figi2"])
    ap.add_argument("--overrides-only", action="store_true", help="with --stage sec: instructions/03, step 3.0")
    ap.add_argument("--new-only", action="store_true", help="with --stage prices: instructions/03, step 3.0")
    ap.add_argument("--holdings", help="with --benchmark, no --stage: step 7.3, map and price a new holdings file")
    ap.add_argument("--benchmark", help="the benchmark holdings file for --holdings")
    ap.add_argument("--retry-missing", action="store_true",
                    help="with --holdings: also retry the tickers in data/raw/prices/missing.csv (instructions/08, A 4)")
    args = ap.parse_args()
    cfg = load_config(ROOT / "config.toml")
    if args.holdings or args.benchmark:
        if args.stage or not (args.holdings and args.benchmark):
            ap.error("--holdings and --benchmark go together, without --stage")
        stage_holdings(cfg, args.holdings, args.benchmark, args.retry_missing)
        return
    if args.retry_missing:
        ap.error("--retry-missing goes with --holdings and --benchmark")
    if not args.stage:
        ap.error("give --stage, or --holdings with --benchmark")
    if args.stage == "figi2":
        stage_figi2(cfg)
        update_manifest("figi2")
        return
    if args.stage == "figi":
        stage_figi(cfg)
        update_manifest("figi")
        return
    if args.stage == "prices":
        stage_prices_new(cfg) if args.new_only else stage_prices(cfg)
        update_manifest("prices")
        return
    if args.stage == "french":
        stage_french(cfg)
        update_manifest("french")
        return
    client = client_from_env(cfg)
    if args.stage == "fixtures":
        stage_fixtures(cfg, client)
    elif args.stage == "edgar":
        update_manifest("edgar", stage_edgar(cfg, client))
    elif args.stage == "sec":
        stage_sec_overrides(cfg, client) if args.overrides_only else stage_sec(cfg, client)
        update_manifest("sec")
    elif args.stage == "navret":
        update_manifest("navret", stage_navret(cfg, client))


if __name__ == "__main__":
    main()
