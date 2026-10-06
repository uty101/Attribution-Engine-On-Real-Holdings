"""Step 8.2 (instructions/08, Section C): every row of answers.csv traces to its source table.

This reads the committed outputs/tables/, which instruction 08 requires of this test; that is the
one exception to rule 7 here, and it is listed in review/section_8.md.

Step 9.0 (instructions/09, Section B) adds 7 Akre-only rows. FICO's weight comes from
POSITION_RETURNS, which run_all.py rebuilds under data/processed/, so the test recomputes it from
data/raw/ through the Section 1 and 3 code (rule 7); FICO's return comes from adjclose.parquet."""

from pathlib import Path

import numpy as np
import pandas as pd
from real_data import real_risk_inputs

from attrib.returns import load_prices, monthly_returns

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
TOL = 1e-15  # instructions/08, C
QUARTERS_PER_YEAR = 4
AKRE_ONLY = 7  # instructions/09, B
NOT_IN_TABLES = ("position_returns", "adjclose")  # rebuilt or read from data/, not outputs/tables/

# figure -> source column, for the rows whose value is 1 cell of the source table
CELL = {
    "linked_allocation": "allocation", "linked_selection": "selection", "linked_interaction": "interaction",
    "mean_q_allocation": "mean", "mean_q_selection": "mean", "mean_q_gap": "mean",
    "alpha_month_book": "value", "alpha_month_nav": "value", "alpha_t_book": "t_hac", "alpha_t_nav": "t_hac",
    "beta_mkt_book": "value", "r2_book": "r2", "resid_vol_ann_book": "resid_vol_ann",
    "active_share_2026_06_30": "active_share", "te_exante_2026_06_30": "te_exante",
    "te_exante_mean": "te_exante_mean", "te_realised_84m": "te_realised",
    "gate_corr": "corr", "gate_n_quarters": "n_quarters", "te_gap_ann": "te_gap_ann",
    "selection_BusEq": "selection", "interaction_BusEq": "interaction",
}


def _keys(source_row: str) -> dict[str, str]:
    return dict(kv.split("=", 1) for kv in source_row.split(","))


def _cell_row(table: pd.DataFrame, keys: dict[str, str]) -> pd.Series:
    m = np.ones(len(table), dtype=bool)
    for k, v in keys.items():
        m &= table[k].astype(str) == v
    assert m.sum() == 1, keys
    return table[m].iloc[0]


def _book(bq: pd.DataFrame, entity: str) -> pd.Series:
    return bq[bq["entity"] == entity].sort_values("t")["book_return"]


def test_answers_trace_to_source():
    ans = pd.read_csv(TABLES / "answers.csv")
    tables = {s: pd.read_csv(TABLES / f"{s}.csv") for s in ans["source_table"].unique() if s not in NOT_IN_TABLES}
    bq = pd.read_csv(TABLES / "book_quarterly.csv")
    seen = 0
    for _, r in ans.iterrows():
        keys, src, fig = _keys(r["source_row"]), tables.get(r["source_table"]), r["figure"]
        lo, hi = r["interval_lo"], r["interval_hi"]
        if fig in CELL:
            row = _cell_row(src, keys)
            assert abs(r["value"] - row[CELL[fig]]) <= TOL, fig
            if r["source_table"] == "bootstrap":
                assert abs(lo - row["p05"]) <= TOL and abs(hi - row["p95"]) <= TOL, fig
            elif fig.startswith("alpha_month_"):  # alpha +/- 1.645 x HAC se (instructions/08, C)
                assert abs(lo - (row["value"] - 1.645 * row["se_hac"])) <= TOL, fig
                assert abs(hi - (row["value"] + 1.645 * row["se_hac"])) <= TOL, fig
            else:
                assert np.isnan(lo) and np.isnan(hi), fig
        elif fig in ("ann_return_fund", "ann_return_bench"):
            r_ = _book(bq, keys["entity"])
            assert len(r_) == 28
            want = (1 + r_).prod() ** (QUARTERS_PER_YEAR / len(r_)) - 1
            assert abs(r["value"] - want) <= TOL, fig
        elif fig == "cum_excess_D":
            fund, bench = keys["entity"].split("|")
            want = (1 + _book(bq, fund)).prod() - (1 + _book(bq, bench)).prod()
            assert abs(r["value"] - want) <= TOL, fig
            # the same D is the Carino Total in linked.csv (kickoff 5.6), to 1e-10
            lk = pd.read_csv(TABLES / "linked.csv")
            tot = lk[(lk["fund"] == fund) & (lk["method"] == "carino") & (lk["bucket"] == "Total")]["total"].iloc[0]
            assert abs(r["value"] - tot) <= 1e-10
        elif fig == "top15_cte_share_2026_06_30":
            d = src[(src["fund"] == keys["fund"]) & (src["holdings_date"] == keys["holdings_date"])]
            top = d.reindex(d["cte"].abs().sort_values(ascending=False, kind="mergesort").index).head(int(keys["top"]))
            rq = pd.read_csv(TABLES / "risk_quarterly.csv")
            te = _cell_row(rq, {"fund": keys["fund"], "holdings_date": keys["holdings_date"]})["te_exante"]
            assert abs(r["value"] - top["cte"].sum() / te) <= TOL, fig
        elif fig.startswith("largest_cte_"):
            d = src[(src["fund"] == keys["fund"]) & (src["holdings_date"] == keys["holdings_date"])]
            big = d.loc[d["cte"].idxmax()]
            assert fig == f"largest_cte_{big['ticker']}_2026_06_30" and keys["ticker"] == big["ticker"]
            assert abs(r["value"] - big["cte"]) <= TOL, fig
        elif fig in ("other_weight_min", "other_weight_max"):
            w = src[(src["entity"] == keys["entity"]) & (src["bucket"] == keys["bucket"])]["weight"]
            assert len(w) == 28 and keys["t"] == "1..28"
            want = w.min() if fig.endswith("_min") else w.max()
            assert np.isnan(lo) and np.isnan(hi) and abs(r["value"] - want) <= TOL, fig
        elif fig == "fico_weight_2026_06_30":
            pos = real_risk_inputs(keys["entity"], "2026-06-30")["posP"]
            assert int(pos["t"].iloc[0]) == int(keys["t"])
            want = pos.loc[pos["ticker"] == keys["ticker"], "weight"].sum()
            assert want > 0 and abs(r["value"] - want) <= TOL, fig
        elif fig == "fico_return_2026_09":
            mret = monthly_returns(load_prices(ROOT / "data")[[keys["ticker"]]])
            want = mret.at[pd.Period(keys["month"], "M"), keys["ticker"]]
            assert abs(r["value"] - want) <= TOL, fig
        elif fig == "active_return_2026_09":
            fund, bench = keys["entity"].split("|")
            m = src[src["month"] == keys["month"]].set_index("entity")["ret"]
            assert abs(r["value"] - (m[fund] - m[bench])) <= TOL, fig
        else:
            raise AssertionError(f"unknown figure {fig}")
        seen += 1
    funds = list(dict.fromkeys(ans["fund"]))
    assert funds == ["akre", "jensen", "polen"]
    assert seen == len(ans) == 25 * len(funds) + AKRE_ONLY
    assert (ans["fund"].iloc[-AKRE_ONLY:] == "akre").all()
