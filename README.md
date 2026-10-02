# Attribution Engine on Real Holdings

A performance and risk attribution engine built on real SEC 13F holdings for Akre, Jensen and Polen, against benchmark books from iShares N-PORT filings.
It splits each fund's excess return into sector allocation, stock selection and interaction (Brinson-Fachler, linked by Carino and Menchero).
It explains monthly returns with the Fama-French 5 factors plus momentum, and decomposes ex-ante tracking error by position and sector.
It measures how far the quarter-start 13F book misses the fund's reported NAV return, which shows what 13F data cannot see.
One function, `attribute()`, takes a holdings file and a benchmark file and returns a PDF report.

Results pending.
