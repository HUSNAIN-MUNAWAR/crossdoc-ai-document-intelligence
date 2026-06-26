# Ocr Engines

CrossDoc AI uses an open-source OCR strategy: PaddleOCR as the preferred engine, Tesseract as fallback, and deterministic Demo OCR only when CROSSDOC_DEMO_OCR=true. Use scripts/check_ocr_engines.py to verify PaddleOCR, pytesseract, tesseract binary, Docling, LayoutParser, Poppler and OpenCV.

## Practical notes

- The implementation is honest about optional heavy dependencies.
- Demo data is synthetic and generated locally.
- Core modules are tested through backend pytest tests.
