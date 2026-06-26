# Validation Report

Validation date: June 27, 2026

## Automated Checks

| Check | Result |
|---|---|
| Backend compile | Passed |
| Backend pytest suite | 27 passed |
| Real OCR smoke test | Passed |
| OCR engine used | Tesseract 5.4.0 |
| PDF pages processed | 1 |
| OCR blocks persisted | 65 |
| Average OCR confidence | 0.953 |
| Validated fields | `INV-2026-001`, `PO-2026-077`, `18500` |
| Frontend dependency audit | 0 vulnerabilities |
| Frontend production build | Passed, 21 routes |
| Real Playwright screenshots | Passed, 5 captures |
| Responsive screenshot check | Passed at 390 x 844 |
| Docker Compose validation | Not run; Docker CLI is unavailable in this environment |

## Commands

```bash
cd backend
python -m compileall app
pytest -q

cd ..
python scripts/validate_real_ocr.py

cd frontend
npm ci
npm run build
npm run screenshots
```

## OCR Health Snapshot

```json
{
  "paddleocr": {"available": false, "status": "not_installed"},
  "tesseract": {
    "available": true,
    "version": "tesseract v5.4.0.20240606",
    "status": "ready"
  },
  "docling": {"available": false, "status": "not_installed"},
  "layoutparser": {"available": false, "status": "optional_not_installed"},
  "poppler": {"available": true, "status": "ready"},
  "opencv": {"available": true, "version": "4.10.0", "status": "ready"},
  "demo_mode": {"enabled": false}
}
```

PaddleOCR, Docling, and LayoutParser are optional adapters and were not installed for
this validation. The smoke test fails if it receives no OCR blocks or if demo OCR is
used.

## Evidence

- Real inspector capture: [`screenshots/03_document_inspector.png`](screenshots/03_document_inspector.png)
- Regression evaluation: [`../metrics/evaluation_report.md`](../metrics/evaluation_report.md)
- OCR smoke script: [`../scripts/validate_real_ocr.py`](../scripts/validate_real_ocr.py)

## Environment Note

Dockerfiles and Compose configuration were reviewed, but the Docker CLI is not
installed in the validation environment. Container build and Compose startup remain
CI/deployment checks.
