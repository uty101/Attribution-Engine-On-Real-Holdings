# Sectors: Fama-French 12
SIC does not map to 11 GICS-style buckets without invented rules, so sectors are French's 12 industries from Siccodes12.
The map is applied identically to fund and benchmark and labelled FF12, never GICS.
Unmapped (no ticker) and Unpriced (no price at quarter start) are explicit buckets on both sides, giving 14 in all.
A mapped ticker with no SIC, or a SIC in no FF12 range, goes to Other and is logged.
