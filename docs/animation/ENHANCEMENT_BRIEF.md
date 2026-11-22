# CrossDoc reconciliation animation enhancement

## Purpose

Show the product’s differentiator: related invoice, logistics, and payment documents are evaluated as one case, with normalized evidence, explainable mismatches, risk, and human review.

## Model and service boundary

The generator executes the repository’s real post-OCR services:

- `DocumentClassifier` assigns document types.
- `ExtractionEngine` applies field patterns, normalization, confidence, and table reconstruction.
- `LayoutDetector` creates explainable heuristic regions.
- `ReconciliationEngine` compares quantities, amounts, references, currencies, destinations, and duplicates.
- `RiskEngine` weights findings and returns a recommended action.

The laptop session does not have a Tesseract binary, so this generator supplies deterministic synthetic OCR evidence blocks after the OCR boundary. The manifest records that limitation and points to `scripts/validate_real_ocr.py` for the binary-backed smoke test. The animation is therefore a faithful post-OCR pipeline reference, not an OCR accuracy benchmark.

## Reproduce

```bash
python scripts/generate_reconciliation_animation.py
```

Outputs:

- `docs/animation/crossdoc_reconciliation_sequence.json` — source checksum, service/model references, extracted document summary, issues, risk, and scene events.
- `frontend/public/animation/crossdoc-reconciliation-reel.html` — dependency-free animation with pause, replay, and stage selection.
