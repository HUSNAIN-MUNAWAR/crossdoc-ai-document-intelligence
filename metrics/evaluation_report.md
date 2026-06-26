# CrossDoc AI Evaluation Report

Synthetic evaluation report generated from local demo cases. Metrics are designed for regression tracking, not for claiming universal OCR performance.

| Metric | Value |
|---|---:|
| Document Classification Accuracy | 1.0 |
| Field Extraction Exact Match | 1.0 |
| Field Extraction Normalized Match | 1.0 |
| Amount Tolerance Match | 0.242 |
| Table Row Count Accuracy | 1.0 |
| Line Item Extraction Score | 0.667 |
| Table Row Reconstruction Score | 1.0 |
| Average Ocr Confidence | 0.83 |
| Review Required Percentage | 0.03 |
| Reconciliation Issue Detection Count | 5 |
| Risk Issue Detection Count | 5 |
| Processing Time Per Document Seconds | 0.0 |
| Ocr Engine Availability Status | {"paddleocr": {"available": false, "version": null, "status": "not_installed"}, "tesseract": {"available": true, "binary_available": true, "pytesseract_available": true, "version": "tesseract 5.5.0", "status": "ready"}, "docling": {"available": false, "version": null, "status": "not_installed"}, "layoutparser": {"available": false, "version": null, "status": "optional_not_installed"}, "poppler": {"available": true, "version": "pdfinfo version 25.06.0", "status": "ready"}, "opencv": {"available": true, "version": "4.13.0", "status": "ready"}, "demo_mode": {"enabled": false, "env_var": "CROSSDOC_DEMO_OCR"}, "language": "en"} |
