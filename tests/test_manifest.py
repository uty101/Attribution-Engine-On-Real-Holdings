import hashlib
import json
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


def test_manifest_hashes_match_committed_files():
    manifest = json.loads((RAW / "MANIFEST.json").read_text(encoding="utf-8"))
    on_disk = {
        p.relative_to(RAW).as_posix()
        for p in RAW.rglob("*")
        if p.is_file() and p.name not in ("MANIFEST.json", ".gitkeep")
    }
    assert on_disk == set(manifest["sha256"])
    for rel, digest in manifest["sha256"].items():
        assert hashlib.sha256((RAW / rel).read_bytes()).hexdigest() == digest, rel
