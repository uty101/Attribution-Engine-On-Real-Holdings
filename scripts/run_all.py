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
from attrib.reconstruction import reconstruction_table  # noqa: E402
from attrib.returns import (  # noqa: E402
    BOOK_MONTHLY,
    BOOK_QUARTERLY,
    NAV_MONTHLY,
    apply_return_overrides,
    book_monthly,
    book_quarter,
    book_return,
    bucket_table,
    daily_returns,
    load_nav,
    load_prices,
    monthly_returns,
    nport_month_series,
    quarter_calendar,
    return_overrides_with_t,
)

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


# kickoff 8 step 2.5, instructions/02 C 2.5 and 02b C 2.5: list lengths and the large-move threshold
UNMAPPED_TOP_N = 60
UNPRICED_TOP_N = 20
NOCIK_TOP_N = 40
LARGE_MOVE_ABS = 0.25  # daily |return| > 25%
MAPPING_WEIGHTS = ["unmapped_weight", "unpriced_weight", "other_nosic_weight"]


def _top(rows: pd.DataFrame, n: int, cols: list[str]) -> pd.DataFrame:
    """Per sec_id: the largest weight, the entity and name at it, and every period in `rows`,
    semicolon-joined; the `n` largest by max_weight (ties by sec_id)."""
    if rows.empty:
        return pd.DataFrame(columns=cols)
    r = rows.sort_values(["sec_id", "weight", "entity", "period_date"], ascending=[True, False, True, True],
                         kind="mergesort")
    first = r.drop_duplicates("sec_id").set_index("sec_id")
    periods = rows.groupby("sec_id")["period_date"].agg(lambda s: ";".join(sorted(set(s))))
    out = first.assign(max_weight=first["weight"], entity_of_max=first["entity"], periods=periods).reset_index()
    out = out.sort_values(["max_weight", "sec_id"], ascending=[False, True], kind="mergesort").head(n)
    return out[cols].reset_index(drop=True)


def mapping_coverage(cfg, smap: pd.DataFrame) -> None:
    """Step 2.5: the mapping columns of coverage.csv, unmapped_top.csv, unpriced_top.csv,
    nocik_top.csv and large_moves.csv. Weights per Convention 4.5, by sec_id."""
    prices = load_prices(ROOT / "data")
    ivv = load_nav(ROOT / "data")[cfg.entities["ivv"].etf_ticker].dropna().index
    cal = quarter_calendar(ivv, holdings_dates(cfg))
    q_start = {str(h): qs for h, qs in zip(cal["holdings_date"], cal["q_start"])}

    books = pd.concat(
        [read_str_csv(PROCESSED / f"holdings_{eid}.csv") for eid in cfg.entities], ignore_index=True
    ).astype({"value_usd": float})
    books["weight"] = books["value_usd"] / books.groupby(["entity", "period_date"])["value_usd"].transform("sum")
    books = books.join(smap.set_index("sec_id")[["id_type", "ticker", "yf_ticker", "map_status"]], on="sec_id")

    def priced(r) -> bool:
        """instructions/02, B: an adjusted close on the exact q_start of the book's return quarter."""
        d, t = q_start[r["period_date"]], r["yf_ticker"]
        return t in prices.columns and d in prices.index and pd.notna(prices.at[d, t])

    has_ticker = books["map_status"] != "no_match"
    books["priced"] = False
    books.loc[has_ticker, "priced"] = books[has_ticker].apply(priced, axis=1)
    flags = {
        "unmapped_weight": books["map_status"] == "no_match",
        "unpriced_weight": has_ticker & ~books["priced"],
        "other_nosic_weight": books["map_status"].isin(["no_cik", "no_sic"]),
    }
    w = pd.DataFrame({k: books["weight"] * v for k, v in flags.items()})
    w = w.join(books[["entity", "period_date"]]).groupby(["entity", "period_date"])[MAPPING_WEIGHTS].sum()
    cov = read_str_csv(TABLES / "coverage.csv").drop(columns=MAPPING_WEIGHTS).join(w, on=["entity", "period_date"])
    write_csv(cov[COVERAGE], TABLES / "coverage.csv")

    write_csv(_top(books[flags["unmapped_weight"]], UNMAPPED_TOP_N,
                   ["sec_id", "id_type", "name", "max_weight", "entity_of_max", "periods"]),
              TABLES / "unmapped_top.csv")
    write_csv(_top(books[flags["unpriced_weight"]], UNPRICED_TOP_N,
                   ["sec_id", "yf_ticker", "name", "max_weight", "entity_of_max", "periods"]),
              TABLES / "unpriced_top.csv")
    write_csv(_top(books[books["map_status"] == "no_cik"], NOCIK_TOP_N,
                   ["sec_id", "ticker", "name", "max_weight", "entity_of_max", "periods"]),
              TABLES / "nocik_top.csv")

    rets = daily_returns(prices)
    t_of = {str(h): t for t, h in zip(cal["t"], cal["holdings_date"])}
    qrow = cal.set_index("t")
    held = books[books["yf_ticker"].fillna("").isin(set(prices.columns))]
    moves = []
    for (eid, period), b in held.groupby(["entity", "period_date"], sort=True):
        t = t_of[period]
        lo, hi = qrow.at[t, "q_start"], qrow.at[t, "q_end"]
        window = rets.loc[(rets.index > lo) & (rets.index <= hi)]
        for _, r in b.iterrows():
            s = window[r["yf_ticker"]]
            for d, x in s[s.abs() > LARGE_MOVE_ABS].items():
                moves.append([eid, t, r["sec_id"], r["yf_ticker"], d.strftime("%Y-%m-%d"), x, r["weight"]])
    large = pd.DataFrame(moves, columns=["entity", "t", "sec_id", "yf_ticker", "date", "daily_return", "weight"])
    write_csv(large.sort_values(["entity", "t", "date", "sec_id"], kind="mergesort"), TABLES / "large_moves.csv")


def section_2(cfg) -> list[str]:
    """SECURITY_MAP to data/processed/security_map.csv (step 2.2), nav_monthly.csv (step 2.1b-2),
    then the mapping coverage and review lists (step 2.5)."""
    smap = security_map_from_dir(ROOT / "data")
    write_csv(smap, PROCESSED / "security_map.csv")
    navm, failures = nav_monthly(cfg)
    write_csv(navm, TABLES / "nav_monthly.csv")
    mapping_coverage(cfg, smap)
    return failures


def book_returns(cfg) -> dict:
    """Step 3.2: POSITION_RETURNS, BUCKETS, the quarterly book table and monthly book returns for
    every entity and quarter (D-17 as amended by instructions/03, step 3.2), with the
    `quarter_return` overrides applied between `book_quarter` and `bucket_table` (D-16)."""
    smap = security_map_from_dir(ROOT / "data")
    prices = load_prices(ROOT / "data")
    ivv = load_nav(ROOT / "data")[cfg.entities["ivv"].etf_ticker].dropna().index
    cal = quarter_calendar(ivv, holdings_dates(cfg))
    ov = return_overrides_with_t(read_str_csv(ROOT / "data" / "manual" / "overrides.csv"), cal)
    pos, monthly = [], []
    for eid in cfg.entities:
        books = read_str_csv(PROCESSED / f"holdings_{eid}.csv").astype({"value_usd": float})
        for _, q in cal.iterrows():
            b = books[books["period_date"] == str(q["holdings_date"])].assign(t=q["t"])
            pos.append(book_quarter(b, smap, prices, q["q_start"], q["q_end"]))
            m = book_monthly(b, smap, prices, q["q_start"], q["q_end"])
            monthly.append(pd.DataFrame({"entity": eid, "month": m.index.astype(str), "ret": m.to_numpy()}))
    pos = apply_return_overrides(pd.concat(pos, ignore_index=True), ov)
    buckets = bucket_table(pos)
    bq = []
    for (eid, t), g in pos.groupby(["entity", "t"], sort=False):
        w = g.groupby("bucket")["weight"].sum()
        bq.append([eid, t, book_return(buckets[(buckets["entity"] == eid) & (buckets["t"] == t)]),
                   w.get("Unmapped", 0.0), w.get("Unpriced", 0.0), g.loc[g["delisted_in_quarter"], "weight"].sum()])
    book_q = pd.DataFrame(bq, columns=BOOK_QUARTERLY)
    write_csv(pos, PROCESSED / "position_returns.csv")
    write_csv(buckets, TABLES / "buckets.csv")
    write_csv(book_q, TABLES / "book_quarterly.csv")
    write_csv(pd.concat(monthly, ignore_index=True)[BOOK_MONTHLY], TABLES / "book_monthly.csv")
    return {"cal": cal, "book_q": book_q}


def benchmark_nav_monthly(cfg) -> pd.DataFrame:
    """Calendar-month returns of each benchmark's ETF (Convention 4.14), as entity, month, ret."""
    mret = monthly_returns(load_nav(ROOT / "data"))
    out = [
        pd.DataFrame({"entity": eid, "month": mret.index.astype(str), "ret": mret[e.etf_ticker].to_numpy()})
        for eid, e in cfg.entities.items() if e.type == "benchmark"
    ]
    return pd.concat(out, ignore_index=True).dropna(subset=["ret"])


def benchmark_check(cfg, table4: pd.DataFrame) -> tuple[list[str], pd.DataFrame]:
    """Step 3.3 as amended by instructions/03: stop under rule 4 if any benchmark |gap| exceeds
    `gates.benchmark_gap_stop`; the quarters above `gates.benchmark_gap_max` are listed, not stopped on."""
    bench = table4[table4["entity"].isin([k for k, e in cfg.entities.items() if e.type == "benchmark"])]
    stop = bench[bench["gap"].abs() > cfg.gates.benchmark_gap_stop]
    failures = [f"{r.entity} t={r.t}: |gap| {abs(r.gap)!r} > benchmark_gap_stop" for r in stop.itertuples()]
    return failures, bench[bench["gap"].abs() > cfg.gates.benchmark_gap_max]


def section_3(cfg) -> list[str]:
    """Book returns (step 3.2), then the benchmark check (step 3.3)."""
    res = book_returns(cfg)
    book_q, cal = res["book_q"], res["cal"]
    bench = book_q[book_q["entity"].isin([k for k, e in cfg.entities.items() if e.type == "benchmark"])]
    table4 = reconstruction_table(bench, benchmark_nav_monthly(cfg), cal)
    failures, above = benchmark_check(cfg, table4)
    if not above.empty:
        print(f"benchmark quarters with |gap| > benchmark_gap_max ({cfg.gates.benchmark_gap_max}):")
        print(above.merge(book_q, on=["entity", "t", "book_return"]).to_string())
    write_csv(table4, TABLES / "reconstruction.csv")
    return failures


SECTIONS = {1: section_1, 2: section_2, 3: section_3}


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
