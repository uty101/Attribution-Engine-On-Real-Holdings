# Open decisions

OPEN-01 to OPEN-30 were decided in instructions/01_section_1.md, Section B.

## OPEN-31: AKRIX has no price data on yfinance (session 2 stop, step 2.3)

`yfinance.download("AKRIX", start="2015-12-01", end="2026-10-01", auto_adjust=True)` returns 0 rows ("possibly delisted; no price data found"). The other Akre share classes AKREX and AKRSX also return 0 rows. JENIX, POLIX, IVV and IWF return 2723 rows each. Ticker AKRE returns an ETF series from 2025-10-27, and yfinance gives its `fundInceptionDate` as 2009-08-31. That points to the Akre Focus Fund having converted into an ETF, after which Yahoo dropped the mutual fund's history. This is not verified against a filing.

- (a) Keep Akre. The reviewer names a non-yfinance source for the AKRIX NAV total return from 2019-09-30 to the conversion date, plus the splice onto AKRE adjusted closes after it, and that series is committed as the AKRIX column of `data/raw/prices/nav_adjclose.csv`.
- (b) Drop the NAV comparison for Akre. Akre has no NAV series, so it cannot be gated (kickoff 5.4). It is reported as failed under Convention 4.19, with the reason "no NAV data", and the AKRIX column of `nav_adjclose.csv` is left blank. Section D's stop condition for a NAV ticker would then exempt AKRIX.

## OPEN-32: `unpriced_weight` and `other_nosic_weight` can overlap (step 2.5, not reached)

Instruction 02, C 2.5 defines `other_nosic_weight` as the weight of `no_cik` or `no_sic` rows, and `unpriced_weight` as rows with a ticker but no price on the exact `q_start`. A `no_cik` row with no price fits both. CMA and CTRA, the 2 tickers in `missing.csv`, are both `no_cik`. Convention 4.6 makes the 14 buckets exclusive.

- (a) The 2 columns are reported as defined and may overlap; the overlap is printed in the review.
- (b) `other_nosic_weight` counts priced rows only, so that the 2 columns match the Other and Unpriced buckets of Convention 4.6.
