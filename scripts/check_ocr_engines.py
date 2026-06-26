from __future__ import annotations
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.ocr_router import inspect_ocr_health

if __name__ == "__main__":
    print(json.dumps(inspect_ocr_health(), indent=2))
