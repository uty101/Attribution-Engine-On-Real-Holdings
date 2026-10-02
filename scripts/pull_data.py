"""The only network code in the repo (rule 8).

    python scripts/pull_data.py --stage fixtures
    python scripts/pull_data.py --stage edgar
    python scripts/pull_data.py --stage figi
    python scripts/pull_data.py --stage sec
    python scripts/pull_data.py --stage french

Every stage but `fixtures` writes under data/raw/ and updates data/raw/MANIFEST.json.
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
import requests
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import run_all  # noqa: E402  (scripts/ is sys.path[0] when this file runs)
from attrib.config import load_config  # noqa: E402
from attrib.mapping import norm_ticker  # noqa: E402
from attrib.edgar import (  # noqa: E402
    HOLDINGS_RAW_NPORT,
    EdgarClient,
    filing_base_url,
    find_infotable_name,
    holdings_dates,
    list_13f_filings,
    list_nport_filings,
    parse_nport,
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
        header, _ = parse_nport(b)
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
            header, raw = parse_nport(b)
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
    ap.add_argument("--stage", required=True, choices=["fixtures", "edgar", "figi", "sec", "french"])
    args = ap.parse_args()
    cfg = load_config(ROOT / "config.toml")
    if args.stage == "figi":
        stage_figi(cfg)
        update_manifest("figi")
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
        stage_sec(cfg, client)
        update_manifest("sec")


if __name__ == "__main__":
    main()
