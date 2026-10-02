"""Fama-French factors (kickoff Sections 5.7 and 5.8). Section 2 adds the loader only."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# instructions/02_section_2.md, C 2.3: French's column names -> the loader's
FRENCH_COLUMNS = {"Mkt-RF": "mkt", "SMB": "smb", "HML": "hml", "RMW": "rmw", "CMA": "cma", "Mom": "umd", "RF": "rf"}


def read_french_csv(path: str | Path) -> pd.DataFrame:
    """1 committed French monthly block, in percent, indexed by YYYYMM, headers stripped of whitespace."""
    df = pd.read_csv(path, index_col=0, skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    df.index = df.index.astype(int)
    return df.astype("float64")


def load_french(data_dir: str | Path) -> pd.DataFrame:
    """mkt, smb, hml, rmw, cma, umd, rf in decimals (Convention 4.15), indexed by `pd.Period(freq="M")`,
    on the months both files share."""
    d = Path(data_dir) / "raw" / "french"
    df = read_french_csv(d / "ff5_monthly.csv").join(read_french_csv(d / "mom_monthly.csv"), how="inner")
    df = df.rename(columns=FRENCH_COLUMNS)[list(FRENCH_COLUMNS.values())] / 100  # Convention 4.15: percent / 100
    df.index = pd.PeriodIndex([pd.Period(f"{i // 100}-{i % 100:02d}", freq="M") for i in df.index], name="month")
    return df.sort_index()
