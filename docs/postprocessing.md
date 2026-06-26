# Postprocessing

The post-processing layer repairs OCR confusions in numeric context, normalizes invoice/PO/container/date/currency/amount/quantity fields, validates HS code length, and performs fuzzy company matching.

## Practical notes

- The implementation is honest about optional heavy dependencies.
- Demo data is synthetic and generated locally.
- Core modules are tested through backend pytest tests.
