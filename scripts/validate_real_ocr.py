from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.document_classifier import DocumentClassifier
from app.services.document_loader import DocumentLoader
from app.services.extraction_engine import ExtractionEngine
from app.services.ocr_router import OCRRouter
from app.services.preprocessing_service import PreprocessingService


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a real OCR smoke test.")
    parser.add_argument(
        "--document",
        type=Path,
        default=ROOT / "sample_data/generated_cases/SHIP-2026-001/commercial_invoice.pdf",
    )
    args = parser.parse_args()

    source = args.document.resolve()
    if not source.is_file():
        raise SystemExit(f"Validation document not found: {source}")

    with tempfile.TemporaryDirectory(prefix="crossdoc-ocr-") as temp:
        workspace = Path(temp)
        pages = DocumentLoader().load_pages(source, workspace / "pages")
        blocks = []
        for page in pages:
            prepared = workspace / "prepared" / Path(page["image_path"]).name
            PreprocessingService().preprocess_to_file(page["image_path"], prepared)
            blocks.extend(OCRRouter().run(prepared, page["page_number"]))

    if not blocks:
        raise SystemExit("Real OCR smoke test failed: no text blocks were returned.")
    engines = sorted({block.engine_name for block in blocks})
    if "demo_ocr" in engines:
        raise SystemExit("Real OCR smoke test failed: demo OCR was used.")

    text = "\n".join(block.text for block in blocks)
    classification = DocumentClassifier().classify(source.name, text)
    extraction = ExtractionEngine().extract(classification.document_type, blocks)
    normalized = {
        name: payload.get("normalized_value")
        for name, payload in extraction["fields"].items()
        if isinstance(payload, dict) and name != "line_items"
    }

    expected = {
        "invoice_number": "INV-2026-001",
        "po_number": "PO-2026-077",
        "total_amount": 18500,
    }
    mismatches = {
        name: {"expected": value, "actual": normalized.get(name)}
        for name, value in expected.items()
        if normalized.get(name) != value
    }
    if mismatches:
        raise SystemExit(
            "Real OCR smoke test failed: "
            + json.dumps(mismatches, ensure_ascii=True)
        )

    print(
        json.dumps(
            {
                "status": "passed",
                "document": source.name,
                "engines": engines,
                "pages": len(pages),
                "ocr_blocks": len(blocks),
                "average_confidence": round(
                    sum(block.confidence for block in blocks) / len(blocks), 3
                ),
                "document_type": classification.document_type,
                "validated_fields": expected,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
