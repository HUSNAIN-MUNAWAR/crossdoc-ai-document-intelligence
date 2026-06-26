# Evaluation

Evaluation uses synthetic ground truth to compute classification accuracy, exact/normalized field matches, amount tolerance match, table row accuracy, line-item score, review percentage, issue count and OCR engine availability.

## Practical notes

- The implementation is honest about optional heavy dependencies.
- Demo data is synthetic and generated locally.
- Core modules are tested through backend pytest tests.
