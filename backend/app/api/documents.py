from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.case_service import CaseService
from app.services.upload_service import UploadService
from app.services.demo_store import DEMO_DOCUMENTS, DEMO_FIELDS
from app.services.docling_adapter import DoclingAdapter
from app.services.document_processing_service import DocumentProcessingService, decode_json_text
from app.models.domain import Document, ExtractedField, ExtractedTable, OCRBlock

router = APIRouter(tags=["documents"])
cases = CaseService(); uploads = UploadService()

@router.post("/api/cases/{case_id}/documents")
def upload_documents(case_id: str, files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    c = cases.get_case(db, case_id)
    if not c:
        raise HTTPException(404, "Case not found")
    try:
        saved = uploads.save_uploads(db, c, files)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return [{"id": d.id, "filename": d.filename, "document_type": d.document_type, "status": d.status} for d in saved]

@router.get("/api/cases/{case_id}/documents")
def list_documents(case_id: str, db: Session = Depends(get_db)):
    c = cases.get_case(db, case_id)
    if c:
        return [{"id": d.id, "filename": d.filename, "content_type": d.content_type, "document_type": d.document_type, "status": d.status, "quality_score": d.quality_score, "ocr_confidence": d.ocr_confidence} for d in c.documents]
    return DEMO_DOCUMENTS.get(case_id, [])

@router.get("/api/documents/{document_id}")
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if document:
        return DocumentProcessingService().serialize_document(db, document)
    for docs in DEMO_DOCUMENTS.values():
        for d in docs:
            if d["id"] == document_id:
                return d
    raise HTTPException(404, "Document not found")

@router.get("/api/documents/{document_id}/ocr")
def get_ocr(document_id: int, db: Session = Depends(get_db)):
    rows = db.query(OCRBlock).filter(OCRBlock.document_id == document_id).all()
    if rows:
        return [{"text": row.text, "normalized_text": row.normalized_text, "confidence": row.confidence, "bbox": row.bbox, "page_number": row.page_number, "block_type": "text", "engine": row.engine_name, "engine_name": row.engine_name} for row in rows]
    blocks = []
    for i, (k, v) in enumerate(DEMO_FIELDS.get(document_id, {}).items()):
        blocks.append({"text": str(v.get("raw_value")), "normalized_text": str(v.get("normalized_value")), "confidence": v.get("confidence", .8), "bbox": {"x": 70, "y": 100+i*35, "w": 320, "h": 24}, "page_number": 1, "block_type": "text", "engine": "seeded_demo_payload", "engine_name": "seeded_demo_payload", "raw_engine_payload": {"field": k}})
    return blocks

@router.get("/api/documents/{document_id}/fields")
def get_fields(document_id: int, db: Session = Depends(get_db)):
    rows = db.query(ExtractedField).filter(ExtractedField.document_id == document_id).all()
    if rows:
        return {row.field_name: {"raw_value": decode_json_text(row.raw_value), "normalized_value": decode_json_text(row.normalized_value), "confidence": row.confidence, "source_page": row.source_page, "bbox": row.bbox, "warnings": []} for row in rows}
    return DEMO_FIELDS.get(document_id, {})

@router.get("/api/documents/{document_id}/tables")
def get_tables(document_id: int, db: Session = Depends(get_db)):
    rows = db.query(ExtractedTable).filter(ExtractedTable.document_id == document_id).all()
    if rows:
        return [{"table_name": row.table_name, "rows": row.rows, "confidence": row.confidence} for row in rows]
    return [{"table_name": "line_items", "columns": ["SKU", "Description", "Qty", "Unit", "Total"], "rows": [{"cells": ["SKU", "Description", "Qty", "Unit", "Total"]}, {"cells": ["BG-100", "Baguette trays", "500", "37", "18500"]}], "confidence": .76, "warnings": [], "source_page": 1, "source_bbox": {"x": 55, "y": 420, "w": 480, "h": 80}}]

@router.get("/api/documents/{document_id}/docling-parse")
def docling_parse(document_id: int, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    path = document.storage_path if document else f"document-{document_id}.pdf"
    return DoclingAdapter().parse_document(path).to_dict()

@router.post("/api/documents/{document_id}/reprocess")
def reprocess_document(document_id: int, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Document not found")
    try:
        return DocumentProcessingService().process_document(db, document)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
