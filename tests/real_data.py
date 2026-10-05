"""BUCKETS for every entity and quarter, rebuilt from data/raw/ and data/manual/ through the
Section 3 functions (rule 7). Shared by the Section 4 tests; not a test module."""

from functools import lru_cache

import pandas as pd
from test_returns_book import ROOT, _real

from attrib.returns import apply_return_overrides, book_quarter, bucket_table, return_overrides_with_t


@lru_cache(maxsize=1)
def real_buckets() -> tuple[pd.DataFrame, pd.DataFrame]:
    """(BUCKETS of all 5 entities x 28 quarters, QUARTERS), with the `quarter_return` overrides
    applied between `book_quarter` and `bucket_table` as in `run_all.book_returns` (D-16)."""
    books, smap, prices, cal = _real()
    ov = return_overrides_with_t(
        pd.read_csv(ROOT / "data" / "manual" / "overrides.csv", dtype=str, keep_default_na=False), cal
    )
    pos = []
    for _, q in cal.iterrows():
        for eid, b in books[books["period_date"] == str(q["holdings_date"])].groupby("entity", sort=True):
            pos.append(book_quarter(b.assign(t=q["t"]), smap, prices, q["q_start"], q["q_end"]))
    return bucket_table(apply_return_overrides(pd.concat(pos, ignore_index=True), ov)), cal


def side(buckets: pd.DataFrame, eid: str, t: int) -> tuple[pd.Series, pd.Series]:
    """(weight, r) by bucket for 1 entity and quarter."""
    g = buckets[(buckets["entity"] == eid) & (buckets["t"] == t)].set_index("bucket")
    return g["weight"], g["r"]


@lru_cache(maxsize=1)
def real_risk_inputs(fund: str = "akre", h: str = "2026-06-30") -> dict:
    """1 fund and its benchmark at holdings date h, rebuilt from data/raw/ and data/manual/ through
    the Section 1 and 3 code (rule 7): POSITION_RETURNS of each side (`posP`, `posB`), SECURITY_MAP,
    the daily returns of the union of both sides' priced, mapped tickers, their FF12 buckets, the
    risk weights `wP` and `wB` and q_start(h). Used by the Section 6 tests."""
    import sys
    from datetime import date

    from test_returns_book import CFG

    from attrib.edgar import holdings_dates
    from attrib.mapping import security_map_from_dir
    from attrib.returns import daily_returns, load_nav, load_prices, quarter_calendar
    from attrib.risk import risk_weights, ticker_buckets

    sys.path.insert(0, str(ROOT / "scripts"))
    import run_all

    d = date.fromisoformat(h)
    bench = CFG.entities[fund].benchmark
    failures: list[str] = []
    bookP, _ = run_all.fund_books(fund, [d], CFG.edgar.implied_price_lo, CFG.edgar.implied_price_hi, failures)
    bookB, _ = run_all.benchmark_books(bench, [d], failures)
    assert failures == []
    smap = security_map_from_dir(ROOT / "data")
    prices = load_prices(ROOT / "data")
    ivv = load_nav(ROOT / "data")[CFG.entities["ivv"].etf_ticker].dropna().index
    cal = quarter_calendar(ivv, holdings_dates(CFG))
    q = cal[cal["holdings_date"] == d].iloc[0]
    posP = book_quarter(bookP.assign(t=q["t"]), smap, prices, q["q_start"], q["q_end"])
    posB = book_quarter(bookB.assign(t=q["t"]), smap, prices, q["q_start"], q["q_end"])
    wP, wB = risk_weights(posP, smap), risk_weights(posB, smap)
    union = sorted(set(wP.index) | set(wB.index))
    return {
        "posP": posP, "posB": posB, "smap": smap, "wP": wP, "wB": wB, "q_start": q["q_start"],
        "returns_d": daily_returns(prices[union]), "buckets": ticker_buckets(smap, union),
    }
