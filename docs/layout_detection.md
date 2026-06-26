# Layout Detection

LayoutDetector includes heuristic mode for header, footer, key-value, table, line-items and signature/stamp-like regions. Model mode is an adapter point for local LayoutParser models without downloading weights automatically.

## Practical notes

- The implementation is honest about optional heavy dependencies.
- Demo data is synthetic and generated locally.
- Core modules are tested through backend pytest tests.
