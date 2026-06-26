from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.domain import (
    Case,
    Document,
    ExtractedField,
    ExtractedTable,
    OCRBlock,
    Page,
    ReconciliationIssue,
    ReviewTask,
    RiskReport,
)
from app.services.document_classifier import DocumentClassifier
from app.services.document_loader import DocumentLoader
from app.services.extraction_engine import ExtractionEngine
from app.services.ocr_router import OCRRouter
from app.services.preprocessing_service import PreprocessingService
from app.services.reconciliation_engine import ReconciliationEngine
from app.services.review_service import ReviewService
from app.services.risk_engine import RiskEngine


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True)


def decode_json_text(value: str) -> Any:
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return value


class DocumentProcessingService:
    """Runs and persists the local document-intelligence pipeline."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.loader = DocumentLoader()
        self.preprocessor = PreprocessingService()
        self.classifier = DocumentClassifier()
        self.extractor = ExtractionEngine()

    def process_document(self, db: Session, document: Document) -> dict[str, Any]:
        self._clear_document_results(db, document.id)
        document.status = "processing"
        db.commit()

        workspace = self.settings.storage_path / "processed" / str(document.id)
        pages = self.loader.load_pages(document.storage_path, workspace / "pages")
        all_blocks = []
        quality_scores: list[float] = []

        try:
            for page in pages:
                source_path = Path(page["image_path"])
                prepared_path = workspace / "preprocessed" / source_path.name
                quality = self.preprocessor.preprocess_to_file(source_path, prepared_path)
                quality_scores.append(float(quality["quality_score"]))

                db.add(
                    Page(
                        document_id=document.id,
                        page_number=page["page_number"],
                        image_path=str(source_path),
                        width=page["width"],
                        height=page["height"],
                        blur_score=quality["blur_score"],
                        quality_score=quality["quality_score"],
                    )
                )
                all_blocks.extend(
                    OCRRouter().run(prepared_path, page_number=page["page_number"])
                )

            if not all_blocks:
                raise RuntimeError(
                    "No OCR text was produced. Install Tesseract or PaddleOCR, "
                    "or explicitly enable CROSSDOC_DEMO_OCR for demo-only runs."
                )

            text = "\n".join(block.text for block in all_blocks)
            classification = self.classifier.classify(document.filename, text)
            extracted = self.extractor.extract(classification.document_type, all_blocks)
            self._persist_results(db, document, all_blocks, extracted)

            document.document_type = classification.document_type
            document.quality_score = round(
                sum(quality_scores) / max(1, len(quality_scores)), 3
            )
            document.ocr_confidence = round(
                sum(block.confidence for block in all_blocks) / len(all_blocks), 3
            )
            document.status = "processed"
            db.commit()
            db.refresh(document)
            return self.serialize_document(db, document, extracted)
        except Exception:
            db.rollback()
            document = db.get(Document, document.id)
            if document is not None:
                document.status = "failed"
                db.commit()
            raise

    def _clear_document_results(self, db: Session, document_id: int) -> None:
        for model in (OCRBlock, ExtractedField, ExtractedTable, Page, ReviewTask):
            db.query(model).filter(
                getattr(model, "document_id") == document_id
            ).delete(synchronize_session=False)
        db.flush()

    def _persist_results(
        self,
        db: Session,
        document: Document,
        blocks: list[Any],
        extracted: dict[str, Any],
    ) -> None:
        for block in blocks:
            db.add(
                OCRBlock(
                    document_id=document.id,
                    page_number=block.page_number,
                    text=block.text,
                    normalized_text=block.normalized_text,
                    confidence=block.confidence,
                    bbox=block.bbox,
                    engine_name=block.engine_name,
                )
            )

        fields = extracted.get("fields", {})
        for name, payload in fields.items():
            if name == "line_items" or not isinstance(payload, dict):
                continue
            db.add(
                ExtractedField(
                    document_id=document.id,
                    field_name=name,
                    raw_value=_json_text(payload.get("raw_value", "")),
                    normalized_value=_json_text(payload.get("normalized_value", "")),
                    confidence=float(payload.get("confidence", 0) or 0),
                    source_page=int(payload.get("source_page", 1) or 1),
                    bbox=payload.get("bbox", {}) or {},
                )
            )

        for table in extracted.get("tables", []):
            db.add(
                ExtractedTable(
                    document_id=document.id,
                    table_name=table.get("table_name", "line_items"),
                    rows=table.get("rows", []),
                    confidence=float(table.get("confidence", 0) or 0),
                )
            )

        tasks = ReviewService().create_tasks_for_fields(
            document.case.case_id,
            document.id,
            fields,
            self.settings.review_confidence_threshold,
        )
        for task in tasks:
            db.add(
                ReviewTask(
                    case_id_fk=document.case_id_fk,
                    document_id=document.id,
                    field_name=task["field_name"],
                    original_value=str(task["original_value"]),
                    suggested_value=str(task["suggested_value"]),
                    reason=task["reason"],
                    confidence=task["confidence"],
                    status=task["status"],
                )
            )

    def serialize_document(
        self,
        db: Session,
        document: Document,
        extracted: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if extracted is None:
            fields = {
                row.field_name: {
                    "raw_value": decode_json_text(row.raw_value),
                    "normalized_value": decode_json_text(row.normalized_value),
                    "confidence": row.confidence,
                    "source_page": row.source_page,
                    "bbox": row.bbox,
                    "warnings": [],
                }
                for row in db.query(ExtractedField)
                .filter(ExtractedField.document_id == document.id)
                .all()
            }
            tables = [
                {
                    "table_name": row.table_name,
                    "rows": row.rows,
                    "confidence": row.confidence,
                }
                for row in db.query(ExtractedTable)
                .filter(ExtractedTable.document_id == document.id)
                .all()
            ]
        else:
            fields = extracted.get("fields", {})
            tables = extracted.get("tables", [])

        return {
            "id": document.id,
            "filename": document.filename,
            "document_type": document.document_type,
            "status": document.status,
            "quality_score": document.quality_score,
            "ocr_confidence": document.ocr_confidence,
            "page_count": db.query(Page)
            .filter(Page.document_id == document.id)
            .count(),
            "ocr_block_count": db.query(OCRBlock)
            .filter(OCRBlock.document_id == document.id)
            .count(),
            "fields": fields,
            "tables": tables,
        }


class CaseProcessingService:
    def __init__(self) -> None:
        self.documents = DocumentProcessingService()

    def process_case(self, db: Session, case: Case) -> dict[str, Any]:
        if not case.documents:
            raise ValueError("Upload at least one document before processing the case.")

        case.status = "processing"
        db.commit()
        processed = [
            self.documents.process_document(db, document) for document in case.documents
        ]
        issues = [
            issue.to_dict() for issue in ReconciliationEngine().reconcile(processed)
        ]
        risk = RiskEngine().calculate(processed, issues)

        db.query(ReconciliationIssue).filter(
            ReconciliationIssue.case_id_fk == case.id
        ).delete(synchronize_session=False)
        db.query(RiskReport).filter(RiskReport.case_id_fk == case.id).delete(
            synchronize_session=False
        )

        for issue in issues:
            db.add(
                ReconciliationIssue(
                    case_id_fk=case.id,
                    issue_type=issue["issue_type"],
                    severity=issue["severity"],
                    message=issue["message"],
                    source_documents=issue["source_documents"],
                    recommended_action=issue["recommended_action"],
                )
            )
        db.add(
            RiskReport(
                case_id_fk=case.id,
                score=risk["score"],
                level=risk["level"],
                factors=risk["factors"],
                recommended_actions=risk["recommended_actions"],
            )
        )

        confidences = [d["ocr_confidence"] for d in processed]
        case.average_confidence = round(sum(confidences) / len(confidences), 3)
        case.risk_score = risk["score"]
        case.risk_level = risk["level"]
        case.status = "needs_review" if risk["score"] > 25 else "processed"
        db.commit()

        return {
            "case_id": case.case_id,
            "status": case.status,
            "documents": processed,
            "reconciliation_issues": issues,
            "risk": risk,
        }
