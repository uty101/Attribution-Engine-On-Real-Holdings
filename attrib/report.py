"""The 4-page PDF report (kickoff Section 5.11; instructions/07, Sections C.1 and C.2).

`build_report` renders what it is given and filters nothing (D-26 B): every frame in `results` is
already cut to 1 fund. Numbers are in percent with 2 decimals unless a label says otherwise.
"""

from __future__ import annotations

import io
import math
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# instructions/07, C.1: A4 portrait, 2 cm margins, Helvetica 9 pt body, 8 pt tables, charts 17 cm wide
MARGIN = 2 * cm
CHART_WIDTH = 17 * cm
BODY_PT, TABLE_PT, TITLE_PT = 9, 8, 14

BODY = ParagraphStyle("body", fontName="Helvetica", fontSize=BODY_PT, leading=BODY_PT * 1.3, spaceAfter=4)
CAPTION = ParagraphStyle("caption", parent=BODY, fontName="Helvetica-Bold", spaceBefore=4)
TITLE = ParagraphStyle("title", parent=BODY, fontName="Helvetica-Bold", fontSize=TITLE_PT, leading=TITLE_PT * 1.3,
                       spaceAfter=8)

EFFECTS = ["allocation", "selection", "interaction"]
FACTOR_HEAD = {"mkt": "Mkt-RF", "smb": "SMB", "hml": "HML", "rmw": "RMW", "cma": "CMA", "umd": "UMD"}
NO_NAV = "No NAV series was supplied, so the reconstruction check is skipped."
LIMITS_HEAD = "What a 13F book cannot see."
# instructions/07, C.1: the 13F limits paragraph, verbatim
LIMITS = (
    "The 13F lists a manager's long US-listed equity positions at each quarter end, filed up to 45 days later. "
    "It omits cash, shorts, most non-US shares, bonds and anything bought and sold inside the quarter. This "
    "report holds each quarter-end book unchanged for the next 3 months, so trades made during the quarter show "
    "up only in the gap between the book and the fund's NAV, together with fees and cash. A 13F belongs to the "
    "manager, not to one fund, so where a manager runs several strategies the book blends them. Sectors are "
    "Fama-French 12 industries built from SIC codes, which put payment networks such as Visa and Mastercard in "
    "Other. Securities that could not be mapped to a ticker, or had no price, earn the book's own return so that "
    "they move nothing."
)
QUARTERS_PER_YEAR = 4  # annualising a compounded quarterly return: (1 + R)^(4 / T) - 1


def num(x) -> str:
    """A plain number with 2 decimals, `0.00` rather than `-0.00`; `n/a` for a blank or non-finite value."""
    if not _finite(x):
        return "n/a"
    s = f"{float(x):.2f}"
    return "0.00" if s == "-0.00" else s


def pct(x) -> str:
    """A decimal as percent with 2 decimals (`num` of 100 x)."""
    return num(100 * float(x)) if _finite(x) else "n/a"


def _finite(x) -> bool:
    try:
        return math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def _table(header: list[str], rows: list[list[str]], bold_last: bool = False) -> Table:
    t = Table([header, *rows], repeatRows=1, hAlign="LEFT")
    style = [
        ("FONT", (0, 0), (-1, -1), "Helvetica", TABLE_PT),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", TABLE_PT),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    if bold_last:
        style += [("FONT", (0, -1), (-1, -1), "Helvetica-Bold", TABLE_PT), ("LINEABOVE", (0, -1), (-1, -1), 0.4,
                                                                            colors.black)]
    t.setStyle(TableStyle(style))
    return t


def _chart(png: bytes) -> Image:
    """A PNG from memory at the chart width, keeping its aspect ratio."""
    w, h = ImageReader(io.BytesIO(png)).getSize()
    return Image(io.BytesIO(png), width=CHART_WIDTH, height=CHART_WIDTH * h / w)


def _annualised(r: pd.Series) -> tuple[float, float]:
    """(compounded return over the quarters of `r`, its annualised rate)."""
    R = float((1 + r.astype("float64")).prod() - 1)
    return R, (1 + R) ** (QUARTERS_PER_YEAR / len(r)) - 1


def _page_1(fund_id: str, res: dict) -> list:
    name, bench = res["fund_name"], res["benchmark_name"]
    cov = res["coverage"]
    dates = sorted(cov["period_date"].astype(str))
    ret_end = (pd.Timestamp(dates[-1]) + pd.offsets.QuarterEnd(1)).strftime("%Y-%m-%d")
    bq = res["book_quarterly"]
    rP = bq[bq["entity"] == fund_id].sort_values("t")
    rB = bq[bq["entity"] != fund_id].sort_values("t")
    RP, aP = _annualised(rP["book_return"])
    RB, aB = _annualised(rB["book_return"])
    T = len(rP)
    linked = res["linked"]
    linked = linked[linked["method"] == "carino"]  # D-27: Carino only in the report
    boot = res["bootstrap"].set_index("series")

    def interval(s: str) -> str:
        r = boot.loc[s]
        return f"{pct(r['mean'])}% (90% interval {pct(r['p05'])}% to {pct(r['p95'])}%)"

    rows = [[str(r["bucket"]), *[pct(r[c]) for c in [*EFFECTS, "total"]]] for _, r in linked.iterrows()]
    return [
        Paragraph(f"{name} vs {bench}: performance and risk attribution", TITLE),
        Paragraph(f"Window: holdings {dates[0]} to {dates[-1]}, returns {dates[0]} to {ret_end}.", BODY),
        Paragraph(
            f"Annualised book return over the {T} quarters: the fund {pct(aP)}%, {bench} {pct(aB)}%. "
            f"Cumulative excess return D: {pct(RP - RB)} percentage points.", BODY),
        Paragraph(
            f"Data: mean unmapped weight of the fund book {pct(rP['unmapped_weight'].mean())}% and mean unpriced "
            f"weight {pct(rP['unpriced_weight'].mean())}% over the {T} quarters.", BODY),
        Paragraph(f"Table 1. Brinson-Fachler effects over the {T} quarters, linked with Carino, in percentage "
                  "points.", CAPTION),
        _table(["Bucket", "Allocation", "Selection", "Interaction", "Total"], rows, bold_last=True),
        Spacer(1, 4),
        Paragraph(f"Mean quarterly allocation {interval('allocation')}; mean quarterly selection "
                  f"{interval('selection')}. Stationary bootstrap.", BODY),
        _chart(res["chart1"]),
    ]


def _page_2(fund_id: str, res: dict) -> list:
    fy = res["factor_by_year"]
    fy = fy[fy["series_id"] == f"{fund_id}_book"]  # D-23: the book series
    factors = list(FACTOR_HEAD)
    rows = [[str(int(r["year"])), str(int(r["n_months"])), pct(r["excess_return"]), *[pct(r[f]) for f in factors],
             pct(r["alpha"]), pct(r["residual"])] for _, r in fy.iterrows()]
    fit = res["factor_fit"]
    fit = fit[fit["series_id"] == f"{fund_id}_book"].set_index("coef")
    a = fit.loc["alpha"]
    return [
        Paragraph("Table 2. Factor attribution of the fund book's monthly excess return by calendar year, with "
                  "full-sample betas, in percent.", CAPTION),
        _table(["Year", "Months", "Excess", *FACTOR_HEAD.values(), "Alpha", "Residual"], rows),
        Spacer(1, 4),
        Paragraph(f"Full sample of {int(a['n_months'])} months: alpha {pct(a['value'])}% a month, HAC t "
                  f"{num(a['t_hac'])}, R² {num(a['r2'])}.", BODY),
        _chart(res["chart2"]),
    ]


def _page_3(fund_id: str, res: dict) -> list:
    rq = res["risk_quarterly"].copy()
    rq["holdings_date"] = rq["holdings_date"].astype(str)
    last = max(rq["holdings_date"])
    pick = rq[rq["holdings_date"].str.endswith("-12-31") | (rq["holdings_date"] == last)]
    rows = [[r["holdings_date"], pct(r["active_share"]), pct(r["te_exante"]), str(int(r["n_names"])),
             "Yes" if str(r["ridged"]) == "True" else "No"] for _, r in pick.iterrows()]
    te = res["te_realised"].iloc[0]
    return [
        Paragraph("Table 3. Active share and ex-ante tracking error at each year end and at the last holdings "
                  "date, in percent.", CAPTION),
        _table(["Date", "Active share", "Ex-ante TE", "Names", "Ridged"], rows),
        Spacer(1, 4),
        Paragraph(f"Realised tracking error over {int(te['n_months'])} months: {pct(te['te_realised'])}%. Mean "
                  f"ex-ante tracking error over the {len(rq)} holdings dates: {pct(te['te_exante_mean'])}%.", BODY),
        _chart(res["chart3"]),
    ]


def _page_4(res: dict) -> list:
    gate = res["gate"]
    out: list = []
    if gate is None or gate.empty:
        out.append(Paragraph(NO_NAV, BODY))
    else:
        g = gate.iloc[0]
        boot = res["bootstrap"].set_index("series").loc["gap"]
        out += [
            Paragraph("Table 4. Quarterly gap between the 13F book return and the fund's NAV return, in percent.",
                      CAPTION),
            _table(["Correlation", "Quarters", "Mean gap", "Std of gap", "TE of gap", "90% interval of mean gap"],
                   [[num(g["corr"]), str(int(g["n_quarters"])), pct(g["mean_gap"]), pct(g["std_gap"]),
                     pct(g["te_gap_ann"]), f"{pct(boot['p05'])} to {pct(boot['p95'])}"]]),
            Spacer(1, 8),
        ]
    out.append(Paragraph(f"<b>{LIMITS_HEAD}</b> {LIMITS}", BODY))
    return out


def build_report(fund_id: str, results: dict, out_path: Path) -> Path:
    """Write the report for `fund_id` to `out_path` (instructions/07, C.1 and C.2): 4 A4 pages, each
    started on a fresh page, built with `invariant=1` so 2 builds of the same `results` are
    byte-identical. `results` holds the output frames cut to this fund (`book_quarterly` also
    carries the benchmark's rows), `fund_name`, `benchmark_name` and the chart PNGs `chart1` to
    `chart3`; `gate` may be empty when no NAV series was supplied (D-28)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN, bottomMargin=MARGIN,
        invariant=1, title=f"{results['fund_name']} vs {results['benchmark_name']}",
    )
    story = [*_page_1(fund_id, results), PageBreak(), *_page_2(fund_id, results), PageBreak(),
             *_page_3(fund_id, results), PageBreak(), *_page_4(results)]
    doc.build(story)
    return out_path
