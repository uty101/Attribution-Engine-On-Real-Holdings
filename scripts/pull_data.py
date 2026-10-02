"""The only network code in the repo (rule 8).

    python scripts/pull_data.py --stage fixtures
    python scripts/pull_data.py --stage edgar

`--stage edgar` writes under data/raw/ and updates data/raw/MANIFEST.json.

Reads SEC_USER_AGENT from the environment; stops if it is unset (rule 15).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import lxml
import numpy
import pandas as pd
import requests
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from attrib.config import load_config  # noqa: E402
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
    ap.add_argument("--stage", required=True, choices=["fixtures", "edgar"])
    args = ap.parse_args()
    cfg = load_config(ROOT / "config.toml")
    client = client_from_env(cfg)
    if args.stage == "fixtures":
        stage_fixtures(cfg, client)
    elif args.stage == "edgar":
        update_manifest("edgar", stage_edgar(cfg, client))


if __name__ == "__main__":
    main()
