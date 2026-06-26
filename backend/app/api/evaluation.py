from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.config import PROJECT_ROOT

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])
REPORT_PATH = PROJECT_ROOT / "metrics" / "evaluation_report.json"


def _report() -> dict:
    if not REPORT_PATH.is_file():
        raise HTTPException(
            404,
            "Evaluation report not found. Run scripts/evaluate_pipeline.py first.",
        )
    return {
        "id": 1,
        "name": "synthetic-regression-evaluation",
        "metrics": json.loads(REPORT_PATH.read_text(encoding="utf-8")),
        "report_path": str(Path("metrics") / "evaluation_report.md"),
    }


@router.post("/run")
def run_evaluation():
    return _report()


@router.get("/runs")
def list_runs():
    return [_report()]


@router.get("/runs/{run_id}")
def get_run(run_id: int):
    if run_id != 1:
        raise HTTPException(404, "Evaluation run not found")
    return _report()
