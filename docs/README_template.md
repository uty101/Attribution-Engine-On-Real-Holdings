# Performance and risk attribution on real 13F holdings

## What this is

This repo takes the quarterly 13F holdings of 3 concentrated quality-growth managers (Akre, Jensen and Polen) and the N-PORT holdings of their ETF benchmarks (IVV for Akre and Jensen, IWF for Polen), and works out where each manager's return against its benchmark came from. Each quarter's book is split into the Fama-French 12 industries (FF12) and attributed with Brinson-Fachler, and the 28 quarters are linked with Carino. Monthly book returns go through a Fama-French 5-factor plus momentum regression with HAC standard errors, and active risk comes from a Ledoit-Wolf covariance of daily returns.

Everything is built from free public data: SEC EDGAR filings, the OpenFIGI mapping API, yfinance prices and Ken French's data library. Each 13F book is checked against the fund's own NAV before it is attributed, and each manager gets a 4-page PDF report: [Akre](outputs/reports/akre.pdf), [Jensen](outputs/reports/jensen.pdf) and [Polen](outputs/reports/polen.pdf). Every table behind the figures is a CSV in [outputs/tables](outputs/tables). The method is written out in full in [docs/METHODS.md](docs/METHODS.md).

## Answers

**Allocation, selection and interaction.** Every fund trailed its benchmark over the 28 quarters to September 2026. Akre's book returned {akre.ann_return_fund:pct} a year against {akre.ann_return_bench:pct} for IVV, a cumulative excess return D of {akre.cum_excess_D:pp}. Jensen's returned {jensen.ann_return_fund:pct} against the same {jensen.ann_return_bench:pct} (D of {jensen.cum_excess_D:pp}), and Polen's {polen.ann_return_fund:pct} against {polen.ann_return_bench:pct} for IWF (D of {polen.cum_excess_D:pp}). Selection, not allocation, carried most of it for Akre and Polen. Linked with Carino, Akre's selection is {akre.linked_selection:pp} against allocation of {akre.linked_allocation:pp}, and Polen's is {polen.linked_selection:pp} against {polen.linked_allocation:pp}. Jensen's loss is also selection, {jensen.linked_selection:pp}, with allocation of {jensen.linked_allocation:pp}. The mean quarterly selection effect is {akre.mean_q_selection:pct2} for Akre and {polen.mean_q_selection:pct2} for Polen, and both bootstrap intervals are entirely negative ({akre.mean_q_selection@lo:pct2} to {akre.mean_q_selection@hi:pct2}, and {polen.mean_q_selection@lo:pct2} to {polen.mean_q_selection@hi:pct2}). Jensen's mean quarterly selection of {jensen.mean_q_selection:pct2} has an interval of {jensen.mean_q_selection@lo:pct2} to {jensen.mean_q_selection@hi:pct2}, which reaches into positive values, so this sample cannot distinguish Jensen's selection from no effect. Only Akre's allocation interval is entirely negative ({akre.mean_q_allocation@lo:pct2} to {akre.mean_q_allocation@hi:pct2}).

**Factors.** Jensen's alpha is {jensen.alpha_month_book:pct2} a month on the book, with a HAC t of {jensen.alpha_t_book:t}, and {jensen.alpha_month_nav:pct2} on the NAV, with a t of {jensen.alpha_t_nav:t}. Polen's is {polen.alpha_month_book:pct2} on the book (t of {polen.alpha_t_book:t}) and {polen.alpha_month_nav:pct2} on the NAV (t of {polen.alpha_t_nav:t}). Akre's alpha of {akre.alpha_month_book:pct2} a month on the book (t of {akre.alpha_t_book:t}, interval {akre.alpha_month_book@lo:pct2} to {akre.alpha_month_book@hi:pct2}) cannot be told apart from no alpha. Its R² of {akre.r2_book:num2}, against {jensen.r2_book:num2} for Jensen and {polen.r2_book:num2} for Polen, says most of Akre's active risk is stock-specific: its residual volatility is {akre.resid_vol_ann_book:pct} a year. Market betas on the book are {akre.beta_mkt_book:num2} for Akre, {jensen.beta_mkt_book:num2} for Jensen and {polen.beta_mkt_book:num2} for Polen. Akre's exposures drifted the most: from 2025 its value loading climbed and its investment loading fell away (Akre's rolling beta chart below).

**Active risk.** At 2026-06-30 Akre's active share against IVV was {akre.active_share_2026_06_30:pct} and its ex-ante tracking error {akre.te_exante_2026_06_30:pct}. Jensen's were {jensen.active_share_2026_06_30:pct} and {jensen.te_exante_2026_06_30:pct}, and Polen's against IWF {polen.active_share_2026_06_30:pct} and {polen.te_exante_2026_06_30:pct}. A few positions carry most of that risk for Akre and Polen: the top positions in each tracking error chart below explain {akre.top15_cte_share_2026_06_30:pct} of Akre's ex-ante tracking error and {polen.top15_cte_share_2026_06_30:pct} of Polen's, against {jensen.top15_cte_share_2026_06_30:pct} of Jensen's. Akre's largest single contribution is a position it holds, {akre.largest_cte_*:ticker} at {akre.largest_cte_*:pp}. Polen's and Jensen's are names they do not own: {polen.largest_cte_*:ticker} at {polen.largest_cte_*:pp} and {jensen.largest_cte_*:ticker} at {jensen.largest_cte_*:pp}. Realised tracking error over 84 months is {akre.te_realised_84m:pct} for Akre, above its ex-ante mean of {akre.te_exante_mean:pct}. The reason is September 2026, the largest active month in the sample: FICO, {akre.fico_weight_2026_06_30:pct} of Akre's book at 2026-06-30, fell {akre.fico_return_2026_09:abspct} in the month after the FHFA's September 2026 order letting every GSE lender use VantageScore, and the book trailed IVV by {akre.active_return_2026_09:abspp} that month. Jensen's and Polen's realised figures, {jensen.te_realised_84m:pct} and {polen.te_realised_84m:pct}, sit close to their ex-ante means of {jensen.te_exante_mean:pct} and {polen.te_exante_mean:pct}.

**The book against the NAV.** The quarter-start book tracks the fund's NAV closely for all of them: the correlation of quarterly book and NAV returns is {akre.gate_corr:num4} for Akre, {jensen.gate_corr:num4} for Jensen and {polen.gate_corr:num4} for Polen. Polen's filing mixes strategies, ETFs included, and its book still tracks the fund's NAV at {polen.gate_corr:num4}. Every mean gap is positive: the book beat the NAV by {akre.mean_q_gap:pct2} a quarter for Akre, {jensen.mean_q_gap:pct2} for Jensen and {polen.mean_q_gap:pct2} for Polen. That is the sign fees and cash predict, since the NAV pays fees and holds cash that the book does not. Jensen's and Polen's bootstrap intervals are entirely positive; Akre's runs from {akre.mean_q_gap@lo:pct2} to {akre.mean_q_gap@hi:pct2}. The gap's annualised tracking error is {jensen.te_gap_ann:pct2} for Jensen, {polen.te_gap_ann:pct2} for Polen and {akre.te_gap_ann:pct2} for Akre.

## Results

### Brinson-Fachler, linked with Carino

Table 1 gives the linked totals over the 28 quarters in percentage points. Allocation, selection and interaction sum to the total, which equals the cumulative excess return D.

{table:carino_totals}

Akre's selection loss sits almost entirely in BusEq. Its BusEq names (Roper, Danaher, CCC and Verisk) did far worse than IVV's BusEq, which is mega-cap technology. Its large positive interaction sits in BusEq too: Akre held far less BusEq than IVV, and an underweight in a bucket where the fund's own picks lost gives a positive interaction ({akre.interaction_BusEq:pp}, against {akre.selection_BusEq:pp} of selection). Its weight in FF12 Other, {akre.other_weight_min:pct} to {akre.other_weight_max:pct} of the book, is Mastercard, Visa, Moody's, FICO and CoStar. Every bucket of every fund is in `outputs/tables/linked.csv`, with the Menchero linking beside Carino.

Akre's selection slides from 2024 and allocation follows it down, with selection ending at {akre.linked_selection:pp}.

![Akre: cumulative allocation and selection](outputs/figures/akre_alloc_vs_sel.png)

Jensen's selection peaked in early 2023 and then fell to {jensen.linked_selection:pp}, while its allocation stayed flat.

![Jensen: cumulative allocation and selection](outputs/figures/jensen_alloc_vs_sel.png)

Polen's shortfall opened in 2022 and is almost all selection, which ends at {polen.linked_selection:pp}.

![Polen: cumulative allocation and selection](outputs/figures/polen_alloc_vs_sel.png)

### Factors

Table 2 gives the full-sample fit of each fund's monthly excess return on the 5 Fama-French factors and momentum, on the book and on the NAV. Jensen's and Polen's alphas lie more than 2 HAC standard errors below 0 on both series; Akre's do not.

{table:factor_fit}

Akre's rolling betas show the drift: its value (HML) loading climbs through 2025 while its investment (CMA) loading falls away.

![Akre: rolling factor betas](outputs/figures/akre_rolling_betas.png)

The holdings-based exposures, built from each stock's own 36-month betas, follow the returns-based line, which is what you would expect, since both use the same 36 months of returns (see Data and method limits).

![Akre: holdings-based against returns-based exposures](outputs/figures/akre_exposures_hb_vs_rb.png)

### Active risk

Table 3 gives active share and ex-ante tracking error at the last holdings date, the mean ex-ante tracking error over the 28 holdings dates, and the realised tracking error over 84 months.

{table:risk}

At 2026-06-30 Akre's largest contribution to tracking error is {akre.largest_cte_*:ticker} at {akre.largest_cte_*:pp}, and the positions shown explain {akre.top15_cte_share_2026_06_30:pct} of its ex-ante tracking error.

![Akre: top contributions to ex-ante tracking error](outputs/figures/akre_cte_top15.png)

Jensen's risk is spread out: the positions shown explain {jensen.top15_cte_share_2026_06_30:pct} of it, and the largest is an underweight in {jensen.largest_cte_*:ticker}.

![Jensen: top contributions to ex-ante tracking error](outputs/figures/jensen_cte_top15.png)

Polen's largest contributions are names it does not own, led by {polen.largest_cte_*:ticker} at {polen.largest_cte_*:pp}.

![Polen: top contributions to ex-ante tracking error](outputs/figures/polen_cte_top15.png)

### The book against the NAV

Table 4 gives the gate for each fund: the correlation of quarterly book and NAV returns, the number of quarters with a NAV return, the gap statistics and the bootstrap interval of the mean gap. A fund passes at a correlation of 0.90 or more.

{table:gate}

## Use it on your own holdings

`attribute()` takes 2 holdings files, the fund's and its benchmark's, and writes the same 4-page report. Each file has the columns `period_date, cusip, name, value_usd, shares`, with `entity`, `isin` and `sec_id` optional, and a row for every calendar quarter end from `start` to `end`. The 2 files in `examples/` are Akre's and IVV's books from 2025-06-30 to 2026-06-30:

```python
from attrib import attribute

pdf = attribute(
    "examples/akre_holdings.csv",
    "examples/ivv_holdings.csv",
    start="2025-06-30",
    end="2026-06-30",
)
print(pdf)  # outputs/reports/akre_holdings.pdf
```

It reads local data only. That window gives 15 monthly returns, fewer than the 24 the factor fit needs, so page 2 of that report says the fit is skipped. No NAV series is supplied, so page 4 skips the reconstruction check.

A file that holds securities not yet in `data/` raises an error listing them. Map them through OpenFIGI and SEC and pull their prices into `data/extra/` with:

```bash
python scripts/pull_data.py --holdings my_fund.csv --benchmark my_benchmark.csv
```

This needs `SEC_USER_AGENT` set in the environment. Tickers already known to have no yfinance prices (`data/raw/prices/missing.csv`) are skipped unless you add `--retry-missing`.

To rebuild every table, figure and report in this repo from `data/raw/` and `data/manual/`:

```bash
python scripts/run_all.py
```

## Data and method limits

**What a 13F book cannot see.** The 13F lists a manager's long US-listed equity positions at each quarter end, filed up to 45 days later. It omits cash, shorts, most non-US shares, bonds and anything bought and sold inside the quarter. This report holds each quarter-end book unchanged for the next 3 months, so trades made during the quarter show up only in the gap between the book and the fund's NAV, together with fees and cash. A 13F belongs to the manager, not to one fund, so where a manager runs several strategies the book blends them. Sectors are Fama-French 12 industries built from SIC codes, which put payment networks such as Visa and Mastercard in Other. Securities that could not be mapped to a ticker, or had no price, earn the book's own return so that they move nothing.

- **Unpriced weight.** A security with a ticker but no price at the start of a quarter goes to the Unpriced bucket. Its mean weight over the 28 quarters is small in every book:

{table:unpriced}

- **Akre's NAV gap.** Akre's monthly NAV returns come from the fund's N-PORT filings (item B.5) up to July 2025 and from the AKRE ETF's prices from November 2025. The months 2025-08 to 2025-10, when the fund converted to an ETF, have no public return. Their quarters are left out of Akre's gate correlation and gap statistics, so Table 4 counts fewer quarters for Akre.
- **The start date.** The window starts with the 2019-09-30 books because iShares filed its first public N-PORT for that quarter. There are no benchmark holdings on EDGAR before it.
- **FF12, not GICS.** Sectors are the Fama-French 12 industries mapped from SIC codes. They are public and reproducible, but they split companies differently from commercial sector schemes: payment networks, ratings agencies and data providers land in Other.
- **Holdings-based and returns-based exposures share a window.** The stock betas behind the holdings-based exposures and the rolling fund betas both use 36 months of returns ending at the same date, so their agreement is partly built in.
- **Determinism across platforms.** 2 runs on 1 machine give byte-identical CSVs, PNGs and PDFs. Across operating systems the numeric outputs agree to 1e-10 relative, and PNGs and PDFs differ at the byte level through font rendering (`docs/CONVENTIONS_RESOLVED.md`, item 25).
- **The project 1 link was dropped.** The original plan took holdings-based exposures from project 1's characteristic scores. Project 1 produced no characteristic scores, so each stock's exposure comes from its own 36-month factor betas instead.

## Reproduce

Python 3.12 and [uv](https://docs.astral.sh/uv/). The lock file `requirements-lock.txt` pins every dependency, including project 3's covariance and bootstrap code at a fixed commit.

```bash
uv venv --python 3.12
uv pip install -r requirements-lock.txt
uv pip install -e . --no-deps
python scripts/run_all.py
pytest -p socket --disable-socket
```

`run_all.py` is offline and reads only `data/raw/` and `data/manual/`, which are committed. `scripts/pull_data.py` is the only code that touches the network.
