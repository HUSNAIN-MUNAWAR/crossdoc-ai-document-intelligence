"""Capture CrossDoc's real Tesseract-backed six-document runtime."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys
import tempfile

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.document_classifier import DocumentClassifier  # noqa: E402
from app.services.extraction_engine import ExtractionEngine  # noqa: E402
from app.services.layout_detector import LayoutDetector  # noqa: E402
from app.services.ocr_router import OCRRouter, inspect_ocr_health  # noqa: E402
from app.services.preprocessing_service import PreprocessingService  # noqa: E402
from app.services.reconciliation_engine import ReconciliationEngine  # noqa: E402
from app.services.risk_engine import RiskEngine  # noqa: E402


GROUND_TRUTH = ROOT / "sample_data" / "ground_truth" / "SHIP-2026-001.json"
CASE_ROOT = ROOT / "sample_data" / "generated_cases" / "SHIP-2026-001"
OUTPUT_ROOT = ROOT / "docs" / "animation" / "runtime-evidence"
VIDEO_PATH = OUTPUT_ROOT / "crossdoc-runtime.mp4"
POSTER_PATH = OUTPUT_ROOT / "crossdoc-runtime-poster.png"
BLOCKS_PATH = OUTPUT_ROOT / "crossdoc-ocr-blocks.csv"
SUMMARY_PATH = OUTPUT_ROOT / "crossdoc-runtime-summary.json"
FRAMES_PER_EVENT = 5
FPS = 5


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display(value: object) -> str:
    return str(value).encode("ascii", "replace").decode("ascii")


def put_text(canvas: np.ndarray, value: object, x: int, y: int, scale: float = 0.56, color: tuple[int, int, int] = (220, 232, 236), thickness: int = 1) -> None:
    cv2.putText(canvas, display(value), (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)


def field_value(fields: dict[str, object], name: str) -> object:
    payload = fields.get(name)
    return payload.get("normalized_value") if isinstance(payload, dict) else None


def run_case() -> dict[str, object]:
    truth = json.loads(GROUND_TRUTH.read_text(encoding="utf-8"))
    health = inspect_ocr_health()
    classifier = DocumentClassifier()
    extractor = ExtractionEngine()
    layout_detector = LayoutDetector()
    documents: list[dict[str, object]] = []
    blocks_for_csv: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="crossdoc-real-runtime-") as temp:
        workspace = Path(temp)
        for truth_doc in truth["documents"]:
            doc_type = truth_doc["type"]
            source = CASE_ROOT / f"{doc_type}_clean.png"
            if not source.is_file():
                raise FileNotFoundError(source)
            prepared = workspace / "prepared" / source.name
            PreprocessingService().preprocess_to_file(source, prepared)
            router = OCRRouter()
            blocks = router.run(prepared, 1)
            if any(block.engine_name == "demo_ocr" for block in blocks):
                raise RuntimeError(f"demo OCR was used for {source.name}")
            text = "\n".join(block.text for block in blocks)
            classified = classifier.classify(source.name, text)
            extracted = extractor.extract(classified.document_type, blocks)
            layout_regions = layout_detector.detect(ocr_blocks=[block.to_dict() for block in blocks], page_number=1)
            actual_fields = extracted["fields"]
            mismatches = {}
            for name, expected in truth_doc["fields"].items():
                actual = field_value(actual_fields, name)
                if actual != expected:
                    mismatches[name] = {"expected": expected, "actual": actual}
            for block_index, block in enumerate(blocks, start=1):
                blocks_for_csv.append(
                    {
                        "document": source.name,
                        "block_index": block_index,
                        "text": block.text,
                        "confidence": block.confidence,
                        "engine": block.engine_name,
                        "page_number": block.page_number,
                        "bbox": json.dumps(block.bbox, sort_keys=True),
                    }
                )
            documents.append(
                {
                    "document_type": classified.document_type,
                    "filename": source.name,
                    "source_sha256": file_sha256(source),
                    "ocr_engine": sorted({block.engine_name for block in blocks}),
                    "ocr_block_count": len(blocks),
                    "ocr_confidence": round(sum(block.confidence for block in blocks) / len(blocks), 6) if blocks else 0.0,
                    "ocr_text": text,
                    "classification_confidence": classified.confidence,
                    "classification_evidence": classified.evidence,
                    "fields": actual_fields,
                    "tables": extracted["tables"],
                    "missing_required_fields": extracted["missing_required_fields"],
                    "layout_region_count": len(layout_regions),
                    "ground_truth_mismatches": mismatches,
                    "quality_score": round(sum(block.confidence for block in blocks) / len(blocks), 6) if blocks else 0.0,
                }
            )

    issues = [issue.to_dict() for issue in ReconciliationEngine().reconcile(documents)]
    risk = RiskEngine().calculate(documents, issues)
    return {
        "case_id": truth["case_id"],
        "intentional_issue": truth["intentional_issue"],
        "source": {
            "ground_truth": str(GROUND_TRUTH.relative_to(ROOT)),
            "ground_truth_sha256": file_sha256(GROUND_TRUTH),
            "image_case_root": str(CASE_ROOT.relative_to(ROOT)),
            "document_count": len(documents),
        },
        "ocr_health": health,
        "model": {
            "engine": "tesseract",
            "version": health["tesseract"]["version"],
            "language": health["language"],
            "binary": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            "traineddata": r"C:\Program Files\Tesseract-OCR\tessdata\eng.traineddata",
            "demo_ocr_used": False,
            "learned_checkpoint": "eng.traineddata",
        },
        "documents": documents,
        "reconciliation": {
            "issues": issues,
            "issue_count": len(issues),
            "issue_types": [issue["type"] for issue in issues],
        },
        "risk": risk,
        "blocks": blocks_for_csv,
    }


def evidence_lines(run: dict[str, object], event_index: int) -> list[str]:
    documents = run["documents"]
    if event_index == 0:
        return [f"case: {run['case_id']}", f"documents: {len(documents)}", f"intentional issue: {run['intentional_issue']}", "inputs: committed clean PNG variants"]
    if event_index == 1:
        return [f"{doc['filename'][:34]} blocks={doc['ocr_block_count']} conf={doc['ocr_confidence']:.2f}" for doc in documents]
    if event_index == 2:
        return [f"{doc['filename'][:30]} -> {doc['document_type']} ({doc['classification_confidence']:.2f})" for doc in documents]
    if event_index == 3:
        lines = []
        for doc in documents[:3]:
            fields = doc["fields"]
            values = [f"{name}={field_value(fields, name)}" for name in ("invoice_number", "po_number", "destination")]
            lines.append(f"{doc['filename'][:20]}: " + ", ".join(values))
        return lines
    if event_index == 4:
        return [f"issues: {run['reconciliation']['issue_count']}", *run["reconciliation"]["issue_types"][:6]]
    if event_index == 5:
        return [f"risk score: {run['risk']['score']}", f"risk level: {run['risk']['level']}", f"confidence: {run['risk']['confidence']:.2f}", f"action: {run['risk']['recommended_action']}"]
    if event_index == 6:
        mismatches = sum(len(doc["ground_truth_mismatches"]) for doc in documents)
        return [f"field mismatches: {mismatches}", "values are compared with committed ground truth", "review task remains human-facing"]
    return ["JSON / CSV evidence preserved", "no customs, tax, payment, or carrier action", "Tesseract only; demo OCR disabled"]


def render_frame(run: dict[str, object], event_index: int, frame_number: int, frame_count: int) -> np.ndarray:
    canvas = np.full((720, 1280, 3), (7, 20, 31), dtype=np.uint8)
    titles = ["Case received", "Real Tesseract OCR", "Document classification", "Field extraction", "Cross-document reconciliation", "Explainable risk", "Human review packet", "Evidence export boundary"]
    details = [
        "Six committed clean document images enter one case.",
        "OCRRouter runs Tesseract; no demo blocks are allowed.",
        "DocumentClassifier assigns types from actual OCR text.",
        "ExtractionEngine normalizes the OCR blocks into fields.",
        "ReconciliationEngine compares actual extracted documents.",
        "RiskEngine scores the actual findings and returns an action.",
        "OCR mismatches remain visible for human correction.",
        "The report preserves evidence; no external action is executed.",
    ]
    put_text(canvas, "CrossDoc AI - REAL OCR LOCAL RUNTIME", 40, 48, 0.98, (235, 242, 246), 2)
    put_text(canvas, f"event {event_index + 1}/8  |  frame {frame_number}/{frame_count}", 40, 80, 0.56, (143, 163, 180))
    cv2.rectangle(canvas, (34, 108), (820, 660), (31, 65, 82), 2)
    cv2.rectangle(canvas, (852, 108), (1240, 660), (31, 65, 82), 2)
    put_text(canvas, titles[event_index], 60, 158, 0.78, (102, 213, 234), 2)
    put_text(canvas, details[event_index], 60, 194, 0.52, (210, 222, 230))
    for index, line in enumerate(evidence_lines(run, event_index)):
        put_text(canvas, line, 66, 260 + index * 38, 0.54, (221, 231, 235))
    health = run["ocr_health"]
    panel = [
        "EXECUTED PATH",
        "OCRRouter -> Tesseract",
        f"engine: {run['model']['version']}",
        "demo OCR: false",
        "",
        "CASE RESULT",
        f"docs: {len(run['documents'])}",
        f"issues: {run['reconciliation']['issue_count']}",
        f"risk: {run['risk']['score']} / {run['risk']['level']}",
        "",
        "CLAIM BOUNDARY",
        f"tesseract: {health['tesseract']['status']}",
        "synthetic test documents only",
        "no external action executed",
    ]
    for index, line in enumerate(panel):
        heading = index in {0, 5, 10}
        put_text(canvas, line, 882, 158 + index * 31, 0.54 if not heading else 0.61, (220, 232, 236) if not heading else (102, 213, 234), 1 if not heading else 2)
    put_text(canvas, "real OCR blocks | actual mismatches retained | no fabricated accuracy", 40, 695, 0.52, (143, 163, 180))
    return canvas


def main() -> None:
    run = run_case()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(VIDEO_PATH), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (1280, 720))
    if not writer.isOpened():
        raise RuntimeError(f"unable to open video writer for {VIDEO_PATH}")
    frame_count = 8 * FRAMES_PER_EVENT
    first_frame: np.ndarray | None = None
    frame_number = 0
    try:
        for event_index in range(8):
            for _ in range(FRAMES_PER_EVENT):
                frame_number += 1
                frame = render_frame(run, event_index, frame_number, frame_count)
                first_frame = first_frame if first_frame is not None else frame.copy()
                writer.write(frame)
    finally:
        writer.release()
    if first_frame is None:
        raise RuntimeError("no runtime frames were produced")
    cv2.imwrite(str(POSTER_PATH), first_frame)

    with BLOCKS_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer_csv = csv.DictWriter(handle, fieldnames=["document", "block_index", "text", "confidence", "engine", "page_number", "bbox"])
        writer_csv.writeheader()
        writer_csv.writerows(run["blocks"])

    traineddata = Path(run["model"]["traineddata"])
    report = {
        "run_type": "crossdoc_real_tesseract_runtime_video",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": "py -3.12 -u scripts/generate_real_runtime_video.py",
        "source": run["source"],
        "model": {**run["model"], "traineddata_sha256": file_sha256(traineddata) if traineddata.is_file() else None},
        "runtime": {"python": platform.python_version(), "opencv": cv2.__version__, "numpy": np.__version__, "platform": platform.platform(), "device": "cpu"},
        "ocr_health": run["ocr_health"],
        "documents": run["documents"],
        "reconciliation": run["reconciliation"],
        "risk": run["risk"],
        "outputs": {
            "video": str(VIDEO_PATH.relative_to(ROOT)),
            "poster": str(POSTER_PATH.relative_to(ROOT)),
            "ocr_blocks_csv": str(BLOCKS_PATH.relative_to(ROOT)),
            "sha256": {str(path.relative_to(ROOT)): file_sha256(path) for path in (VIDEO_PATH, POSTER_PATH, BLOCKS_PATH)},
        },
        "interpretation": [
            "This trace uses real Tesseract OCR blocks from the committed clean PNG inputs; demo OCR was disabled.",
            "The PDF validator remains a separate limitation because its rendered PDF fixture does not expose the expected text to OCR.",
            "OCR mismatches against the committed ground truth are preserved and are not converted into passing metrics.",
            "The input documents are synthetic test fixtures, not customer records or production accuracy evidence.",
        ],
    }
    SUMMARY_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"video": str(VIDEO_PATH), "poster": str(POSTER_PATH), "summary": str(SUMMARY_PATH), "documents": len(run["documents"]), "blocks": len(run["blocks"])}, indent=2))


if __name__ == "__main__":
    main()
