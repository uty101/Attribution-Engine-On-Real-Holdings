# Pricing rules
Adjusted close only; yfinance ticker is the OpenFIGI ticker with / replaced by - (BRK/B to BRK-B).
Position return is P(end) / P(q_start) - 1; a name whose prices stop mid-quarter is held as cash at 0 return after its last close.
No price on q_start sends the position to Unpriced, which earns the book's priced, mapped return, as does Unmapped.
Unmapped, unpriced and delisted weight are reported every quarter.
