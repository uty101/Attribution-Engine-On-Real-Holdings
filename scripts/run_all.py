"""Regenerate outputs from data/raw/ and data/manual/ (D-01).

    python scripts/run_all.py --section N

runs every section up to and including N. Offline: no network is touched.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from pc.cov import window_daily  # noqa: E402
from pc.stats import stationary_bootstrap_indices  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from attrib.brinson import EFFECTS, brinson_fachler, fill_empty  # noqa: E402
from attrib.config import load_config  # noqa: E402
from attrib.factors import (  # noqa: E402
    ALPHA,
    factor_contrib_by_year,
    fallback_betas,
    holdings_exposure,
    load_french,
    returns_based,
    rolling_betas,
    stock_betas,
)
from attrib.linking import carino, menchero  # noqa: E402
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
from attrib.bootstrap import bootstrap_mean  # noqa: E402
from attrib.reconstruction import gate, reconstruction_table  # noqa: E402
from attrib.risk import (  # noqa: E402
    DAILY_TO_MONTHLY,
    MONTHS_PER_YEAR,
    active_cov,
    active_share,
    fill_daily,
    issuer_weights,
    risk_weights,
    te_decomposition,
    ticker_buckets,
)
from attrib.returns import (  # noqa: E402
    BOOK_MONTHLY,
    BUCKETS_ORDER,
    BOOK_QUARTERLY,
    NAV_MONTHLY,
    NEUTRAL,
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
FIGURES = ROOT / "outputs" / "figures"

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


BOOTSTRAP = ["fund", "series", "mean", "p05", "p95"]


def section_3(cfg) -> list[str]:
    """Book returns (step 3.2), the benchmark check (step 3.3), then Table 4 for every entity, the
    fund gate and the gap bootstrap (step 3.4; amendment 11)."""
    res = book_returns(cfg)
    book_q, cal = res["book_q"], res["cal"]
    nav = pd.concat([read_str_csv(TABLES / "nav_monthly.csv").astype({"ret": float})[["entity", "month", "ret"]],
                     benchmark_nav_monthly(cfg)], ignore_index=True)
    table4 = reconstruction_table(book_q, nav, cal)
    failures, above = benchmark_check(cfg, table4)
    if not above.empty:
        print(f"benchmark quarters with |gap| > benchmark_gap_max ({cfg.gates.benchmark_gap_max}):")
        print(above.merge(book_q, on=["entity", "t", "book_return"]).to_string())
    write_csv(table4, TABLES / "reconstruction.csv")

    funds = [k for k, e in cfg.entities.items() if e.type == "fund"]
    fund4 = table4[table4["entity"].isin(funds)]
    write_csv(gate(fund4, cfg.gates.fund_nav_corr_min), TABLES / "gate.csv")
    b = cfg.bootstrap
    boot = []
    for eid in funds:  # kickoff 5.9; amendment 11: blank quarters left out
        gaps = fund4.loc[fund4["entity"] == eid, "gap"].dropna().to_numpy()
        boot.append([eid, "gap", *bootstrap_mean(gaps, b.mean_block, b.reps, cfg.run.bootstrap_seed, b.lo, b.hi)])
    write_csv(pd.DataFrame(boot, columns=BOOTSTRAP), TABLES / "bootstrap.csv")
    return failures


# instructions/05, A answer 3: `filled` after rB, true where Convention 4.11 supplied rP or rB
BRINSON_QUARTERLY = ["fund", "t", "bucket", "wP", "wB", "rP", "rB", "filled", *EFFECTS]
LINKED = ["fund", "method", "bucket", *EFFECTS, "total"]
LINK_METHODS = {"carino": carino, "menchero": menchero}
SERIES_ORDER = [*EFFECTS, "gap"]  # kickoff 6.2, bootstrap.csv
IDENTITY_TOL = 1e-10  # kickoff 5.5 and 5.6, real data


def fund_label(cfg, fund: str) -> tuple[str, str]:
    """(fund, benchmark) as named on Chart 1: the fund id capitalised and the benchmark's ETF ticker."""
    return fund.capitalize(), cfg.entities[cfg.entities[fund].benchmark].etf_ticker


def chart_1(cfg, fund: str, rP: pd.Series, rB: pd.Series, eff: pd.DataFrame, cal: pd.DataFrame, path: Path) -> None:
    """Chart 1 (instructions/04, Section B; instructions/05, step 5.0): for each k, quarters 1 to k
    linked with Carino; the Total allocation and Total selection against q_end of quarter k, and
    the cumulative excess D_k = R_P,k - R_B,k with both compounded over quarters 1 to k, all in
    percentage points."""
    ks = sorted(rP.index)
    pts = []
    for k in ks:
        sub = [t for t in ks if t <= k]
        linked = carino(rP[sub], rB[sub], eff[eff["t"] <= k], cfg.linking.zero_tol)
        D = np.prod(1 + rP[sub].to_numpy()) - np.prod(1 + rB[sub].to_numpy())
        pts.append([linked["allocation"].sum(), linked["selection"].sum(), D])
    pts = 100 * np.array(pts)
    x = pd.to_datetime(cal.set_index("t").loc[ks, "q_end"])
    name, bench = fund_label(cfg, fund)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.axhline(0, color="0.5", linewidth=0.8)
    ax.plot(x, pts[:, 0], label="Allocation", color="#1f77b4", linewidth=1.8)
    ax.plot(x, pts[:, 1], label="Selection", color="#d62728", linewidth=1.8)
    ax.plot(x, pts[:, 2], label="Total excess (D)", color="black", linestyle="--", linewidth=1.8)
    ax.set_ylabel("Percentage points of cumulative return")
    ax.legend(loc="best", frameon=False)
    fig.suptitle(f"{name} vs {bench}: cumulative allocation and selection (Carino)")
    ax.set_title("Interaction is excluded from the chart and shown in Table 1.", fontsize=9)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=cfg.report.dpi, metadata={"Software": None})
    plt.close(fig)


def section_4(cfg) -> list[str]:
    """Steps 4.1 to 4.3 for every fund that passed the gate: brinson_quarterly.csv, linked.csv,
    the allocation, selection and interaction rows of bootstrap.csv, and Chart 1. Inputs are
    buckets.csv and book_quarterly.csv only (instructions/04, Section B)."""
    failures: list[str] = []
    buckets = read_str_csv(TABLES / "buckets.csv").replace("", np.nan).astype({"t": int, "weight": float, "r": float})
    book_q = read_str_csv(TABLES / "book_quarterly.csv").astype({"t": int, "book_return": float})
    gate_df = read_str_csv(TABLES / "gate.csv").set_index("fund")
    ivv = load_nav(ROOT / "data")[cfg.entities["ivv"].etf_ticker].dropna().index
    cal = quarter_calendar(ivv, holdings_dates(cfg))
    b = cfg.bootstrap

    def side(eid: str, t: int) -> tuple[pd.Series, pd.Series]:
        g = buckets[(buckets["entity"] == eid) & (buckets["t"] == t)].set_index("bucket").reindex(BUCKETS_ORDER)
        return g["weight"], g["r"]

    def book_r(eid: str) -> pd.Series:
        return book_q[book_q["entity"] == eid].set_index("t")["book_return"]

    bq, linked_rows, boot = [], [], []
    for fund, e in cfg.entities.items():
        if e.type != "fund":
            continue
        if gate_df.at[fund, "pass"] != "True":  # Convention 4.19
            print(f"{fund}: excluded from Section 4, it failed the NAV gate (corr {gate_df.at[fund, 'corr']})")
            continue
        rP, rB = book_r(fund), book_r(e.benchmark)
        eff = []
        for t in cal["t"]:
            wP, sP = side(fund, t)
            wB, sB = side(e.benchmark, t)
            ef = brinson_fachler(wP, sP, wB, sB)
            fP, fB, _ = fill_empty(wP, sP, wB, sB)
            err = abs(float(ef.to_numpy().sum()) - (rP[t] - rB[t]))
            if err >= IDENTITY_TOL:
                failures.append(f"{fund} t={t}: Brinson identity misses by {err!r}")
            bq.append(pd.DataFrame({"fund": fund, "t": t, "bucket": BUCKETS_ORDER, "wP": wP.to_numpy(),
                                    "wB": wB.to_numpy(), "rP": fP.to_numpy(), "rB": fB.to_numpy(),
                                    "filled": ~((wP > 0) & (wB > 0)).to_numpy(),
                                    **{c: ef[c].to_numpy() for c in EFFECTS}}))
            eff.append(ef.reset_index().assign(t=t))
        eff = pd.concat(eff, ignore_index=True)[["t", "bucket", *EFFECTS]]
        D = float(np.prod(1 + rP.to_numpy()) - np.prod(1 + rB.to_numpy()))
        for method, f in LINK_METHODS.items():
            lk = f(rP, rB, eff, cfg.linking.zero_tol)
            lk = pd.concat([lk, pd.DataFrame([["Total", *lk[EFFECTS].sum()]], columns=lk.columns)], ignore_index=True)
            lk["total"] = lk[EFFECTS].sum(axis=1)
            err = abs(float(lk["total"].iloc[-1]) - D)
            if err >= IDENTITY_TOL:
                failures.append(f"{fund} {method}: linked total misses D by {err!r}")
            linked_rows.append(lk.assign(fund=fund, method=method)[LINKED])
        tot = eff.groupby("t")[EFFECTS].sum()  # quarterly totals over buckets, unlinked
        idx = stationary_bootstrap_indices(len(tot), b.mean_block, b.reps, cfg.run.bootstrap_seed)
        for s in EFFECTS:
            boot.append([fund, s, *bootstrap_mean(tot[s].to_numpy(), b.mean_block, b.reps, cfg.run.bootstrap_seed,
                                                  b.lo, b.hi, idx=idx)])
        chart_1(cfg, fund, rP, rB, eff, cal, FIGURES / f"{fund}_alloc_vs_sel.png")
    write_csv(pd.concat(bq, ignore_index=True)[BRINSON_QUARTERLY], TABLES / "brinson_quarterly.csv")
    write_csv(pd.concat(linked_rows, ignore_index=True), TABLES / "linked.csv")

    gap = read_str_csv(TABLES / "bootstrap.csv")
    gap = gap[gap["series"] == "gap"].astype({c: float for c in BOOTSTRAP[2:]})
    out = pd.concat([pd.DataFrame(boot, columns=BOOTSTRAP), gap], ignore_index=True)
    order = {f: i for i, f in enumerate(cfg.entities)}
    out = out.assign(_f=out["fund"].map(order), _s=out["series"].map(SERIES_ORDER.index))
    write_csv(out.sort_values(["_f", "_s"], kind="mergesort")[BOOTSTRAP], TABLES / "bootstrap.csv")
    return failures


FACTOR_FIT = ["series_id", "series_kind", "coef", "value", "se_hac", "t_hac", "r2", "resid_vol_ann", "n_months"]
FIT_COLS = ["value", "se_hac", "t_hac"]
# kickoff 6.2 with `n_months` after `year` (instructions/05, C)
FACTOR_BY_YEAR = ["series_id", "year", "n_months", "excess_return", "mkt", "smb", "hml", "rmw", "cma", "umd", ALPHA,
                  "residual", "r2_full"]
YEAR_TOL = 1e-12  # instructions/05, D 5.1: year rows sum to the year's excess return
FACTOR_LABELS = {"mkt": "Mkt-RF", "smb": "SMB", "hml": "HML", "rmw": "RMW", "cma": "CMA", "umd": "UMD"}


def factor_months(cfg, ff: pd.DataFrame) -> pd.PeriodIndex:
    """Kickoff 3.3 with amendment 7 (instructions/05, C): the month after the first holdings date to
    the earlier of the last return month and the last French month."""
    first = pd.Period(cfg.sample.first_holdings_date, freq="M") + 1
    last = min(pd.Period(cfg.sample.last_return_date, freq="M"), ff.index.max())
    return pd.period_range(first, last, freq="M", name="month")


def monthly_series(cfg, months: pd.PeriodIndex) -> dict[str, tuple[str, pd.Series]]:
    """D-22: series_id -> (series_kind, monthly return by month) for `{fund}_book`, `{fund}_nav`,
    then `{benchmark}_book`, in config order; a missing month has no row (D-33)."""
    def by_month(df: pd.DataFrame, eid: str) -> pd.Series:
        r = df[df["entity"] == eid].set_index("month")["ret"]
        r.index = pd.PeriodIndex(r.index, freq="M", name="month")
        return r[r.index.isin(months)]

    book = read_str_csv(TABLES / "book_monthly.csv").astype({"ret": float})
    nav = read_str_csv(TABLES / "nav_monthly.csv").astype({"ret": float})
    out = {}
    for kind in ("fund", "benchmark"):
        for eid, e in cfg.entities.items():
            if e.type != kind:
                continue
            out[f"{eid}_book"] = ("book", by_month(book, eid))
            if kind == "fund":
                out[f"{eid}_nav"] = ("nav", by_month(nav, eid))
    return out


def chart_2(cfg, fund: str, rb: pd.DataFrame, path: Path) -> None:
    """Chart 2 (instructions/05, Section C): the 6 rolling book betas against window end."""
    x = rb.index.to_timestamp(how="end").normalize()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.axhline(0, color="0.5", linewidth=0.8)
    for f in cfg.factors.names:
        ax.plot(x, rb[f].to_numpy(), label=FACTOR_LABELS[f], linewidth=1.6)
    ax.set_ylabel("Beta")
    ax.legend(loc="best", frameon=False, ncol=3)
    ax.set_title(f"{fund.capitalize()}: rolling {cfg.factors.rolling_window}-month factor betas (book)")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=cfg.report.dpi, metadata={"Software": None})
    plt.close(fig)


HOLDINGS_EXPOSURES = ["fund", "holdings_date", "side", "mkt", "smb", "hml", "rmw", "cma", "umd", "excluded_weight"]
SIDES = ["fund", "benchmark", "active"]
EXPOSURE_DATES = ["2019-09-30", "2022-12-31", "2026-06-30"]  # instructions/05, E 4


def priced_mapped_weights() -> tuple[pd.DataFrame, list[str]]:
    """Per (entity, t, yf_ticker): the summed weight and the FF12 bucket of the priced, mapped
    positions of POSITION_RETURNS (instructions/05, C: the stock universe and the exposures)."""
    pos = read_str_csv(PROCESSED / "position_returns.csv").astype({"t": int, "weight": float})
    smap = read_str_csv(PROCESSED / "security_map.csv").set_index("sec_id")["yf_ticker"]
    pm = pos[~pos["bucket"].isin(NEUTRAL)].assign(yf_ticker=lambda d: d["sec_id"].map(smap))
    g = pm.groupby(["entity", "t", "yf_ticker"], sort=True)
    two = g["bucket"].nunique()
    failures = [f"{e} t={t}: {tk} sits in 2 buckets" for (e, t, tk), n in two.items() if n > 1]
    return g.agg(weight=("weight", "sum"), bucket=("bucket", "first")).reset_index(), failures


def chart_exposures(cfg, fund: str, hb: pd.DataFrame, rb: pd.DataFrame, path: Path) -> None:
    """instructions/05, C: 2 x 3 panels, 1 per factor. Holdings-based fund exposure at each h
    (markers) and the rolling returns-based book beta whose window ends at h's month (line)."""
    x = pd.to_datetime(hb["holdings_date"])
    rbh = rb.reindex(pd.PeriodIndex(x, freq="M"))
    fig, axes = plt.subplots(2, 3, figsize=(10, 6), sharex=True)
    for ax, f in zip(axes.flat, cfg.factors.names):
        ax.axhline(0, color="0.5", linewidth=0.8)
        ax.plot(x, rbh[f].to_numpy(), color="#1f77b4", linewidth=1.6,
                label=f"Returns-based, rolling {cfg.factors.rolling_window} months (book)")
        ax.plot(x, hb[f].to_numpy(), "o", color="#d62728", markersize=3.5, label="Holdings-based")
        ax.set_title(FACTOR_LABELS[f], fontsize=10)
        ax.tick_params(axis="x", labelrotation=45, labelsize=8)
    for ax in axes[:, 0]:
        ax.set_ylabel("Beta")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False)
    fig.suptitle(f"{fund.capitalize()}: holdings-based vs returns-based factor exposures")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=cfg.report.dpi, metadata={"Software": None})
    plt.close(fig)


def exposures(cfg, ff: pd.DataFrame, funds: list[str], rolls: dict[str, pd.DataFrame]) -> list[str]:
    """Step 5.2 (instructions/05, C): stock betas at each holdings date h over the 36 calendar months
    ending at h's month, the fund, benchmark and active exposures to holdings_exposures.csv with
    each side's excluded weight, the exposures chart per fund and the IVV sanity check (D 5.2)."""
    names = list(cfg.factors.names)
    fc = cfg.factors
    w, failures = priced_mapped_weights()
    mret = monthly_returns(load_prices(ROOT / "data"))
    excess = mret.sub(ff["rf"].reindex(mret.index), axis=0)  # Convention 4.15
    ivv = load_nav(ROOT / "data")[cfg.entities["ivv"].etf_ticker].dropna().index
    cal = quarter_calendar(ivv, holdings_dates(cfg))
    sides = {fund: (fund, cfg.entities[fund].benchmark) for fund in funds}
    in_scope = {e for pair in sides.values() for e in pair}
    rows, diag = [], []
    for t, h in zip(cal["t"], cal["holdings_date"]):
        wt = w[w["t"] == t]
        universe = sorted(set(wt.loc[wt["entity"].isin(in_scope), "yf_ticker"]))
        betas = stock_betas(excess.reindex(columns=universe), ff[names], pd.Period(h, freq="M"),
                            fc.stock_beta_window, fc.stock_beta_min_obs)
        for fund, (eid_f, eid_b) in sides.items():
            out = {}
            for side, eid in (("fund", eid_f), ("benchmark", eid_b)):
                g = wt[wt["entity"] == eid].set_index("yf_ticker")
                own = betas.reindex(g.index).notna().all(axis=1)
                has = fallback_betas(betas.reindex(g.index), g["bucket"]).notna().all(axis=1)
                out[side] = holdings_exposure(g["weight"], betas, g["bucket"])
                excl = 1.0 - float(g.loc[has, "weight"].sum())  # book weights sum to 1 (Convention 4.5)
                rows.append([fund, str(h), side, *out[side][names], excl])
                diag.append([fund, side, float(g.loc[has & ~own, "weight"].sum()), float(g.loc[~has, "weight"].sum()),
                             int((has & ~own).sum()), int((~has).sum())])
            rows.append([fund, str(h), "active", *(out["fund"] - out["benchmark"])[names], np.nan])
    hx = pd.DataFrame(rows, columns=HOLDINGS_EXPOSURES)
    order = {fd: i for i, fd in enumerate(funds)}
    hx = hx.assign(_f=hx["fund"].map(order), _s=hx["side"].map(SIDES.index))
    hx = hx.sort_values(["_f", "holdings_date", "_s"], kind="mergesort")[HOLDINGS_EXPOSURES].reset_index(drop=True)
    write_csv(hx, TABLES / "holdings_exposures.csv")
    for fund in funds:
        chart_exposures(cfg, fund, hx[(hx["fund"] == fund) & (hx["side"] == "fund")], rolls[f"{fund}_book"],
                        FIGURES / f"{fund}_exposures_hb_vs_rb.png")

    d = pd.DataFrame(diag, columns=["fund", "side", "fallback_weight", "no_beta_weight", "n_fallback", "n_no_beta"])
    with pd.option_context("display.width", 250):
        print("beta coverage per side, the largest value over the holdings dates:")
        print(d.groupby(["fund", "side"], sort=False).max().to_string())
        print("holdings-based exposures at the review dates (instructions/05, E 4):")
        print(hx[hx["holdings_date"].isin(EXPOSURE_DATES)].to_string())
        ivv_side = [fd for fd in funds if cfg.entities[fd].benchmark == "ivv"]
        if ivv_side:
            s = hx[(hx["fund"] == ivv_side[0]) & (hx["side"] == "benchmark")]
            print("IVV sanity check (instructions/05, D 5.2): holdings-based ivv_book market beta at every h")
            print(s[["holdings_date", "mkt", "excluded_weight"]].to_string())
    return failures


def section_5(cfg) -> list[str]:
    """Steps 5.1 and 5.2 (instructions/05, Section C): the full-sample HAC fit of every series to
    factor_fit.csv, Table 2 to factor_by_year.csv, the rolling book betas to rolling_betas.csv,
    Chart 2 per fund, then the holdings-based exposures (`exposures`). Funds that failed the gate
    keep their factor_fit rows only (Convention 4.19)."""
    failures: list[str] = []
    names = list(cfg.factors.names)
    ff = load_french(ROOT / "data")
    months = factor_months(cfg, ff)
    fac = ff.loc[months, names]
    gate_df = read_str_csv(TABLES / "gate.csv").set_index("fund")
    excluded = {f for f in gate_df.index if gate_df.at[f, "pass"] != "True"}
    for f in sorted(excluded):
        print(f"{f}: excluded from Table 2, rolling betas and Chart 2, it failed the NAV gate")

    fit_rows, years, rolls, rb_by = [], [], [], {}
    for sid, (kind, ret) in monthly_series(cfg, months).items():
        excess = ret - ff["rf"].reindex(ret.index)  # Convention 4.15
        fit = returns_based(excess, fac, cfg.factors.hac_maxlags)
        tab = pd.DataFrame({c: fit[c] for c in FIT_COLS}).rename_axis("coef").reset_index()
        fit_rows.append(tab.assign(series_id=sid, series_kind=kind, r2=fit["r2"],
                                   resid_vol_ann=fit["resid_vol_ann"], n_months=fit["n_months"]))
        if sid.rsplit("_", 1)[0] in excluded:
            continue
        t2 = factor_contrib_by_year(excess, fac, fit)
        err = (t2[[*names, ALPHA, "residual"]].sum(axis=1) - t2["excess_return"]).abs().max()
        if err >= YEAR_TOL:
            failures.append(f"{sid}: Table 2 year rows miss the excess return by {err!r}")
        years.append(t2.assign(series_id=sid))
        if kind == "book":  # D-23
            rb = rolling_betas(excess, fac, cfg.factors.rolling_window)
            rb_by[sid] = rb
            rolls.append(rb.reset_index().assign(series_id=sid, month_end=rb.index.astype(str)))
            eid = sid.rsplit("_", 1)[0]
            if cfg.entities[eid].type == "fund":
                chart_2(cfg, eid, rb, FIGURES / f"{eid}_rolling_betas.png")
    write_csv(pd.concat(fit_rows, ignore_index=True)[FACTOR_FIT], TABLES / "factor_fit.csv")
    write_csv(pd.concat(years, ignore_index=True)[FACTOR_BY_YEAR], TABLES / "factor_by_year.csv")
    write_csv(pd.concat(rolls, ignore_index=True)[["series_id", "month_end", *names]], TABLES / "rolling_betas.csv")
    fits = pd.concat(fit_rows, ignore_index=True)
    print("IVV sanity check (instructions/05, D 5.2): full-sample returns-based ivv_book market beta")
    print(fits.loc[(fits["series_id"] == "ivv_book") & (fits["coef"] == "mkt"),
                   ["series_id", "coef", "value", "se_hac", "n_months"]].to_string())
    funds = [k for k, e in cfg.entities.items() if e.type == "fund" and k not in excluded]
    return failures + exposures(cfg, ff, funds, rb_by)


# kickoff 6.2 with the 2 unmapped columns after `active_share` (instructions/06, C)
RISK_QUARTERLY = ["fund", "holdings_date", "active_share", "unmapped_weight_fund", "unmapped_weight_bench",
                  "te_exante", "excluded_weight_fund", "excluded_weight_bench", "n_names", "max_fill_share",
                  "delta_lw", "ridged"]
CTE_POSITIONS = ["fund", "holdings_date", "ticker", "bucket", "a", "mcte", "cte"]
CTE_SECTORS = ["fund", "holdings_date", "bucket", "cte"]
TE_REALISED = ["fund", "te_realised", "te_exante_mean", "n_months"]  # D-25
EULER_TOL = 1e-12  # kickoff 5.10: sum CTE = TE


def chart_3(cfg, fund: str, dec: pd.DataFrame, te: float, h: str, path: Path) -> None:
    """Chart 3 (instructions/06, C): the `risk.top_n_positions` largest CTE positions at h by |CTE|,
    as horizontal bars in percentage points of annualised TE, sorted by CTE with the largest at
    the top, positive and negative in 2 colours, with a vertical zero line."""
    n = cfg.risk.top_n_positions
    top = dec.assign(_abs=dec["cte"].abs()).sort_values(["_abs", "ticker"], ascending=[False, True],
                                                         kind="mergesort").head(n)
    top = top.sort_values(["cte", "ticker"], ascending=[True, False], kind="mergesort")  # barh draws bottom-up
    share = float(top["cte"].sum()) / te
    name, bench = fund_label(cfg, fund)
    fig, ax = plt.subplots(figsize=(8, 6))
    vals = 100 * top["cte"].to_numpy()
    ax.barh(top["ticker"], vals, color=np.where(vals >= 0, "#d62728", "#1f77b4"))
    ax.axvline(0, color="0.3", linewidth=0.8)
    ax.set_xlabel("Contribution to ex-ante tracking error (percentage points, annualised)")
    fig.suptitle(f"{name} vs {bench}: top {n} contributions to ex-ante tracking error, {h}")
    ax.set_title(f"Ex-ante TE {100 * te:.2f}%; these {n} positions explain {100 * share:.1f}% of it", fontsize=9)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=cfg.report.dpi, metadata={"Software": None})
    plt.close(fig)


def realised_te(cfg, funds: list[str], risk_q: pd.DataFrame) -> pd.DataFrame:
    """D-25 (instructions/06, C): per fund, std (ddof 1) of the monthly book active return (fund
    book minus its benchmark book) x sqrt(months_per_year) over the 83 months of the Section 5
    monthly sample (`factor_months`), the mean of the ex-ante TEs and n_months."""
    months = factor_months(cfg, load_french(ROOT / "data"))
    book = read_str_csv(TABLES / "book_monthly.csv").astype({"ret": float})
    rows = []
    for fund in funds:
        r = {e: book[book["entity"] == e].set_index("month")["ret"] for e in (fund, cfg.entities[fund].benchmark)}
        act = (r[fund] - r[cfg.entities[fund].benchmark]).reindex(months.astype(str)).dropna()
        te_ex = risk_q.loc[risk_q["fund"] == fund, "te_exante"]
        rows.append([fund, float(act.std(ddof=1) * np.sqrt(cfg.risk.months_per_year)), float(te_ex.mean()), len(act)])
    return pd.DataFrame(rows, columns=TE_REALISED)


def section_6(cfg) -> list[str]:
    """Steps 6.1 and 6.2 (instructions/06, C) for every fund that passed the gate, at each of the
    28 holdings dates: active share on issuer weights (all positions), the ex-ante TE and its Euler
    split on the risk weights over the window of daily returns ending at q_start(h), filled and
    shrunk; then risk_quarterly.csv, cte_positions.csv, cte_sectors.csv, te_realised.csv and
    Chart 3 at the last holdings date."""
    rk = cfg.risk
    if (rk.daily_to_monthly, rk.months_per_year) != (DAILY_TO_MONTHLY, MONTHS_PER_YEAR):
        return [f"config risk ({rk.daily_to_monthly}, {rk.months_per_year}) differs from kickoff 5.10 (21, 12)"]
    failures: list[str] = []
    gate_df = read_str_csv(TABLES / "gate.csv").set_index("fund")
    funds = []
    for fund, e in cfg.entities.items():
        if e.type != "fund":
            continue
        if gate_df.at[fund, "pass"] != "True":  # Convention 4.19
            print(f"{fund}: excluded from Section 6, it failed the NAV gate (corr {gate_df.at[fund, 'corr']})")
            continue
        funds.append(fund)
    pos = read_str_csv(PROCESSED / "position_returns.csv").astype({"t": int, "weight": float})
    smap = read_str_csv(PROCESSED / "security_map.csv")
    rets = daily_returns(load_prices(ROOT / "data"))
    ivv = load_nav(ROOT / "data")[cfg.entities["ivv"].etf_ticker].dropna().index
    cal = quarter_calendar(ivv, holdings_dates(cfg))
    last_h = str(cfg.sample.last_holdings_date)

    rq, cte_p, cte_s, fills, last = [], [], [], [], {}
    for fund in funds:
        bench = cfg.entities[fund].benchmark
        for t, h, qs in zip(cal["t"], cal["holdings_date"], cal["q_start"]):
            posP = pos[(pos["entity"] == fund) & (pos["t"] == t)]
            posB = pos[(pos["entity"] == bench) & (pos["t"] == t)]
            AS = active_share(issuer_weights(posP, smap), issuer_weights(posB, smap))
            unm = [float(p.loc[p["bucket"] == "Unmapped", "weight"].sum()) for p in (posP, posB)]
            excl = [float(p.loc[p["bucket"].isin(NEUTRAL), "weight"].sum()) for p in (posP, posB)]
            wP, wB = risk_weights(posP, smap), risk_weights(posB, smap)
            union = sorted(set(wP.index) | set(wB.index))
            buckets = ticker_buckets(smap, union)
            X = window_daily(rets[union], qs, rk.cov_months)
            filled, share = fill_daily(X, buckets)
            S, info = active_cov(filled, qs, rk.cov_months, rk.max_cond)
            a = wP.reindex(union, fill_value=0.0) - wB.reindex(union, fill_value=0.0)
            dec = te_decomposition(a, S).assign(bucket=buckets.to_numpy())
            te = float(np.sqrt(MONTHS_PER_YEAR * a.to_numpy() @ S.to_numpy() @ a.to_numpy()))
            err = abs(float(dec["cte"].sum()) - te)
            if err >= EULER_TOL:
                failures.append(f"{fund} {h}: sum CTE misses TE by {err!r}")
            rq.append([fund, str(h), AS, *unm, te, *excl, len(union), float(share.max()), info["delta_lw"],
                       info["ridged"]])
            cte_p.append(dec.assign(fund=fund, holdings_date=str(h))[CTE_POSITIONS])
            sec = dec.groupby("bucket")["cte"].sum().reindex(BUCKETS_ORDER[:12], fill_value=0.0)
            cte_s.append(pd.DataFrame({"fund": fund, "holdings_date": str(h), "bucket": sec.index, "cte": sec.to_numpy()}))
            fills.append([fund, str(h), info["n_days"], int((share > 0).sum()), share.idxmax(), float(share.max()),
                          info["cond_before"], info["ridge"]])
            if str(h) == last_h:
                last[fund] = (dec, te, share)
    risk_q = pd.DataFrame(rq, columns=RISK_QUARTERLY)
    write_csv(risk_q, TABLES / "risk_quarterly.csv")
    write_csv(pd.concat(cte_p, ignore_index=True), TABLES / "cte_positions.csv")
    cte_sec = pd.concat(cte_s, ignore_index=True)
    write_csv(cte_sec, TABLES / "cte_sectors.csv")
    write_csv(realised_te(cfg, funds, risk_q), TABLES / "te_realised.csv")
    for fund in funds:
        dec, te, _ = last[fund]
        chart_3(cfg, fund, dec, te, last_h, FIGURES / f"{fund}_cte_top15.png")

    sec_err = (cte_sec.groupby(["fund", "holdings_date"])["cte"].sum()
               - risk_q.set_index(["fund", "holdings_date"])["te_exante"]).abs().max()
    if sec_err >= EULER_TOL:
        failures.append(f"sector CTE sums miss TE by {sec_err!r}")
    f = pd.DataFrame(fills, columns=["fund", "holdings_date", "n_days", "n_filled", "max_fill_ticker",
                                     "max_fill_share", "cond_before", "ridge"])
    with pd.option_context("display.width", 250):
        print("fill and conditioning per date:")
        print(f.to_string())
        print(f"largest |sum CTE - TE| over funds and dates and over sector sums: {sec_err!r}")
    return failures


SECTIONS = {1: section_1, 2: section_2, 3: section_3, 4: section_4, 5: section_5, 6: section_6}


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
