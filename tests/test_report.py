"""Step 7.1: the PDF report (instructions/07, Sections C.1 and C.2), on synthetic results shaped
like a real fund's: 28 quarters, 14 buckets, 8 calendar years, 28 holdings dates and 3 charts at
the real charts' sizes. Nothing here reads outputs/ (rule 7)."""

import io
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from pypdf import PdfReader

from attrib.config import load_config
from attrib.report import build_report

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "config.toml")
BUCKETS = ["NoDur", "Durbl", "Manuf", "Enrgy", "Chems", "BusEq", "Telcm", "Utils", "Shops", "Hlth", "Money", "Other",
           "Unmapped", "Unpriced"]
FACTORS = ["mkt", "smb", "hml", "rmw", "cma", "umd"]


def _png(rng, size: tuple[float, float]) -> bytes:
    fig = Figure(figsize=size)
    ax = fig.subplots()
    ax.plot(rng.normal(size=28).cumsum())
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=CFG.report.dpi, metadata={"Software": None})
    return buf.getvalue()


def synthetic_results(with_nav: bool = True) -> dict:
    rng = np.random.default_rng(CFG.run.bootstrap_seed)
    T = 28
    hdates = [str(d.date()) for d in pd.date_range("2019-09-30", periods=T, freq="QE")]
    bq = pd.concat([
        pd.DataFrame({"entity": e, "t": range(1, T + 1), "book_return": rng.normal(0.03, 0.08, T),
                      "unmapped_weight": rng.uniform(0, 0.01, T), "unpriced_weight": rng.uniform(0, 0.01, T),
                      "delisted_weight": 0.0})
        for e in ("fund", "bench")
    ], ignore_index=True)
    eff = rng.normal(0, 0.01, (len(BUCKETS), 3))
    lk = pd.DataFrame(eff, columns=["allocation", "selection", "interaction"]).assign(bucket=BUCKETS)
    lk = pd.concat([lk, pd.DataFrame([["Total", *eff.sum(axis=0)]], columns=["bucket", "allocation", "selection",
                                                                            "interaction"])], ignore_index=True)
    lk["total"] = lk[["allocation", "selection", "interaction"]].sum(axis=1)
    linked = pd.concat([lk.assign(fund="fund", method=m) for m in ("carino", "menchero")], ignore_index=True)
    years = list(range(2019, 2027))
    fby = pd.DataFrame(rng.normal(0, 0.05, (len(years), 9)),
                       columns=["excess_return", *FACTORS, "alpha", "residual"]).assign(
        series_id="fund_book", year=years, n_months=[3, *[12] * 6, 9], r2_full=0.9)
    fit = pd.DataFrame({"series_id": "fund_book", "series_kind": "book", "coef": ["alpha", *FACTORS],
                        "value": rng.normal(0, 0.01, 7), "se_hac": 0.01, "t_hac": rng.normal(0, 2, 7), "r2": 0.9,
                        "resid_vol_ann": 0.05, "n_months": 83})
    rq = pd.DataFrame({"fund": "fund", "holdings_date": hdates, "active_share": rng.uniform(0.5, 1, T),
                       "te_exante": rng.uniform(0.03, 0.15, T), "n_names": rng.integers(100, 600, T),
                       "ridged": rng.uniform(size=T) > 0.5})
    boot = pd.DataFrame({"fund": "fund", "series": ["allocation", "selection", "interaction", "gap"],
                         "mean": rng.normal(0, 0.01, 4), "p05": -0.02, "p95": 0.02})
    gate = pd.DataFrame({"fund": ["fund"], "corr": [0.97], "pass": [True], "n_quarters": [28], "mean_gap": [0.001],
                         "std_gap": [0.02], "mean_abs_gap": [0.015], "te_gap_ann": [0.04]})
    cov = pd.DataFrame({"entity": "fund", "period_date": hdates})
    return {
        "linked": linked, "factor_by_year": fby, "factor_fit": fit, "risk_quarterly": rq,
        "te_realised": pd.DataFrame({"fund": ["fund"], "te_realised": [0.1], "te_exante_mean": [0.09],
                                     "n_months": [84]}),
        "gate": gate if with_nav else gate.iloc[0:0],
        "bootstrap": boot if with_nav else boot[boot["series"] != "gap"],
        "book_quarterly": bq, "coverage": cov, "fund_name": "Fund", "benchmark_name": "BENCH",
        "chart1": _png(rng, (8, 4.5)), "chart2": _png(rng, (8, 4.5)), "chart3": _png(rng, (8, 6)),
    }


def test_two_builds_byte_identical(tmp_path):
    res = synthetic_results()
    a = build_report("fund", res, tmp_path / "a.pdf").read_bytes()
    b = build_report("fund", res, tmp_path / "b.pdf").read_bytes()
    assert a == b


def test_page_count_at_most_4(tmp_path):
    """instructions/07, C.2: exactly 4 pages for a fund with a NAV series; a report with no NAV
    keeps the 4-page shape (D-28) and is never longer than `report.max_pages`."""
    for with_nav in (True, False):
        path = build_report("fund", synthetic_results(with_nav), tmp_path / f"r{with_nav}.pdf")
        n = len(PdfReader(path).pages)
        assert n <= CFG.report.max_pages
        assert n == 4
