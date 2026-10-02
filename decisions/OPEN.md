# Open decisions

OPEN-01 to OPEN-30 were decided in instructions/01_section_1.md, Section B. OPEN-31 (Akre NAV from N-PORT B.5) and OPEN-32 (option a) were decided in instructions/02b_section_2_completion.md, Section B.

## OPEN-33: Akre has no monthly NAV return for August, September and October 2025 (session 2b stop, step 2.1b)

Akre's last NPORT-P (`0000894189-25-009200`, filed 2025-09-26) is for period 2025-07-31, so the B.5 returns of AKRIX (class `C000080287`, "Institutional Class") run from 2019-08 to 2025-07 with no gap. After it, series `S000026760` filed only an N-CSR (2025-10-06), a 24F-2NT (2025-10-08) and an N-CEN (2025-10-10). The series has no ETF class, since AKRE is its own series (`S000089351`), so source 2 is empty. Source 3, AKRE on yfinance from 2025-10-27, applies only to months whose first day is after 2025-10-27, which is November 2025 on. That leaves 2025-08, 2025-09 and 2025-10 missing: 3 months, against the limit of 1 in 02b step 2.1b.

- (a) Fill the 3 months from sources the reviewer names, entered as rows of `data/manual/overrides.csv` with kind `nav_return` and a source note. One example: August 2025 backed out of the fiscal-year total return in the 2025-10-06 N-CSR (fiscal year to 2025-08-31) and the 11 B.5 months before it. September 2025, and October 2025 to the conversion, would come from AKRIX daily NAVs published by the fund, then AKRE from 2025-10-27.
- (b) Accept the gap. Akre's quarterly NAV return is blank for the 2 return quarters that need a missing month (t = 24, 2025-06-30 to 2025-09-30, and t = 25, 2025-09-30 to 2025-12-31). Those 2 quarters drop out of Akre's gate correlation and gap statistics, and the review reports them.
