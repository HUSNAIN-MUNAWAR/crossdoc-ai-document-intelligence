from __future__ import annotations
from datetime import datetime
from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class Case(Base):
    __tablename__ = "cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="created")
    risk_level: Mapped[str] = mapped_column(String(30), default="unknown")
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    average_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    documents: Mapped[list["Document"]] = relationship(back_populates="case", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id_fk: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120), default="application/octet-stream")
    storage_path: Mapped[str] = mapped_column(String(500))
    document_type: Mapped[str] = mapped_column(String(80), default="unknown")
    status: Mapped[str] = mapped_column(String(50), default="uploaded")
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    ocr_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    case: Mapped[Case] = relationship(back_populates="documents")
    pages: Mapped[list["Page"]] = relationship(back_populates="document", cascade="all, delete-orphan")

class Page(Base):
    __tablename__ = "pages"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    page_number: Mapped[int]
    image_path: Mapped[str] = mapped_column(String(500))
    width: Mapped[int] = mapped_column(Integer, default=0)
    height: Mapped[int] = mapped_column(Integer, default=0)
    blur_score: Mapped[float] = mapped_column(Float, default=0.0)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    document: Mapped[Document] = relationship(back_populates="pages")

class OCRBlock(Base):
    __tablename__ = "ocr_blocks"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    page_number: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    normalized_text: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float)
    bbox: Mapped[dict] = mapped_column(JSON, default=dict)
    engine_name: Mapped[str] = mapped_column(String(80))

class ExtractedField(Base):
    __tablename__ = "extracted_fields"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    field_name: Mapped[str] = mapped_column(String(120))
    raw_value: Mapped[str] = mapped_column(Text, default="")
    normalized_value: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    source_page: Mapped[int] = mapped_column(Integer, default=1)
    bbox: Mapped[dict] = mapped_column(JSON, default=dict)

class ExtractedTable(Base):
    __tablename__ = "extracted_tables"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    table_name: Mapped[str] = mapped_column(String(120), default="line_items")
    rows: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

class ReconciliationIssue(Base):
    __tablename__ = "reconciliation_issues"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id_fk: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    issue_type: Mapped[str] = mapped_column(String(120))
    severity: Mapped[str] = mapped_column(String(30))
    message: Mapped[str] = mapped_column(Text)
    source_documents: Mapped[list] = mapped_column(JSON, default=list)
    recommended_action: Mapped[str] = mapped_column(Text, default="")
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)

class RiskReport(Base):
    __tablename__ = "risk_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id_fk: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    score: Mapped[int]
    level: Mapped[str] = mapped_column(String(30))
    factors: Mapped[list] = mapped_column(JSON, default=list)
    recommended_actions: Mapped[list] = mapped_column(JSON, default=list)

class ReviewTask(Base):
    __tablename__ = "review_tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id_fk: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    field_name: Mapped[str] = mapped_column(String(120))
    original_value: Mapped[str] = mapped_column(Text, default="")
    suggested_value: Mapped[str] = mapped_column(Text, default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="open")

class ReviewCorrection(Base):
    __tablename__ = "review_corrections"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("review_tasks.id"))
    original_value: Mapped[str] = mapped_column(Text, default="")
    corrected_value: Mapped[str] = mapped_column(Text, default="")
    reviewer_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ExportJob(Base):
    __tablename__ = "export_jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id_fk: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    export_type: Mapped[str] = mapped_column(String(50))
    file_path: Mapped[str] = mapped_column(String(500))

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    report_path: Mapped[str] = mapped_column(String(500), default="")
