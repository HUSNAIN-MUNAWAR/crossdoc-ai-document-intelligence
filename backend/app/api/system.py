from fastapi import APIRouter
from app.core.config import get_settings
from app.services.ocr_router import OCRRouter, inspect_ocr_health
router = APIRouter(tags=["system"])

@router.get("/health")
def health():
    return {"status": "ok", "service": "crossdoc-ai-backend", "database": "configured", "worker": "configured", "storage": "local/minio-ready"}

@router.get("/api/system/ocr-engines")
def engines():
    return OCRRouter().available_engines()

@router.get("/api/system/ocr-health")
def ocr_health():
    return inspect_ocr_health()

@router.get("/api/system/settings")
def settings():
    s = get_settings()
    return {"app_env": s.app_env, "demo_mode": s.demo_ocr_enabled, "ocr_confidence_threshold": s.ocr_confidence_threshold, "review_confidence_threshold": s.review_confidence_threshold, "ocr_lang": s.ocr_lang, "layout_mode": s.layout_mode}
