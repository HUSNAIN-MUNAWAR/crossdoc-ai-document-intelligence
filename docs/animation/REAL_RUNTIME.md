# CrossDoc real OCR runtime evidence

This runtime evidence executes the real OCR and post-OCR services over the six
committed clean PNGs for `SHIP-2026-001`. It is separate from the older HTML
animation, whose generator deliberately supplies synthetic OCR blocks.

## Reproduce

```powershell
py -3.12 -u scripts/generate_real_runtime_video.py
```

The runner executes:

- `PreprocessingService` on each clean input image;
- `OCRRouter` with real Tesseract and demo OCR disabled;
- `DocumentClassifier` and `ExtractionEngine`;
- `LayoutDetector`, `ReconciliationEngine`, and `RiskEngine`.

It holds eight data-driven pipeline events for five frames each so the actual
run is watchable. The CSV contains each OCR block, confidence, engine, page,
and bounding box. The JSON contains source hashes, Tesseract and `eng.traineddata`
identity, every document's extracted fields and mismatches, reconciliation
issues, risk, runtime details, and output hashes.

## Captured result

| Measure | Result |
| --- | ---: |
| Documents | 6 |
| Tesseract OCR blocks | 209 |
| Reconciliation issues | 6 |
| Risk score | 100 / critical |
| Ground-truth field mismatches | 31 |
| Demo OCR used | No |

The mismatches are preserved. They are not rounded up into an accuracy claim.
The original PDF validator still fails on the generated PDF fixture because its
rasterized page does not expose the expected text to OCR; the clean PNG runtime
is the real local OCR path used for this evidence.
