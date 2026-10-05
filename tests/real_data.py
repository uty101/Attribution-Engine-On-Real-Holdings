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
