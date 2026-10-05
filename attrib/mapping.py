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


def name_tokens(name: str) -> list[str]:
    """instructions/02b, step 2.1c: upper-case, every non-alphanumeric character to a space, split,
    and a leading `THE` dropped."""
    t = re.sub(r"[^A-Z0-9]", " ", str(name).upper()).split()
    return t[1:] if t and t[0] == "THE" else t


def name_check(holding_name: str, result_name: str) -> str:
    """'' when the first tokens of the 2 normalised names are equal, else the reject reason."""
    h, r = name_tokens(holding_name), name_tokens(result_name)
    if not h or not r:
        return f"name check: empty name ({holding_name!r} vs {result_name!r})"
    if h[0] != r[0]:
        return f"name check: {h[0]} != {r[0]}"
    return ""


def isin_check_digit(body: str) -> str:
    """The ISO 6166 Luhn check digit of an 11-character ISIN body."""
    digits = "".join(str(int(c, 36)) for c in body)
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch) * (2 if i % 2 == 0 else 1)
        total += d // 10 + d % 10
    return str((10 - total % 10) % 10)


def us_isin(cusip: str) -> str:
    """instructions/02b, step 2.1c: `"US" + cusip + Luhn check digit`."""
    return "US" + cusip + isin_check_digit("US" + cusip)


# instructions/02b, step 2.1c: the exchanges each fallback pass accepts
FIGI_US_EXCH = {"US", "UN", "UW", "UQ", "UA", "UR", "UP", "UF", "UV", "UD"}
YAHOO_US_EXCH = {"NYQ", "NMS", "NGM", "NCM", "ASE", "PCX", "BTS"}
YAHOO_TYPES = {"EQUITY", "ETF"}
FALLBACK = [
    "sec_id", "pass", "query_type", "query_value", "rank", "ticker", "name", "exch_code", "market_sector",
    "security_type", "accepted", "reject_reason",
]
FALLBACK_SOURCE = {1: "openfigi", 2: "figi_isin", 3: "figi_noexch", 4: "yahoo_isin"}


def judge_results(
    sec_id: str, pass_no: int, query_type: str, query_value: str, results: list[dict], holding_name: str,
    no_result_reason: str = "no result",
) -> list[list]:
    """FALLBACK rows for 1 query of pass 2, 3 or 4: every result, with the first acceptable one
    accepted (instructions/02b, step 2.1c).

    `results` are dicts with ticker, name, exch_code, market_sector, security_type. Pass 2 needs
    marketSector Equity; pass 3 also an exchange in FIGI_US_EXCH; pass 4 a Yahoo quoteType
    (in security_type) of EQUITY or ETF and an exchange in YAHOO_US_EXCH. Passes 2 to 4 all need
    the name check against `holding_name`.
    """
    if not results:
        return [[sec_id, pass_no, query_type, query_value, None, "", "", "", "", "", False, no_result_reason]]
    rows, done = [], False
    for rank, r in enumerate(results, start=1):
        if done:
            reason = "an earlier result was accepted"
        elif pass_no in (2, 3) and r.get("market_sector") != "Equity":
            reason = f"marketSector {r.get('market_sector')!r} is not Equity"
        elif pass_no == 3 and r.get("exch_code") not in FIGI_US_EXCH:
            reason = f"exchCode {r.get('exch_code')!r} is not a US venue"
        elif pass_no == 4 and r.get("security_type") not in YAHOO_TYPES:
            reason = f"quoteType {r.get('security_type')!r} is not EQUITY or ETF"
        elif pass_no == 4 and r.get("exch_code") not in YAHOO_US_EXCH:
            reason = f"exchange {r.get('exch_code')!r} is not a US venue"
        elif not r.get("ticker"):
            reason = "no ticker"
        else:
            reason = name_check(holding_name, r.get("name", ""))
        ok = not done and reason == ""
        done = done or ok
        rows.append([
            sec_id, pass_no, query_type, query_value, rank, r.get("ticker") or "", r.get("name") or "",
            r.get("exch_code") or "", r.get("market_sector") or "", r.get("security_type") or "", ok, reason,
        ])
    return rows


def _accepted_fallback(fallback: pd.DataFrame) -> pd.DataFrame:
    """Per sec_id, the accepted fallback result of the lowest pass."""
    fb = fallback.fillna("")
    fb = fb[fb["accepted"].astype(str).isin(["True", "true", "1"])].copy()
    fb["_pass"] = pd.to_numeric(fb["pass"])
    fb = fb.sort_values(["sec_id", "_pass"], kind="mergesort").drop_duplicates("sec_id")
    return fb.set_index("sec_id")[["_pass", "ticker", "name"]]


def build_security_map(
    figi: pd.DataFrame,
    fallback: pd.DataFrame,
    overrides: pd.DataFrame,
    tickers: pd.DataFrame,
    sic: pd.DataFrame,
    ff12: pd.DataFrame,
) -> pd.DataFrame:
    """SECURITY_MAP, 1 row per `sec_id` in `figi`, sorted by `sec_id`.

    `figi` is data/raw/openfigi/mapping.csv; `fallback` is data/raw/openfigi/fallback.csv;
    `overrides` is data/manual/overrides.csv; `tickers` has columns cik and ticker
    (company_tickers.json); `sic` is data/raw/sec/sic.csv; `ff12` is `parse_siccodes12` output.

    - ticker: an override `ticker` row, else the first OpenFIGI equity result (pass 1), else the
      accepted fallback result of pass 2, 3 or 4 (instructions/02b, step 2.1c).
    - source: `openfigi`, `figi_isin`, `figi_noexch` or `yahoo_isin` for the pass that gave the
      ticker (`openfigi` when none did), with `;override_ticker` and `;override_cik` appended.
    - cik: exact match on the normalised ticker; an override `cik` row sets it when that match fails.
    - map_status: `no_match` (no ticker), `no_cik`, `no_sic`, else `mapped` (D-12).
    - ff12: blank for `no_match` (the Unmapped bucket); Other for `no_cik` and `no_sic` (Convention 4.6).
    """
    figi = figi.fillna("")
    ids = figi.drop_duplicates("sec_id").set_index("sec_id")["id_type"].sort_index()
    eq = _first_equity(figi)
    fb = _accepted_fallback(fallback)
    ov = overrides.fillna("").astype(str)
    ov_ticker = dict(zip(ov.loc[ov["kind"] == "ticker", "sec_id"], ov.loc[ov["kind"] == "ticker", "value"]))
    ov_cik = dict(zip(ov.loc[ov["kind"] == "cik", "sec_id"], ov.loc[ov["kind"] == "cik", "value"]))

    t = tickers.astype({"cik": "int64"}).assign(key=tickers["ticker"].astype(str).map(norm_ticker))
    by_ticker = t.groupby("key")["cik"].agg(lambda s: sorted(set(s)))
    s = sic.fillna("").astype(str)
    sic_by_cik = dict(zip(s["cik"].astype(int), s["sic"]))

    rows = []
    for sid, kind in ids.items():
        ticker = figi_id = figi_name = ""
        base = FALLBACK_SOURCE[1]
        if sid in eq.index:
            ticker, figi_id, figi_name = eq.loc[sid, ["ticker", "figi", "name"]]
        elif sid in fb.index:
            p, ticker, figi_name = fb.loc[sid, ["_pass", "ticker", "name"]]
            base = FALLBACK_SOURCE[int(p)]
        source = [base]
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
            sid, kind, ticker, yf_ticker(ticker), figi_id, figi_name, cik, sic_code, ff, status, ";".join(source),
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
        csv(d / "raw" / "openfigi" / "fallback.csv"),
        csv(d / "manual" / "overrides.csv"),
        load_company_tickers(d / "raw" / "sec" / "company_tickers.json"),
        csv(d / "raw" / "sec" / "sic.csv"),
        parse_siccodes12((d / "raw" / "french" / "Siccodes12.txt").read_text(encoding="latin-1")),
    )
