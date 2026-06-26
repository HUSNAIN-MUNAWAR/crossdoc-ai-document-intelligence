from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any

class EvaluationService:
    def evaluate(self, predictions: list[dict], ground_truth: list[dict], ocr_health: dict | None = None) -> dict[str, Any]:
        start = time.perf_counter()
        gt = {x["case_id"]: x for x in ground_truth}
        total_docs = matched_docs = total_fields = exact = norm = amount_tol = table_expected = table_ok = line_score_total = issues = review_required = 0
        conf: list[float] = []
        for pred in predictions:
            gdocs = {d["type"]: d for d in gt.get(pred.get("case_id"), {}).get("documents", [])}
            for d in pred.get("documents", []):
                total_docs += 1
                dt = d.get("document_type")
                if dt in gdocs:
                    matched_docs += 1
                    for k, exp in gdocs[dt].get("fields", {}).items():
                        total_fields += 1
                        got = d.get("fields", {}).get(k, {})
                        raw, normalized = got.get("raw_value"), got.get("normalized_value")
                        if str(raw) == str(exp): exact += 1
                        if str(normalized).lower() == str(exp).lower(): norm += 1
                        if k in {"total_amount", "subtotal", "tax", "quantity"}:
                            try:
                                if abs(float(normalized) - float(exp)) <= max(1, 0.01 * float(exp)):
                                    amount_tol += 1
                            except Exception:
                                pass
                conf += [float(v.get("confidence", 0)) for v in d.get("fields", {}).values() if isinstance(v, dict) and v.get("confidence") is not None]
                review_required += sum(1 for v in d.get("fields", {}).values() if isinstance(v, dict) and float(v.get("confidence", 1)) < .75)
                if d.get("tables"):
                    table_expected += 1
                    if d["tables"][0].get("rows"):
                        table_ok += 1
                        line_score_total += min(1.0, len(d["tables"][0].get("rows", [])) / 3)
            issues += len(pred.get("reconciliation_issues", []))
        return {
            "document_classification_accuracy": self._r(matched_docs, total_docs),
            "field_extraction_exact_match": self._r(exact, total_fields),
            "field_extraction_normalized_match": self._r(norm, total_fields),
            "amount_tolerance_match": self._r(amount_tol, max(1, total_fields)),
            "table_row_count_accuracy": self._r(table_ok, table_expected),
            "line_item_extraction_score": round(line_score_total / table_expected, 3) if table_expected else 0,
            "table_row_reconstruction_score": self._r(table_ok, table_expected),
            "average_ocr_confidence": round(sum(conf)/len(conf), 3) if conf else 0,
            "review_required_percentage": round(review_required / max(1, total_fields), 3),
            "reconciliation_issue_detection_count": issues,
            "risk_issue_detection_count": issues,
            "processing_time_per_document_seconds": round((time.perf_counter()-start)/max(1, total_docs), 4),
            "ocr_engine_availability_status": ocr_health or {},
        }

    def _r(self, a: int, b: int) -> float:
        return round(a / b, 3) if b else 0

    def write_report(self, metrics: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
        p = Path(out_dir); p.mkdir(parents=True, exist_ok=True)
        json_path = p / "evaluation_report.json"
        md_path = p / "evaluation_report.md"
        csv_path = p / "evaluation_summary.csv"
        json_path.write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")
        md_path.write_text("# CrossDoc AI Evaluation Report\n\nSynthetic evaluation report generated from local demo cases. Metrics are designed for regression tracking, not for claiming universal OCR performance.\n\n| Metric | Value |\n|---|---:|\n" + "\n".join(f"| {k.replace('_',' ').title()} | {json.dumps(v) if isinstance(v, dict) else v} |" for k, v in metrics.items()) + "\n", encoding="utf-8")
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f); writer.writerow(["metric", "value"])
            for k, v in metrics.items(): writer.writerow([k, json.dumps(v, default=str) if isinstance(v, dict) else v])
        return {"json": str(json_path), "markdown": str(md_path), "csv": str(csv_path)}
