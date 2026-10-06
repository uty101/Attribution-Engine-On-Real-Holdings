"""Step 8.3 (instructions/08, D.1): README.md is rendered from docs/README_template.md, every
number in its prose a placeholder filled from answers.csv and every table filled from its CSV.

This reads the committed README.md and outputs/tables/, which instruction 08 requires of these
tests; that is the one exception to rule 7 here, and it is listed in review/section_8.md."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_readme  # noqa: E402

TEMPLATE = ROOT / "docs" / "README_template.md"


def test_readme_tables_match_csvs():
    """Rendering the template again from the committed CSVs gives the committed README byte for byte."""
    again = build_readme.render(TEMPLATE.read_text(encoding="utf-8")).encode("utf-8")
    assert again == (ROOT / "README.md").read_bytes()


def _answers_section(text: str) -> str:
    m = re.search(r"^## Answers\n(.*?)^## ", text, flags=re.S | re.M)
    assert m, "no ## Answers section in the template"
    return m.group(1)


def test_readme_has_no_bare_numbers_in_answers():
    """No digit in the template's Answers section outside a placeholder, except years, the 28 and
    84 counts, and the date 2026-06-30 (instructions/08, D.1)."""
    text = _answers_section(TEMPLATE.read_text(encoding="utf-8"))
    assert build_readme.VALUE.search(text), "the Answers section has no placeholders"
    text = build_readme.VALUE.sub(" ", text)
    text = text.replace("2026-06-30", " ")
    text = re.sub(r"(?<![0-9])(?:19|20)[0-9]{2}(?![0-9])", " ", text)
    text = re.sub(r"(?<![0-9])(?:28|84)(?![0-9])", " ", text)
    bare = re.findall(r".{0,30}[0-9].{0,30}", text)
    assert not bare, bare
