# Open decisions

Each item is something the kickoff leaves unspecified. None is decided; the reviewer picks an option in a later instruction file. Numbers match the OPEN-NN markers in `PLAN.md`.

## Repo-wide

**OPEN-01. What produces each section's output files before `scripts/run_all.py` (8.1) exists.** Steps 1.6, 2.5, 3.3, 3.4, 4.3, 5.1, 5.2, 6.2 and 7.4 write files but name no script.
- A: one script per section, `scripts/section_N.py`, absorbed into `scripts/run_all.py` in 8.1.
- B: `scripts/run_all.py` is created in Section 1 with a `--section N` flag that grows each section; 8.1 adds only the run-twice clean check.

**OPEN-02. Directory of output tables whose path is not stated** (`gate.csv`, `brinson_quarterly.csv`, `linked.csv`, `factor_fit.csv`, `factor_by_year.csv`, `rolling_betas.csv`, `holdings_exposures.csv`, `risk_quarterly.csv`, `cte_positions.csv`, `cte_sectors.csv`, `bootstrap.csv`).
- A: `outputs/tables/<name>`, alongside `reconstruction.csv` and `coverage.csv`.
- B: `outputs/tables/<name>` for tables named "Table N" and `outputs/tables/detail/<name>` for the rest.

**OPEN-03. Build backend and package discovery in `pyproject.toml`.** None is specified; `pip install -e . --no-deps` (rule 12, from Section 1) needs one.
- A: setuptools, `[build-system] requires = ["setuptools>=61"]`, `[tool.setuptools] packages = ["attrib"]`.
- B: hatchling, `[tool.hatch.build.targets.wheel] packages = ["attrib"]` and `[tool.hatch.metadata] allow-direct-references = true` (needed for the `pc` git dependency).

**OPEN-04. Python version the lock is resolved for.** `uv pip compile` resolves for the interpreter it finds; session 0 got CPython 3.14.4 on Windows x86_64. `requires-python` is `>=3.11`.
- A: keep the 3.14 resolution and use Python 3.14 for every venv and fresh-clone check.
- B: regenerate with `uv pip compile pyproject.toml --extra dev --python-version 3.11` and use Python 3.11.

**OPEN-05. Project version.** `[project]` needs `version` or the lock cannot be built. Session 0 set `version = "0.0.0"` so the lock could be built; it has no effect on results.
- A: keep `0.0.0`.
- B: `0.1.0`.

## Section 1

**OPEN-30. Which `[sample]` dates `test_dates_parse_and_are_quarter_ends` checks for quarter end (1.1).** `price_start` (2015-12-01) and `price_end_exclusive` (2026-10-01) are not quarter ends.
- A: all `[sample]` dates must parse; quarter-end check on `first_holdings_date`, `last_holdings_date` and `last_return_date` only.
- B: as A, plus the day before `price_end_exclusive` must equal `last_return_date`.

**OPEN-06. How `EdgarClient` gets the retry waits (1.2).** Its fixed signature has no parameter for `edgar.backoff_s`, and rule 6 bans hard-coding [2, 4, 8].
- A: add a keyword argument `backoff: Sequence[float]` to `__init__` (amends the Section 6 signature).
- B: waits computed as 2**k for k = 1..retries, a literal citing kickoff Section 5.1, with a test that they equal `edgar.backoff_s`.

**OPEN-07. Period of the committed IVV `primary_doc.xml` fixture (1.4).**
- A: 2023-06-30, matching the Akre dollars fixture.
- B: 2026-06-30, the last holdings date.

**OPEN-08. Meaning of `coverage.csv` `amendments_used` (1.6).**
- A: integer count of 13F-HR/A filings applied to the book; N-PORT rows count superseded NPORT-P filings for the period.
- B: semicolon-joined accession numbers of the 13F-HR/A filings applied; blank for N-PORT rows.

**OPEN-09. Base of `coverage.csv` `total_value_usd` (1.6).**
- A: all rows of the information table before filtering, so `dropped_value_usd / total_value_usd` is the dropped share.
- B: kept equity rows only, the weight denominator of Convention 4.5.

## Section 2

**OPEN-10. Columns of `data/raw/openfigi/mapping.csv` (2.1).**
- A: cusip, status, figi, ticker, name, exch_code, market_sector, security_type (first Equity result only).
- B: cusip, status, result_rank, figi, ticker, name, exch_code, market_sector, security_type (every result returned, ranked).

**OPEN-11. How the 2.2 FF12 tests read `Siccodes12.txt` before 2.3 pulls it.**
- A: run `--stage french` at the start of 2.2, committed in step 2.2, with 2.3 adding only the factor files.
- B: commit a copy of `Siccodes12.txt` to `tests/fixtures/` in 2.2; 2.3 pulls `data/raw/french/Siccodes12.txt` as written.

**OPEN-12. Vocabulary of SECURITY_MAP `map_status` (2.2).**
- A: mapped, no_match, no_cik, no_sic.
- B: ok, no_match (missing CIK and SIC shown only by blank `cik` and `sic`).

**OPEN-13. Names and modules of loaders not in Section 6 (2.3, 2.4):** French factors, prices, daily and monthly stock returns.
- A: `attrib/returns.py`: `load_prices(data_dir)`, `daily_returns(prices)`, `monthly_returns(prices)`; `attrib/factors.py`: `load_french(data_dir)`.
- B: a new module `attrib/data.py` holding all 4 under the same names.

**OPEN-14. Numbering of `t` in QUARTERS (2.4).**
- A: 1 to 30.
- B: 0 to 29.

**OPEN-15. Columns of `unmapped_top.csv`, `unpriced_top.csv` and `large_moves.csv` (2.5).**
- A: top files: cusip, ticker, name, max_weight, max_weight_entity, max_weight_period, periods_held (semicolon-joined `entity:period`); large_moves: entity, t, ticker, date, return, weight.
- B: top files in long form, one row per (cusip, entity, period_date) with ticker, name, weight, for the 20 CUSIPs; large_moves as in A.

## Section 3

**OPEN-16. Where `quarter_return` overrides enter (3.1)**, given `book_quarter` takes no overrides argument. Applies only if instruction 03 does not say.
- A: a helper in `attrib/returns.py` that replaces `r` in POSITION_RETURNS rows after `book_quarter`, before `bucket_table`.
- B: an extra `override_return` column in SECURITY_MAP read by `book_quarter`.

**OPEN-17. Where per-entity book outputs are stored (3.2)** (POSITION_RETURNS, BUCKETS, monthly book returns).
- A: `data/processed/position_returns.csv`, `data/processed/buckets.csv`, `data/processed/book_monthly.csv` (gitignored).
- B: the same 3 files under `outputs/tables/` (committed).

**OPEN-18. Where the benchmark gap is computed in 3.3**, before 3.4 builds `attrib/reconstruction.py`.
- A: 3.3 builds `reconstruction_table` and runs it for ivv and iwf; 3.4 adds `gate`, the bootstrap and the fund rows.
- B: 3.3 computes the gaps in the section script; 3.4 replaces that with `reconstruction_table`.

**OPEN-19. Where the per-fund gap statistics of kickoff 5.4 go (3.4):** standard deviation, mean |gap|, annualised tracking error of the gap.
- A: widen `gate.csv` to fund, corr, pass, mean_gap, std_gap, mean_abs_gap, te_gap_ann.
- B: new `outputs/tables/gap_stats.csv` (fund, mean_gap, std_gap, mean_abs_gap, te_gap_ann, corr); `gate.csv` unchanged.

**OPEN-20. Module holding the bootstrap helper (5.9, first used in 3.4).**
- A: new module `attrib/bootstrap.py` with `bootstrap_mean(x, mean_block, reps, seed, lo, hi) -> tuple[float, float, float]`.
- B: the same function in `attrib/reconstruction.py`, imported by Section 4.

## Section 4

**OPEN-21. Layout of `effects` passed to `carino`/`menchero` and of their result (4.2).**
- A: `effects` indexed by t with MultiIndex columns (bucket, effect); result indexed by bucket with columns allocation, selection, interaction.
- B: `effects` long with columns t, bucket, allocation, selection, interaction; result has columns bucket, allocation, selection, interaction.

## Section 5

**OPEN-22. `series_id` format (5.1).** `factor_by_year.csv` and `rolling_betas.csv` have no `series_kind`, so the id must tell book from NAV.
- A: `{entity}_{kind}`, e.g. `akre_book`, `akre_nav`, `ivv_book`.
- B: entity id for book series and the NAV ticker for NAV series, e.g. `akre`, `AKRIX`, `ivv`.

**OPEN-23. Which series feeds Chart 2, the holdings-vs-returns exposure chart and the report's Table 2 (5.1, 5.2, 7.1).**
- A: the fund's book series.
- B: the fund's NAV series.

**OPEN-24. Keys of the dict returned by `returns_based` (5.1).**
- A: statsmodels names: params, bse, tvalues, rsquared, resid, nobs.
- B: names matching `factor_fit.csv`: value, se_hac, t_hac, r2, resid_vol_ann, n_months, resid.

## Section 6

**OPEN-25. Output for realised tracking error (6.2).** No schema is given.
- A: new `outputs/tables/te_realised.csv` (fund, te_realised, te_exante_mean, n_months).
- B: new column `te_realised` in `risk_quarterly.csv`, repeated on each row of the fund (amends a fixed schema).

## Section 7

**OPEN-26. Structure of `results` passed to `build_report` (7.1).**
- A: dict of DataFrames keyed by output file stem (`linked`, `factor_by_year`, `risk_quarterly`, `reconstruction`, `cte_positions`, …) plus a `meta` dict.
- B: dict keyed by exhibit (`table1`…`table4`, `chart1`…`chart3`, `meta`) holding frames already filtered to the fund.

**OPEN-27. Linking method shown in the report's Table 1 (7.1).**
- A: Carino only, matching Chart 1; Menchero stays in `linked.csv`.
- B: both, side by side per bucket.

**OPEN-28. Table 4 and the gate in `attribute()` for a user holdings file with no NAV series (7.2).**
- A: page 4 shows book returns only with a line that no NAV was supplied and the gate was not run; results are not excluded.
- B: page 4 is dropped and the report is 3 pages, with the same line on page 1.

**OPEN-29. Tool that renders PDF pages to PNG for `review/section_7_pages/` (7.4).** None is in the dependencies.
- A: add `pymupdf` to the dev extra and the lock.
- B: poppler's `pdftoppm` as an external binary, not a Python dependency.
