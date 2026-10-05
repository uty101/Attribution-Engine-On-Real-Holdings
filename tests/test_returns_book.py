import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from attrib.config import load_config
from attrib.edgar import holdings_dates
from attrib.mapping import SECURITY_MAP, security_map_from_dir
from attrib.returns import (
    BUCKETS_ORDER,
    book_monthly,
    book_quarter,
    book_return,
    bucket_table,
    load_nav,
    load_prices,
    quarter_calendar,
)

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
TOL = 1e-12  # kickoff Section 8, step 3.2


def _smap(rows):
    """SECURITY_MAP rows given as (sec_id, ticker, ff12, map_status)."""
    out = pd.DataFrame(
        [[s, "cusip", t, t, "", "", None, None, f, m, "openfigi"] for s, t, f, m in rows], columns=SECURITY_MAP
    )
    return out


def _book(rows):
    """HOLDINGS rows given as (sec_id, value_usd)."""
    return pd.DataFrame(
        [["fund", "2019-12-31", s, "", s, s, v, 1.0] for s, v in rows],
        columns=["entity", "period_date", "cusip", "isin", "sec_id", "name", "value_usd", "shares"],
    ).assign(t=1)


DATES = pd.DatetimeIndex(["2019-12-31", "2020-01-15", "2020-01-31", "2020-02-28", "2020-03-16", "2020-03-31"])


def test_hand_built_three_stock_quarter():
    """3 stocks, 1 quarter, weights 0.5 / 0.3 / 0.2 (values 50, 30, 20).

    AAA (BusEq) 100 -> 110: r = 0.10. BBB (BusEq) 50 -> 45: r = -0.10. CCC (Hlth) 20 -> 25: r = 0.25.
    Book return = 0.5 * 0.10 + 0.3 * -0.10 + 0.2 * 0.25 = 0.07.
    BusEq weight 0.8, return (0.05 - 0.03) / 0.8 = 0.025. Hlth weight 0.2, return 0.25.
    """
    prices = pd.DataFrame(
        {"AAA": [100, 104, 102, 108, 90, 110], "BBB": [50, 51, 49, 47, 40, 45], "CCC": [20, 21, 22, 23, 24, 25]},
        index=DATES, dtype="float64",
    )
    smap = _smap([("AAA", "AAA", "BusEq", "mapped"), ("BBB", "BBB", "BusEq", "mapped"), ("CCC", "CCC", "Hlth", "mapped")])
    pos = book_quarter(_book([("AAA", 50), ("BBB", 30), ("CCC", 20)]), smap, prices, DATES[0], DATES[-1])
    bk = bucket_table(pos)
    print(pos.to_string())
    print(bk.to_string())
    assert np.allclose(pos["weight"], [0.5, 0.3, 0.2], rtol=0, atol=TOL)
    assert np.allclose(pos["r"], [0.10, -0.10, 0.25], rtol=0, atol=TOL)
    assert abs(book_return(bk) - 0.07) < TOL
    b = bk.set_index("bucket")
    assert b.index.tolist() == BUCKETS_ORDER
    assert abs(b.at["BusEq", "weight"] - 0.8) < TOL and abs(b.at["BusEq", "r"] - 0.025) < TOL
    assert abs(b.at["Hlth", "weight"] - 0.2) < TOL and abs(b.at["Hlth", "r"] - 0.25) < TOL
    assert b.drop(["BusEq", "Hlth"])["weight"].eq(0).all() and b.drop(["BusEq", "Hlth"])["r"].isna().all()
    assert not pos["delisted_in_quarter"].any()


def test_delisted_mid_quarter():
    """DDD's prices end on 2020-02-28 at 60 from 80 at q_start: r = 60 / 80 - 1 = -0.25, held as cash
    after that (Convention 4.8). EEE has a ticker but no close on q_start, so it is Unpriced, and
    FFF has no ticker, so it is Unmapped; both earn the priced, mapped return (Convention 4.9)."""
    prices = pd.DataFrame(
        {"AAA": [100, 101, 102, 103, 104, 110], "DDD": [80, 75, 70, 60, np.nan, np.nan],
         "EEE": [np.nan, 10, 11, 12, 13, 14]},
        index=DATES, dtype="float64",
    )
    smap = _smap([("AAA", "AAA", "BusEq", "mapped"), ("DDD", "DDD", "Enrgy", "mapped"),
                  ("EEE", "EEE", "Money", "mapped"), ("FFF", "", "", "no_match")])
    book = _book([("AAA", 40), ("DDD", 40), ("EEE", 10), ("FFF", 10)])
    pos = book_quarter(book, smap, prices, DATES[0], DATES[-1]).set_index("sec_id")
    print(pos.to_string())
    assert pos.at["DDD", "delisted_in_quarter"] and pos.at["DDD", "last_price_date"] == "2020-02-28"
    assert abs(pos.at["DDD", "r"] - -0.25) < TOL
    assert not pos.at["AAA", "delisted_in_quarter"] and pos.at["AAA", "last_price_date"] == "2020-03-31"
    rpm = (0.4 * 0.10 + 0.4 * -0.25) / 0.8
    assert pos.at["EEE", "bucket"] == "Unpriced" and abs(pos.at["EEE", "r"] - rpm) < TOL
    assert pos.at["FFF", "bucket"] == "Unmapped" and abs(pos.at["FFF", "r"] - rpm) < TOL
    assert abs(book_return(bucket_table(pos.reset_index())) - rpm) < TOL
    m = book_monthly(book, smap, prices, DATES[0], DATES[-1])
    print(m.to_string())
    # Convention 4.12: DDD is flat at 60 in March, so March's V moves only with AAA
    v = [1.0, (0.4 * 102 / 100 + 0.4 * 70 / 80) / 0.8, (0.4 * 103 / 100 + 0.4 * 60 / 80) / 0.8,
         (0.4 * 110 / 100 + 0.4 * 60 / 80) / 0.8]
    assert np.allclose(m.to_numpy(), np.array(v[1:]) / np.array(v[:-1]) - 1, rtol=0, atol=TOL)
    assert abs(np.prod(1 + m.to_numpy()) - 1 - rpm) < TOL


@lru_cache(maxsize=1)
def _real():
    """Every book in H rebuilt from data/raw/ with the Section 1 code (rule 7), the security map
    from data/raw/ and data/manual/, the price panel and the quarter calendar."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import run_all

    H = holdings_dates(CFG)
    failures: list[str] = []
    books = []
    for eid, e in CFG.entities.items():
        if e.type == "fund":
            book, _ = run_all.fund_books(eid, H, CFG.edgar.implied_price_lo, CFG.edgar.implied_price_hi, failures)
        else:
            book, _ = run_all.benchmark_books(eid, H, failures)
        books.append(book)
    assert failures == []
    ivv = load_nav(ROOT / "data")[CFG.entities["ivv"].etf_ticker].dropna().index
    cal = quarter_calendar(ivv, H)
    return pd.concat(books, ignore_index=True), security_map_from_dir(ROOT / "data"), load_prices(ROOT / "data"), cal


def _each_real_book():
    books, smap, prices, cal = _real()
    for _, q in cal.iterrows():
        for eid, b in books[books["period_date"] == str(q["holdings_date"])].groupby("entity", sort=True):
            yield eid, q, b.assign(t=q["t"]), smap, prices


def test_bucket_identity_every_real_book():
    worst, n = 0.0, 0
    for eid, q, b, smap, prices in _each_real_book():
        pos = book_quarter(b, smap, prices, q["q_start"], q["q_end"])
        pm = ~pos["bucket"].isin(["Unmapped", "Unpriced"])
        r_pm = (pos.loc[pm, "weight"] * pos.loc[pm, "r"]).sum() / pos.loc[pm, "weight"].sum()
        bk = bucket_table(pos)
        assert abs(bk["weight"].sum() - 1) < TOL
        worst = max(worst, abs(book_return(bk) - r_pm))
        n += 1
    print(f"{n} books, max |sum w_s r_s - priced, mapped return| = {worst:.3e}")
    assert n == 5 * 28
    assert worst < TOL


def test_monthly_compounds_to_quarterly():
    worst, n = 0.0, 0
    for eid, q, b, smap, prices in _each_real_book():
        r = book_return(bucket_table(book_quarter(b, smap, prices, q["q_start"], q["q_end"])))
        m = book_monthly(b, smap, prices, q["q_start"], q["q_end"])
        assert len(m) == 3
        worst = max(worst, abs(float(np.prod(1 + m.to_numpy())) - 1 - r))
        n += 1
    print(f"{n} books, max |compounded monthly - quarterly| = {worst:.3e}")
    assert n == 5 * 28
    assert worst < TOL
