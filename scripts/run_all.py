"""Regenerate outputs from data/raw/ and data/manual/ (D-01).

    python scripts/run_all.py --section N

runs every section up to and including N. Offline: no network is touched.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from attrib.config import load_config  # noqa: E402
from attrib.edgar import (  # noqa: E402
    aggregate_book,
    equity_rows_13f,
    equity_rows_nport,
    holdings_dates,
    parse_13f_infotable,
    resolve_13f_books,
    resolve_nport_books,
    select_13f_filings,
    select_nport_filing,
    units_check,
)
from attrib.mapping import security_map_from_dir  # noqa: E402
from attrib.returns import NAV_MONTHLY, load_nav, monthly_returns, nport_month_series  # noqa: E402

RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "outputs" / "tables"

COVERAGE = [
    "entity", "period_date", "filing_date", "lag_days", "n_rows_raw", "n_rows_kept", "dropped_value_usd",
    "total_value_usd", "median_implied_price", "amendments_used", "isin_only_weight", "unmapped_weight",
    "unpriced_weight", "other_nosic_weight",
]
# instructions/01_section_1.md, D 1.6: kept pctVal of every N-PORT book must sum into [95, 101]
NPORT_PCT_LO, NPORT_PCT_HI = 95.0, 101.0


def write_csv(df: pd.DataFrame, path: Path) -> None:
    """Rule 9 as amended by instructions/01b: %.17g floats, LF, UTF-8, no index."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, float_format="%.17g", lineterminator="\n", encoding="utf-8")


def read_str_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _lag(filing_date: str, period: str) -> int:
    return (date.fromisoformat(filing_date) - date.fromisoformat(period)).days


def _isin_only_weight(book: pd.DataFrame) -> float:
    """instructions/01b, step 1.4b: the weight of rows whose `sec_id` is an ISIN."""
    isin = (book["isin"] != "") & (book["sec_id"] == book["isin"])
    return float(book.loc[isin, "value_usd"].sum() / book["value_usd"].sum())


def fund_books(eid: str, H: list[date], lo: float, hi: float, failures: list[str]):
    filings = read_str_csv(RAW / "edgar" / "13f" / f"filings_{eid}.csv")
    fdate = dict(zip(filings["accession"], filings["filing_date"]))
    tables = {}
    for p in sorted((RAW / "edgar" / "13f" / eid).glob("*.xml")):
        acc = p.stem.split("_", 1)[1]
        tables[acc] = parse_13f_infotable(p.read_bytes(), date.fromisoformat(fdate[acc]))
    book = resolve_13f_books(filings, tables, H)
    cov = []
    for d in H:
        period = str(d)
        base, after = select_13f_filings(filings, period)
        if base is None:
            failures.append(f"{eid}: no 13F book for {period}")
            continue
        used = [base, *after]
        raw = pd.concat([tables[r["accession"]] for r in used], ignore_index=True)
        kept = equity_rows_13f(raw)
        b = book[book["period_date"] == period]
        _, bad = aggregate_book(kept, "value_usd", "shares")
        med = units_check(b)
        if not lo <= med <= hi:
            failures.append(f"{eid} {period}: median implied price {med!r} outside [{lo}, {hi}]")
        total = int(raw["value_usd"].sum())
        cov.append(
            {
                "entity": eid,
                "period_date": period,
                "filing_date": base["filing_date"],
                "lag_days": _lag(base["filing_date"], period),
                "n_rows_raw": len(raw),
                "n_rows_kept": len(kept) - len(bad),
                "dropped_value_usd": total - int(b["value_usd"].sum()),
                "total_value_usd": total,
                "median_implied_price": med,
                "amendments_used": ";".join(r["accession"] for r in used if r["form"] == "13F-HR/A"),
                "isin_only_weight": _isin_only_weight(b),
            }
        )
    return book, cov


def benchmark_books(eid: str, H: list[date], failures: list[str]):
    filings = read_str_csv(RAW / "edgar" / "nport" / f"filings_{eid}.csv")
    raw = read_str_csv(RAW / "edgar" / "nport" / f"holdings_{eid}.csv")
    raw = raw.astype({"balance": float, "val_usd": float, "pct_val": float})
    book = resolve_nport_books(filings, raw, H)
    Hs = {str(d) for d in H}
    for p in sorted(set(book["period_date"]) - Hs):
        failures.append(f"{eid}: N-PORT book with period {p} not in H")
    cov = []
    for d in H:
        period = str(d)
        f = select_nport_filing(filings, period)
        if f is None:
            failures.append(f"{eid}: no NPORT-P for {period}")
            continue
        r = raw[raw["accession"] == f["accession"]]
        kept = equity_rows_nport(r)
        _, bad = aggregate_book(kept, "val_usd", "balance")
        kept = kept.drop(bad.index)
        pct = float(kept["pct_val"].sum())
        if not NPORT_PCT_LO <= pct <= NPORT_PCT_HI:
            failures.append(f"{eid} {period}: kept pctVal sum {pct!r} outside [{NPORT_PCT_LO}, {NPORT_PCT_HI}]")
        b = book[book["period_date"] == period]
        total = float(r["val_usd"].sum())
        cov.append(
            {
                "entity": eid,
                "period_date": period,
                "filing_date": f["filing_date"],
                "lag_days": _lag(f["filing_date"], period),
                "n_rows_raw": len(r),
                "n_rows_kept": len(kept),
                "dropped_value_usd": total - float(b["value_usd"].sum()),
                "total_value_usd": total,
                "median_implied_price": units_check(b),
                "amendments_used": f["accession"],
                "isin_only_weight": _isin_only_weight(b),
            }
        )
    return book, cov


def section_1(cfg) -> list[str]:
    """Holdings books for all 5 entities and outputs/tables/coverage.csv (step 1.6)."""
    H = holdings_dates(cfg)
    failures: list[str] = []
    cov = []
    for eid, e in cfg.entities.items():
        if e.type == "fund":
            book, c = fund_books(eid, H, cfg.edgar.implied_price_lo, cfg.edgar.implied_price_hi, failures)
        else:
            book, c = benchmark_books(eid, H, failures)
        write_csv(book, PROCESSED / f"holdings_{eid}.csv")
        cov += c
    coverage = pd.DataFrame(cov).reindex(columns=COVERAGE)
    write_csv(coverage, TABLES / "coverage.csv")
    return failures


# instructions/02c_section_2_completion.md, Section B: OPEN-33 (b), the accepted Akre gap
AKRE_GAP_MONTHS = {"2025-08", "2025-09", "2025-10"}


def nav_monthly(cfg) -> tuple[pd.DataFrame, list[str]]:
    """NAV_MONTHLY for every fund, October 2019 to September 2026 (instructions/02b step 2.1b, 02c C 1).

    `nav_source = "nport"`: N-PORT B.5 month by month (`nport_month_series`); `"yfinance"`: the
    NAV ticker's month-end return. Missing months have no row. A `nport` fund may miss only the
    months of the accepted gap (02c, Section B).
    """
    nav = load_nav(ROOT / "data")
    mret = monthly_returns(nav)
    first = pd.Period(cfg.sample.first_holdings_date, freq="M") + 1
    months = list(pd.period_range(first, pd.Period(cfg.sample.last_return_date, freq="M"), freq="M"))
    resolved = read_str_csv(RAW / "edgar" / "nport_returns" / "series_resolved.csv").set_index("entity")
    out, failures = [], []
    for eid, e in cfg.entities.items():
        if e.type != "fund":
            continue
        if e.nav_source == "nport":
            b5 = read_str_csv(RAW / "edgar" / "nport_returns" / f"{eid}_monthly.csv")
            b5 = b5[b5["rtn_pct"] != ""]

            def pct(ids: list[str]) -> pd.Series:
                return b5[b5["class_id"].isin(ids)].set_index("month")["rtn_pct"].astype(float)

            r = resolved.loc[eid]
            etf_ids = [c for c in r["etf_class_ids"].split(";") if c]
            first_etf = nav[e.etf_successor].dropna().index[0].date()
            s = nport_month_series(months, pct([r["class_id"]]), pct(etf_ids), mret[e.etf_successor], first_etf)
            bad = sorted(set(s.loc[s["source"] == "missing", "month"]) - AKRE_GAP_MONTHS)
            if bad:
                failures.append(f"{eid}: monthly NAV return missing outside the accepted gap: {bad}")
        else:
            m = mret[e.nav_ticker]
            s = pd.DataFrame(
                [[str(p), m.get(p), "yfinance" if pd.notna(m.get(p)) else "missing"] for p in months],
                columns=["month", "ret", "source"],
            ).astype({"ret": "float64"})
        out.append(s[s["source"] != "missing"].assign(entity=eid))
    return pd.concat(out, ignore_index=True)[NAV_MONTHLY], failures


def section_2(cfg) -> list[str]:
    """SECURITY_MAP to data/processed/security_map.csv (step 2.2) and nav_monthly.csv (step 2.1b-2)."""
    smap = security_map_from_dir(ROOT / "data")
    write_csv(smap, PROCESSED / "security_map.csv")
    navm, failures = nav_monthly(cfg)
    write_csv(navm, TABLES / "nav_monthly.csv")
    return failures


SECTIONS = {1: section_1, 2: section_2}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--section", type=int, required=True, choices=range(1, 9))
    args = ap.parse_args()
    cfg = load_config(ROOT / "config.toml")
    for n in range(1, args.section + 1):
        if n not in SECTIONS:
            sys.exit(f"section {n} is not built yet")
        failures = SECTIONS[n](cfg)
        if failures:
            print(f"stop under rule 4: section {n} checks failed:")
            print("\n".join(failures))
            sys.exit(1)
        print(f"section {n}: all checks passed")


if __name__ == "__main__":
    main()
