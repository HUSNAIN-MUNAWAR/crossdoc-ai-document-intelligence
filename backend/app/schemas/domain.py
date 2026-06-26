from typing import Any
from pydantic import BaseModel, Field

class CaseCreate(BaseModel):
    case_id: str = Field(..., examples=["SHIP-2026-001"])
    title: str

class ReviewUpdate(BaseModel):
    corrected_value: str | None = None
    reviewer_note: str | None = None
    status: str = "corrected"

class OCRResult(BaseModel):
    text: str
    confidence: float
    bbox: dict[str, Any]
    page_number: int
    engine_name: str
    normalized_text: str = ""
