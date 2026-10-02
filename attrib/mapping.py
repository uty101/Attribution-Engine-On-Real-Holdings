"""sec_id -> ticker -> CIK -> SIC -> FF12 (kickoff Section 5.2, instructions/02_section_2.md B and C 2.2)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

SECURITY_MAP = [
    "sec_id", "id_type", "ticker", "yf_ticker", "figi", "figi_name", "cik", "sic", "ff12", "map_status", "source",
]
OVERRIDES = ["kind", "sec_id", "period_date", "value", "source_note"]
# Convention 4.6: the 12 FF12 industries in French's order
FF12 = ["NoDur", "Durbl", "Manuf", "Enrgy", "Chems", "BusEq", "Telcm", "Utils", "Shops", "Hlth", "Money", "Other"]

_HEADER_RE = re.compile(r"^\s*(\d{1,2})\s+(\S+)\s+(.*\S)\s*$")
_RANGE_RE = re.compile(r"^\s*(\d{4})-(\d{4})\b")


def parse_siccodes12(text: str) -> pd.DataFrame:
    """French's Siccodes12.txt: an industry header line (number, short name, long name), then
    lines of `NNNN-NNNN` ranges. Returns (industry, sic_lo, sic_hi) in file order.

    Industry 12 (Other) has no ranges, so it has no row.
    """
    rows, industry = [], None
    for line in text.splitlines():
        if not line.strip():
            continue
        m = _RANGE_RE.match(line)
        if m:
            if industry is None:
                raise ValueError(f"range before any industry header: {line!r}")
            rows.append([industry, int(m.group(1)), int(m.group(2))])
            continue
        h = _HEADER_RE.match(line)
        if not h:
            raise ValueError(f"unrecognised Siccodes12 line: {line!r}")
        industry = h.group(2)
    return pd.DataFrame(rows, columns=["industry", "sic_lo", "sic_hi"]).astype({"sic_lo": "int64", "sic_hi": "int64"})


def sic_to_ff12(sic: int | None, table: pd.DataFrame) -> str:
    """The FF12 industry whose range holds `sic`; Other for None or a SIC in no range (Convention 4.6)."""
    if sic is None or pd.isna(sic):
        return "Other"
    hit = table[(table["sic_lo"] <= int(sic)) & (int(sic) <= table["sic_hi"])]
    return "Other" if hit.empty else str(hit["industry"].iloc[0])


def norm_ticker(t: str) -> str:
    """Kickoff 5.2: `-` and `/` both normalised to `-` before the exact ticker match."""
    return t.replace("/", "-")


def yf_ticker(t: str) -> str:
    """Convention 4.7: `/` replaced by `-` (BRK/B -> BRK-B)."""
    return t.replace("/", "-")


def _first_equity(figi: pd.DataFrame) -> pd.DataFrame:
    """Per sec_id, the first result (by result_rank) with marketSector Equity (instructions/02, B)."""
    eq = figi[figi["market_sector"] == "Equity"].copy()
    eq["_rank"] = pd.to_numeric(eq["result_rank"])
    eq = eq.sort_values(["sec_id", "_rank"], kind="mergesort").drop_duplicates("sec_id")
    comp = eq["composite_figi"].fillna("")
    eq["figi"] = comp.where(comp != "", eq["figi"])
    return eq.set_index("sec_id")[["ticker", "figi", "name"]]


def build_security_map(
    figi: pd.DataFrame, overrides: pd.DataFrame, tickers: pd.DataFrame, sic: pd.DataFrame, ff12: pd.DataFrame
) -> pd.DataFrame:
    """SECURITY_MAP, 1 row per `sec_id` in `figi`, sorted by `sec_id`.

    `figi` is data/raw/openfigi/mapping.csv; `overrides` is data/manual/overrides.csv;
    `tickers` has columns cik and ticker (company_tickers.json); `sic` is data/raw/sec/sic.csv;
    `ff12` is `parse_siccodes12` output.

    - ticker: the first OpenFIGI equity result's ticker, replaced by an override `ticker` row.
    - cik: exact match on the normalised ticker; an override `cik` row sets it when that match fails.
    - map_status: `no_match` (no ticker), `no_cik`, `no_sic`, else `mapped` (D-12).
    - ff12: blank for `no_match` (the Unmapped bucket); Other for `no_cik` and `no_sic` (Convention 4.6).
    """
    figi = figi.fillna("")
    ids = figi.drop_duplicates("sec_id").set_index("sec_id")["id_type"].sort_index()
    eq = _first_equity(figi)
    ov = overrides.fillna("").astype(str)
    ov_ticker = dict(zip(ov.loc[ov["kind"] == "ticker", "sec_id"], ov.loc[ov["kind"] == "ticker", "value"]))
    ov_cik = dict(zip(ov.loc[ov["kind"] == "cik", "sec_id"], ov.loc[ov["kind"] == "cik", "value"]))

    t = tickers.astype({"cik": "int64"}).assign(key=tickers["ticker"].astype(str).map(norm_ticker))
    by_ticker = t.groupby("key")["cik"].agg(lambda s: sorted(set(s)))
    s = sic.fillna("").astype(str)
    sic_by_cik = dict(zip(s["cik"].astype(int), s["sic"]))

    rows = []
    for sid, kind in ids.items():
        source = []
        ticker = figi_id = figi_name = ""
        if sid in eq.index:
            ticker, figi_id, figi_name = eq.loc[sid, ["ticker", "figi", "name"]]
        if sid in ov_ticker:
            ticker = ov_ticker[sid]
            source.append("override_ticker")
        cik = sic_code = None
        ff = ""
        if not ticker:
            status = "no_match"
        else:
            ciks = by_ticker.get(norm_ticker(ticker), [])
            if len(ciks) > 1:
                raise ValueError(f"ticker {ticker!r} matches {len(ciks)} CIKs in company_tickers.json: {ciks}")
            if ciks:
                cik = ciks[0]
            elif sid in ov_cik:
                cik = int(ov_cik[sid])
                source.append("override_cik")
            if cik is None:
                status, ff = "no_cik", "Other"
            else:
                sic_code = sic_by_cik.get(cik, "") or None
                if sic_code is None:
                    status, ff = "no_sic", "Other"
                else:
                    sic_code = int(sic_code)
                    status, ff = "mapped", sic_to_ff12(sic_code, ff12)
        rows.append([
            sid, kind, ticker, yf_ticker(ticker), figi_id, figi_name, cik, sic_code, ff, status,
            ";".join(source) if source else "openfigi",
        ])
    out = pd.DataFrame(rows, columns=SECURITY_MAP)
    return out.astype({"cik": "Int64", "sic": "Int64"})


def load_company_tickers(path: str | Path) -> pd.DataFrame:
    """company_tickers.json as (cik, ticker, title)."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return pd.DataFrame(
        [[int(r["cik_str"]), r["ticker"], r["title"]] for r in d.values()], columns=["cik", "ticker", "title"]
    )


def security_map_from_dir(data_dir: str | Path) -> pd.DataFrame:
    """`build_security_map` on the committed inputs under `data_dir` (data/raw/ and data/manual/)."""
    d = Path(data_dir)

    def csv(p: Path) -> pd.DataFrame:
        return pd.read_csv(p, dtype=str, keep_default_na=False)

    return build_security_map(
        csv(d / "raw" / "openfigi" / "mapping.csv"),
        csv(d / "manual" / "overrides.csv"),
        load_company_tickers(d / "raw" / "sec" / "company_tickers.json"),
        csv(d / "raw" / "sec" / "sic.csv"),
        parse_siccodes12((d / "raw" / "french" / "Siccodes12.txt").read_text(encoding="latin-1")),
    )
