"""The only network code in the repo (rule 8).

    python scripts/pull_data.py --stage fixtures
    python scripts/pull_data.py --stage edgar

Reads SEC_USER_AGENT from the environment; stops if it is unset (rule 15).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from attrib.config import load_config  # noqa: E402
from attrib.edgar import EdgarClient, filing_base_url, find_infotable_name, list_13f_filings  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"

# instructions/01_section_1.md, D 1.3: the 2 Akre fixtures
AKRE_DOLLARS = ("2023-06-30", "0001112520-23-000013")
AKRE_THOUSANDS_PERIOD = "2022-06-30"


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write_bytes(path: Path, b: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b)


def write_json(path: Path, obj) -> None:
    write_bytes(path, (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def client_from_env(cfg) -> EdgarClient:
    ua = os.environ.get("SEC_USER_AGENT", "").strip()
    if not ua:
        sys.exit("SEC_USER_AGENT is unset: stop under rule 4 (kickoff rule 15)")
    e = cfg.edgar
    return EdgarClient(ua, e.min_interval_s, e.retries, e.backoff_s)


def infotable_url(client: EdgarClient, cik: int, accession: str) -> str:
    base = filing_base_url(cik, accession)
    return f"{base}/{find_infotable_name(client.get_json(f'{base}/index.json'))}"


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

    path = FIXTURES / "FIXTURES.json"
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    existing.update(record)
    write_json(path, existing)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["fixtures"])
    args = ap.parse_args()
    cfg = load_config(ROOT / "config.toml")
    client = client_from_env(cfg)
    if args.stage == "fixtures":
        stage_fixtures(cfg, client)


if __name__ == "__main__":
    main()
