from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "animation" / "crossdoc_reconciliation_sequence.json"
REEL = ROOT / "frontend" / "public" / "animation" / "crossdoc-reconciliation-reel.html"


def test_reconciliation_animation_uses_real_post_ocr_services() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/generate_reconciliation_animation.py"],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": "backend"},
        check=True,
        capture_output=True,
        text=True,
    )
    assert "issues:" in result.stdout

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    reel = REEL.read_text(encoding="utf-8")
    assert manifest["source"]["synthetic"] is True
    assert manifest["source"]["document_count"] == 6
    assert manifest["model"]["reconciliation"].endswith("ReconciliationEngine")
    assert manifest["model"]["risk"].endswith("RiskEngine")
    assert manifest["pipeline"]["reconciliation_issue_count"] >= 2
    assert manifest["pipeline"]["risk"]["score"] > 0
    assert len(manifest["events"]) == 8
    assert "synthetic fixture" in reel.lower()
