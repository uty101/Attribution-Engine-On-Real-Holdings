"""Render README.md from docs/README_template.md (step 8.3; instructions/08, D.1).

    python scripts/build_readme.py

The template holds the prose. Every number in it is a placeholder filled from
outputs/tables/answers.csv, and every table is a placeholder filled from its CSV:

    {akre.linked_selection:pp}         the value of 1 answers.csv row (fund, figure), formatted
    {akre.mean_q_selection@lo:pct2}    its interval_lo (@hi for interval_hi)
    {akre.largest_cte_*:pp}            a figure name with 1 wildcard, matched to exactly 1 row
    {akre.largest_cte_*:ticker}        the part of that figure name the wildcard matched
    {table:carino_totals}              a Markdown table built from its CSVs (TABLES below)

Formats: pp (x 100, 1 decimal, "pp"), pct (x 100, 1 decimal, "%"), pct2 (x 100, 2 decimals, "%"),
num2 and t (2 decimals), num4 (4 decimals, for every correlation), abspct and abspp (as pct and pp,
of the absolute value, where the verb carries the sign) (instructions/09b, B). Offline; reads only the template and outputs/tables/.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs" / "README_template.md"
README = ROOT / "README.md"
TABLES_DIR = ROOT / "outputs" / "tables"

VALUE = re.compile(r"\{([a-z]+)\.([A-Za-z0-9_*]+)(@lo|@hi)?:([a-z0-9]+)\}")
TABLE = re.compile(r"\{table:([a-z0-9_]+)\}")
MINUS = "−"
FUND_NAMES = {"akre": "Akre", "jensen": "Jensen", "polen": "Polen", "ivv": "IVV", "iwf": "IWF"}


def _signed(s: str) -> str:
    """A typographic minus, and no negative zero."""
    if s.startswith("-"):
        return s[1:] if float(s) == 0 else MINUS + s[1:]
    return s


def fmt(x: float, kind: str) -> str:
    """instructions/08, D.1: pp, pct, pct2, num2 and t; instructions/09b, B: num4, abspct and abspp."""
    if kind == "pp":
        return _signed(f"{100 * x:.1f}") + " pp"
    if kind == "abspp":
        return f"{100 * abs(x):.1f} pp"
    if kind == "pct":
        return _signed(f"{100 * x:.1f}") + "%"
    if kind == "abspct":
        return f"{100 * abs(x):.1f}%"
    if kind == "pct2":
        return _signed(f"{100 * x:.2f}") + "%"
    if kind in ("num2", "t"):
        return _signed(f"{x:.2f}")
    if kind == "num4":
        return _signed(f"{x:.4f}")
    raise ValueError(f"unknown format {kind!r}")


def _lookup(ans: pd.DataFrame, fund: str, figure: str) -> tuple[pd.Series, str]:
    """The 1 answers.csv row for (fund, figure), and the text a `*` in `figure` matched."""
    rows = ans[ans["fund"] == fund]
    if "*" in figure:
        pat = re.compile(re.escape(figure).replace(r"\*", "(.+)") + "$")
        hits = [(r, m.group(1)) for _, r in rows.iterrows() if (m := pat.match(r["figure"]))]
    else:
        hits = [(r, "") for _, r in rows.iterrows() if r["figure"] == figure]
    if len(hits) != 1:
        raise KeyError(f"{fund}.{figure}: {len(hits)} rows in answers.csv")
    return hits[0]


def _md(header: list[str], rows: list[list[str]]) -> str:
    align = ["---", *["---:"] * (len(header) - 1)]
    return "\n".join("| " + " | ".join(r) + " |" for r in [header, align, *rows])


def table_carino_totals(t: dict[str, pd.DataFrame]) -> str:
    """Table 1: the Carino Total row of linked.csv per fund, and D from answers.csv, in pp."""
    lk, ans = t["linked"], t["answers"]
    rows = []
    for fund in dict.fromkeys(ans["fund"]):
        r = lk[(lk["fund"] == fund) & (lk["method"] == "carino") & (lk["bucket"] == "Total")].iloc[0]
        D = _lookup(ans, fund, "cum_excess_D")[0]["value"]
        rows.append([FUND_NAMES[fund], *[fmt(r[c], "pp") for c in ("allocation", "selection", "interaction", "total")],
                     fmt(D, "pp")])
    return _md(["Fund", "Allocation", "Selection", "Interaction", "Total", "D"], rows)


def table_factor_fit(t: dict[str, pd.DataFrame]) -> str:
    """Table 2: per fund, from factor_fit.csv: book and NAV alpha a month with HAC t, the book's
    market beta and R²."""
    ff = t["factor_fit"].set_index(["series_id", "coef"])
    rows = []
    for fund in dict.fromkeys(t["answers"]["fund"]):
        b, n = ff.loc[(f"{fund}_book", "alpha")], ff.loc[(f"{fund}_nav", "alpha")]
        rows.append([FUND_NAMES[fund], fmt(b["value"], "pct2"), fmt(b["t_hac"], "t"), fmt(n["value"], "pct2"),
                     fmt(n["t_hac"], "t"), fmt(ff.at[(f"{fund}_book", "mkt"), "value"], "num2"), fmt(b["r2"], "num2")])
    return _md(["Fund", "Alpha a month, book", "HAC t, book", "Alpha a month, NAV", "HAC t, NAV",
                "Market beta, book", "R², book"], rows)


def table_risk(t: dict[str, pd.DataFrame]) -> str:
    """Table 3: active share and ex-ante TE at 2026-06-30 from risk_quarterly.csv, the mean ex-ante
    TE and the realised TE from te_realised.csv."""
    rq, tr = t["risk_quarterly"], t["te_realised"].set_index("fund")
    rows = []
    for fund in dict.fromkeys(t["answers"]["fund"]):
        r = rq[(rq["fund"] == fund) & (rq["holdings_date"] == "2026-06-30")].iloc[0]
        rows.append([FUND_NAMES[fund], fmt(r["active_share"], "pct"), fmt(r["te_exante"], "pct2"),
                     fmt(tr.at[fund, "te_exante_mean"], "pct2"), fmt(tr.at[fund, "te_realised"], "pct2")])
    return _md(["Fund", "Active share, 2026-06-30", "Ex-ante TE, 2026-06-30", "Mean ex-ante TE",
                "Realised TE, 84 months"], rows)


def table_gate(t: dict[str, pd.DataFrame]) -> str:
    """Table 4: the rows of gate.csv, with the gap bootstrap interval from bootstrap.csv."""
    bt = t["bootstrap"]
    rows = []
    for _, g in t["gate"].iterrows():
        b = bt[(bt["fund"] == g["fund"]) & (bt["series"] == "gap")].iloc[0]
        rows.append([FUND_NAMES[g["fund"]], fmt(g["corr"], "num4"), "Yes" if bool(g["pass"]) else "No",
                     str(int(g["n_quarters"])), fmt(g["mean_gap"], "pct2"), fmt(g["std_gap"], "pct2"),
                     fmt(g["mean_abs_gap"], "pct2"), fmt(g["te_gap_ann"], "pct2"),
                     f"{fmt(b['p05'], 'pct2')} to {fmt(b['p95'], 'pct2')}"])
    return _md(["Fund", "Correlation", "Passes", "Quarters", "Mean gap", "Std of gap", "Mean abs gap",
                "TE of gap", "Mean gap, bootstrap interval"], rows)


def table_unpriced(t: dict[str, pd.DataFrame]) -> str:
    """The mean unpriced weight of each entity's book over its quarters in book_quarterly.csv."""
    bq = t["book_quarterly"]
    m = bq.groupby("entity", sort=False)["unpriced_weight"].mean()
    rows = [[FUND_NAMES[e], fmt(w, "pct2")] for e, w in m.items()]
    return _md(["Book", "Mean unpriced weight"], rows)


TABLES = {"carino_totals": table_carino_totals, "factor_fit": table_factor_fit, "risk": table_risk,
          "gate": table_gate, "unpriced": table_unpriced}
SOURCES = ["answers", "linked", "factor_fit", "risk_quarterly", "te_realised", "gate", "bootstrap", "book_quarterly"]


def render(template: str, tables_dir: Path = TABLES_DIR) -> str:
    t = {s: pd.read_csv(tables_dir / f"{s}.csv") for s in SOURCES}
    ans = t["answers"]

    def value(m: re.Match) -> str:
        fund, figure, side, kind = m.groups()
        row, matched = _lookup(ans, fund, figure)
        if kind == "ticker":
            return matched.removesuffix("_2026_06_30")
        col = {None: "value", "@lo": "interval_lo", "@hi": "interval_hi"}[side]
        return fmt(float(row[col]), kind)

    out = TABLE.sub(lambda m: TABLES[m.group(1)](t), template)
    out = VALUE.sub(value, out)
    left = re.findall(r"\{[^{}\n]*\}", out)
    if left:
        raise ValueError(f"unfilled placeholders: {left}")
    return out


def main() -> None:
    text = render(TEMPLATE.read_text(encoding="utf-8"))
    README.write_bytes(text.encode("utf-8"))
    print(f"wrote {README.relative_to(ROOT).as_posix()}: {len(text.encode('utf-8'))} bytes")


if __name__ == "__main__":
    sys.exit(main())
