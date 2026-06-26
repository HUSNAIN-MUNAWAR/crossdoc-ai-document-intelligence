# Docling Integration

DoclingAdapter provides a graceful optional integration for digital PDFs. When installed, it attempts a structured parse and normalizes text blocks and tables. When missing, the API returns not_installed instead of crashing.

## Practical notes

- The implementation is honest about optional heavy dependencies.
- Demo data is synthetic and generated locally.
- Core modules are tested through backend pytest tests.
