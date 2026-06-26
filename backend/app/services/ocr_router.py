from __future__ import annotations

import importlib
import importlib.metadata
import logging
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.services.postprocessor import PostProcessor

logger = logging.getLogger("crossdoc.ocr")


def _version(package: str) -> str | None:
    try:
        return importlib.metadata.version(package)
    except Exception:
        return None


def _check_import(module: str) -> tuple[bool, str | None]:
    try:
        imported = importlib.import_module(module)
        return True, getattr(imported, "__version__", None) or _version(module.split(".")[0])
    except Exception:
        return False, None


def _resolve_binary(binary: str) -> str | None:
    resolved = shutil.which(binary)
    if resolved:
        return resolved
    if binary == "tesseract":
        candidates = [
            os.getenv("TESSERACT_CMD"),
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        for candidate in candidates:
            if candidate and Path(candidate).is_file():
                return candidate
    return None


def _binary_version(binary: str, args: list[str] | None = None) -> tuple[bool, str | None]:
    resolved = _resolve_binary(binary)
    if not resolved:
        return False, None
    try:
        proc = subprocess.run([resolved] + (args or ["--version"]), capture_output=True, text=True, timeout=5)
        text = (proc.stdout or proc.stderr or "").strip().splitlines()[0]
        return True, text
    except Exception:
        return True, None


def inspect_ocr_health() -> dict[str, Any]:
    settings = get_settings()
    paddle_ok, paddle_version = _check_import("paddleocr")
    pytess_ok, pytess_version = _check_import("pytesseract")
    docling_ok, docling_version = _check_import("docling")
    layout_ok, layout_version = _check_import("layoutparser")
    cv2_ok, cv2_version = _check_import("cv2")
    tesseract_ok, tesseract_version = _binary_version("tesseract")
    poppler_pdfinfo_ok, poppler_version = _binary_version("pdfinfo", ["-v"])
    return {
        "paddleocr": {"available": paddle_ok, "version": paddle_version, "status": "ready" if paddle_ok else "not_installed"},
        "tesseract": {"available": tesseract_ok and pytess_ok, "binary_available": tesseract_ok, "pytesseract_available": pytess_ok, "version": tesseract_version or pytess_version, "status": "ready" if (tesseract_ok and pytess_ok) else "not_ready"},
        "docling": {"available": docling_ok, "version": docling_version, "status": "ready" if docling_ok else "not_installed"},
        "layoutparser": {"available": layout_ok, "version": layout_version, "status": "ready" if layout_ok else "optional_not_installed"},
        "poppler": {"available": poppler_pdfinfo_ok, "version": poppler_version, "status": "ready" if poppler_pdfinfo_ok else "not_found"},
        "opencv": {"available": cv2_ok, "version": cv2_version, "status": "ready" if cv2_ok else "not_installed"},
        "demo_mode": {"enabled": settings.demo_ocr_enabled, "env_var": "CROSSDOC_DEMO_OCR"},
        "language": settings.ocr_lang,
    }


def calibrate_confidence(value: Any, engine: str) -> float:
    try:
        score = float(value)
    except Exception:
        score = 0.0
    if engine == "tesseract" and score > 1:
        score = score / 100.0
    if engine == "demo_ocr":
        score = min(score, 0.68)
    return max(0.0, min(1.0, score))


@dataclass
class OCRBlockResult:
    text: str
    confidence: float
    bbox: dict[str, float]
    page_number: int
    block_type: str = "text"
    engine: str = "unknown"
    raw_engine_payload: dict[str, Any] = field(default_factory=dict)
    normalized_text: str = ""

    def __post_init__(self) -> None:
        self.confidence = calibrate_confidence(self.confidence, self.engine)
        self.normalized_text = self.normalized_text or PostProcessor().repair_text_preserving_words(self.text)
        self.bbox = validate_bbox(self.bbox)

    @property
    def engine_name(self) -> str:
        return self.engine

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["engine_name"] = self.engine
        return data


def validate_bbox(bbox: dict[str, Any] | None) -> dict[str, float]:
    bbox = bbox or {}
    x = max(0.0, float(bbox.get("x", 0) or 0))
    y = max(0.0, float(bbox.get("y", 0) or 0))
    w = max(0.0, float(bbox.get("w", bbox.get("width", 0)) or 0))
    h = max(0.0, float(bbox.get("h", bbox.get("height", 0)) or 0))
    return {"x": x, "y": y, "w": w, "h": h}


class PaddleOCREngine:
    name = "paddleocr"

    def __init__(self, lang: str = "en"):
        from paddleocr import PaddleOCR
        self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)

    def run(self, image_path: str | Path, page_number: int = 1) -> list[OCRBlockResult]:
        out: list[OCRBlockResult] = []
        result = self.ocr.ocr(str(image_path), cls=True) or []
        for page in result:
            for line in page or []:
                pts, payload = line
                text, conf = payload
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                out.append(OCRBlockResult(
                    text=str(text),
                    confidence=calibrate_confidence(conf, self.name),
                    bbox={"x": min(xs), "y": min(ys), "w": max(xs)-min(xs), "h": max(ys)-min(ys)},
                    page_number=page_number,
                    block_type="text",
                    engine=self.name,
                    raw_engine_payload={"points": pts, "confidence": conf},
                ))
        return out


class TesseractEngine:
    name = "tesseract"

    def __init__(self, lang: str = "eng"):
        self.lang = lang or "eng"

    def run(self, image_path: str | Path, page_number: int = 1) -> list[OCRBlockResult]:
        import pytesseract
        from PIL import Image
        binary = _resolve_binary("tesseract")
        if binary:
            pytesseract.pytesseract.tesseract_cmd = binary
        data = pytesseract.image_to_data(Image.open(image_path), lang=self.lang, output_type=pytesseract.Output.DICT)
        out: list[OCRBlockResult] = []
        for i, txt in enumerate(data.get("text", [])):
            if not str(txt).strip():
                continue
            conf = calibrate_confidence(data.get("conf", [0])[i], self.name)
            out.append(OCRBlockResult(
                text=str(txt).strip(),
                confidence=conf,
                bbox={"x": data["left"][i], "y": data["top"][i], "w": data["width"][i], "h": data["height"][i]},
                page_number=page_number,
                block_type="text",
                engine=self.name,
                raw_engine_payload={"level": data.get("level", [None])[i], "confidence": data.get("conf", [None])[i]},
            ))
        return out


class DemoOCREngine:
    name = "demo_ocr"

    def run(self, image_path: str | Path, page_number: int = 1) -> list[OCRBlockResult]:
        name = Path(str(image_path)).name.lower()
        if "packing" in name:
            texts = ["PACKING LIST", "PO-2026-077", "Atlas Trading Co.", "Nexa Imports Ltd.", "Quantity 480", "Destination Riyadh"]
        elif "payment" in name or "bank" in name:
            texts = ["BANK PAYMENT PROOF", "INV-2026-001", "Total USD 18000", "Transaction TXN-9001"]
        elif "lading" in name or "bol" in name:
            texts = ["BILL OF LADING", "BL-2026-445", "Container MSCU 1234567", "Destination Jeddah"]
        elif "purchase" in name or "po" in name:
            texts = ["PURCHASE ORDER", "PO-2026-077", "Quantity 500", "Total USD 18500"]
        else:
            texts = ["COMMERCIAL INVOICE", "INV-2026-001", "PO-2026-077", "Atlas Trading Co.", "Nexa Imports Ltd.", "Quantity 500", "Total USD 18500", "Destination Jeddah"]
        return [OCRBlockResult(t, 0.64 - i * .01, {"x": 70, "y": 90+i*32, "w": 420, "h": 24}, page_number, "text", self.name, {"mode": "deterministic_demo"}) for i, t in enumerate(texts)]


class OCRRouter:
    def __init__(self):
        self.settings = get_settings()
        self.errors: list[dict[str, str]] = []

    def available_engines(self) -> list[dict[str, Any]]:
        health = inspect_ocr_health()
        return [
            {"name": "PaddleOCR", "enabled": self.settings.enable_paddleocr, "role": "primary", **health["paddleocr"]},
            {"name": "Tesseract", "enabled": self.settings.enable_tesseract, "role": "fallback", **health["tesseract"]},
            {"name": "Docling", "enabled": self.settings.enable_docling, "role": "structured digital PDF parser", **health["docling"]},
            {"name": "LayoutParser", "enabled": self.settings.enable_layoutparser, "role": "optional model layout detector", **health["layoutparser"]},
            {"name": "Demo OCR", "enabled": self.settings.demo_ocr_enabled, "role": "explicit deterministic fallback", **health["demo_mode"]},
        ]

    def _record_error(self, engine: str, exc: Exception) -> None:
        payload = {
            "engine": engine,
            "error_type": type(exc).__name__,
            "error_message": str(exc)[:500],
        }
        self.errors.append(payload)
        logger.warning("ocr_engine_failed", extra=payload)

    def run(self, image_path: str | Path, page_number: int = 1) -> list[OCRBlockResult]:
        paddle_available, _ = _check_import("paddleocr")
        if self.settings.enable_paddleocr and paddle_available:
            try:
                blocks = PaddleOCREngine(self.settings.ocr_lang).run(image_path, page_number)
                if blocks:
                    return blocks
            except Exception as e:
                self._record_error("paddleocr", e)
        if self.settings.enable_tesseract:
            try:
                tess_lang = "eng" if self.settings.ocr_lang == "en" else self.settings.ocr_lang
                blocks = TesseractEngine(tess_lang).run(image_path, page_number)
                if blocks:
                    return blocks
            except Exception as e:
                self._record_error("tesseract", e)
        if self.settings.demo_ocr_enabled:
            logger.info("using_explicit_demo_ocr_fallback")
            return DemoOCREngine().run(image_path, page_number)
        logger.warning("no_real_ocr_available_and_demo_disabled", extra={"image_path": str(image_path), "errors": self.errors})
        return []
