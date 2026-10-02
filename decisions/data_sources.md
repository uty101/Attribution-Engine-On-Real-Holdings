# Data sources
Fund holdings: 13F-HR information tables from EDGAR. Benchmark holdings: the ETF's own NPORT-P filings, since the iShares CSV is today's file only.
CUSIP to ticker via OpenFIGI, ticker to CIK via company_tickers.json, CIK to SIC via the submissions API.
Prices and NAVs: yfinance adjusted close, 2015-12-01 to 2026-09-30. Factors: Ken French FF5 and momentum, monthly.
Fund and benchmark join on CUSIP. Only scripts/pull_data.py touches the network.
