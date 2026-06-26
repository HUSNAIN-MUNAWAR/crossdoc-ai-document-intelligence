Write-Host "[CrossDoc AI] Installing Python OCR bindings. Heavy OCR packages are optional."
python -m pip install --upgrade pip
python -m pip install pytesseract pdf2image opencv-python-headless pillow
Write-Host ""
Write-Host "Optional heavy engines:"
Write-Host "  python -m pip install paddleocr paddlepaddle"
Write-Host "  python -m pip install docling"
Write-Host "  python -m pip install layoutparser"
Write-Host ""
Write-Host "Windows system dependencies:"
Write-Host "  Install Tesseract OCR from UB Mannheim builds and add tesseract.exe to PATH."
Write-Host "  Install Poppler for Windows and add bin folder to PATH."
Write-Host ""
Write-Host "Verify with: python scripts/check_ocr_engines.py"
