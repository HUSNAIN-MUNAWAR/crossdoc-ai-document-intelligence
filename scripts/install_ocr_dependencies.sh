#!/usr/bin/env bash
set -euo pipefail

echo "[CrossDoc AI] Installing Python OCR bindings. Heavy OCR packages are optional."
python -m pip install --upgrade pip
python -m pip install pytesseract pdf2image opencv-python-headless pillow

echo ""
echo "Optional heavy engines:"
echo "  python -m pip install paddleocr paddlepaddle"
echo "  python -m pip install docling"
echo "  python -m pip install layoutparser"
echo ""
echo "Linux system packages usually needed:"
echo "  sudo apt-get update && sudo apt-get install -y tesseract-ocr poppler-utils"
echo ""
echo "Verify with: python scripts/check_ocr_engines.py"
