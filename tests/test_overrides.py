import pandas as pd

from attrib.mapping import FALLBACK, OVERRIDES, build_security_map
from attrib.returns import POSITION_RETURNS, QUARTERS, apply_return_overrides, return_overrides_with_t
from test_mapping import FF12, _figi, _sic, _tickers


def _overrides(rows=()):
    return pd.DataFrame(list(rows), columns=OVERRIDES).astype(str)


def _changed(before: pd.DataFrame, after: pd.DataFrame, key: str) -> set[str]:
    b, a = before.set_index(key).astype(str), after.set_index(key).astype(str)
    return {k for k in b.index if not b.loc[k].equals(a.loc[k])}


def test_each_override_changes_only_named_rows():
    # ticker and cik rows act through build_security_map: each changes its own sec_id's row only.
    figi = _figi([
        ["111111111", "cusip", "ok", "1", "F1", "", "AAA", "ALPHA CO", "US", "Equity", "Common Stock"],
        ["222222222", "cusip", "ok", "1", "F2", "", "GONE", "BETA CO", "US", "Equity", "Common Stock"],
        ["333333333", "cusip", "No identifier found.", "", "", "", "", "", "", "", ""],
    ])
    tickers = _tickers([[1, "AAA", "ALPHA CO"], [3, "CCC", "GAMMA CO"]])
    sic = _sic([[1, "ALPHA CO", "3571", ""], [2, "BETA CO", "2834", ""], [3, "GAMMA CO", "6021", ""]])
    fb = pd.DataFrame(columns=FALLBACK).astype(str)
    base = build_security_map(figi, fb, _overrides(), tickers, sic, FF12)
    rows = [
        ["ticker", "333333333", "", "CCC", "Gamma Co"],
        ["cik", "222222222", "", "2", "Beta Co"],
    ]
    for row in rows:
        after = build_security_map(figi, fb, _overrides([row]), tickers, sic, FF12)
        print(pd.concat([base[base["sec_id"] == row[1]], after[after["sec_id"] == row[1]]]).to_string())
        assert _changed(base, after, "sec_id") == {row[1]}

    # quarter_return rows act through apply_return_overrides on POSITION_RETURNS.
    pos = pd.DataFrame(
        [
            ["fund", 1, "111111111", "111111111", "111111", "AAA", "BusEq", 0.5, 0.10, False, "2020-03-31"],
            ["fund", 1, "222222222", "222222222", "222222", "GONE", "Hlth", 0.3, 0.20, False, "2020-03-31"],
            ["fund", 1, "333333333", "333333333", "333333", "", "Unmapped", 0.2, 0.1375, False, ""],
            ["fund", 2, "111111111", "111111111", "111111", "AAA", "BusEq", 0.6, 0.05, False, "2020-06-30"],
            ["fund", 2, "222222222", "222222222", "222222", "GONE", "Hlth", 0.4, -0.05, False, "2020-06-30"],
            ["bench", 1, "111111111", "111111111", "111111", "AAA", "BusEq", 0.7, 0.10, False, "2020-03-31"],
            ["bench", 1, "444444444", "444444444", "444444", "DDD", "Money", 0.3, 0.02, False, "2020-03-31"],
        ],
        columns=POSITION_RETURNS,
    )
    cal = pd.DataFrame(
        [[1, "2019-12-31", pd.Timestamp("2019-12-31"), pd.Timestamp("2020-03-31")],
         [2, "2020-03-31", pd.Timestamp("2020-03-31"), pd.Timestamp("2020-06-30")]],
        columns=QUARTERS,
    )
    ov = return_overrides_with_t(_overrides([["quarter_return", "111111111", "2019-12-31", "-0.25", "spin-off"]]), cal)
    after = apply_return_overrides(pos, ov)
    print(pd.concat([pos, after], keys=["before", "after"]).to_string())
    named = (pos["sec_id"] == "111111111") & (pos["t"] == 1)
    assert (after.loc[named, "r"] == -0.25).all()
    # Convention 4.9: the Unmapped row of the changed fund book takes its new priced, mapped return
    neutral = (pos["bucket"] == "Unmapped") & (pos["entity"] == "fund") & (pos["t"] == 1)
    assert after.loc[neutral, "r"].iloc[0] == (0.5 * -0.25 + 0.3 * 0.20) / 0.8
    rest = ~named & ~neutral
    pd.testing.assert_frame_equal(after[rest], pos[rest])
    assert after.columns.tolist() == POSITION_RETURNS
