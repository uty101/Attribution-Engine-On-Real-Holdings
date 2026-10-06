"""Step 7.2: `attribute()` on the committed mini data directory (instructions/07, C.3): 3 synthetic
stocks, 2 holdings dates, its own prices, security map and French factors. Offline (rule 7)."""

from pathlib import Path

import pandas as pd
import pytest
from pypdf import PdfReader

from attrib import attribute
from attrib.config import load_config

ROOT = Path(__file__).resolve().parents[1]
MINI = ROOT / "tests" / "fixtures" / "mini"
CFG = load_config(ROOT / "config.toml")


def test_mini_end_to_end_offline(tmp_path):
    out = attribute(MINI / "holdings_fund.csv", MINI / "holdings_benchmark.csv", "2019-12-31", "2020-03-31",
                    data_dir=MINI, out_dir=tmp_path)
    assert out == tmp_path / "holdings_fund.pdf"
    assert out.read_bytes().startswith(b"%PDF")
    assert 1 <= len(PdfReader(out).pages) <= CFG.report.max_pages


def test_short_window_skips_factor_page(tmp_path):
    """instructions/08, A answer 2: the mini window has 6 monthly returns, fewer than
    `report.min_factor_months`, so page 2 carries the skip line and the PDF has no Table 2."""
    assert CFG.report.min_factor_months > 6
    out = attribute(MINI / "holdings_fund.csv", MINI / "holdings_benchmark.csv", "2019-12-31", "2020-03-31",
                    data_dir=MINI, out_dir=tmp_path)
    text = "\n".join(p.extract_text() for p in PdfReader(out).pages)
    assert f"Fewer than {CFG.report.min_factor_months} monthly returns, so the factor fit is skipped." in text
    assert "Table 2" not in text


def test_missing_cusip_error_lists_and_names_pull_command(tmp_path):
    """Every sec_id absent from the data directory is listed, and the pull command is named."""
    h = pd.read_csv(MINI / "holdings_fund.csv", dtype=str)
    extra = pd.DataFrame([["2019-12-31", "ZZZZ00001", "NEW ONE", "1000", "10"],
                          ["2020-03-31", "ZZZZ00002", "NEW TWO", "1000", "10"]], columns=h.columns)
    path = tmp_path / "holdings_new.csv"
    pd.concat([h, extra], ignore_index=True).to_csv(path, index=False, lineterminator="\n")
    with pytest.raises(ValueError) as err:
        attribute(path, MINI / "holdings_benchmark.csv", "2019-12-31", "2020-03-31", data_dir=MINI,
                  out_dir=tmp_path)
    msg = str(err.value)
    assert "ZZZZ00001" in msg and "ZZZZ00002" in msg
    assert "python scripts/pull_data.py --holdings" in msg and "--benchmark" in msg
    assert not (tmp_path / "holdings_new.pdf").exists()
