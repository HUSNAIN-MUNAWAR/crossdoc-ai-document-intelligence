from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DoclingParseResult:
    available: bool
    status: str
    document_path: str
    text_blocks: list[dict[str, Any]] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DoclingAdapter:
    """Small practical adapter around Docling.

    The adapter is intentionally defensive: Docling changes APIs over time, and this
    project should fail gracefully when the optional package is not installed.
    """

    def is_available(self) -> bool:
        try:
            import docling  # noqa: F401
            return True
        except Exception:
            return False

    def parse_pdf(self, path: str | Path) -> DoclingParseResult:
        pdf_path = Path(path)
        if not self.is_available():
            return DoclingParseResult(False, "not_installed", str(pdf_path), error="Docling is optional. Install it with `pip install docling`.")
        try:
            from docling.document_converter import DocumentConverter
            converter = DocumentConverter()
            converted = converter.convert(str(pdf_path))
            document = getattr(converted, "document", converted)
            text = ""
            if hasattr(document, "export_to_markdown"):
                text = document.export_to_markdown()
            elif hasattr(document, "export_to_text"):
                text = document.export_to_text()
            else:
                text = str(document)
            blocks = []
            for i, line in enumerate([x.strip() for x in text.splitlines() if x.strip()]):
                blocks.append({"text": line, "page_number": 1, "bbox": {}, "confidence": None, "source": "docling", "block_id": f"docling-{i}"})
            # Docling table APIs vary; this keeps a stable normalized output even if none are found.
            tables = []
            for i, table in enumerate(getattr(document, "tables", []) or []):
                tables.append({"table_id": f"docling-table-{i}", "rows": getattr(table, "data", []) or [], "source": "docling"})
            return DoclingParseResult(True, "parsed", str(pdf_path), blocks, tables, {"block_count": len(blocks), "table_count": len(tables)})
        except Exception as exc:
            return DoclingParseResult(True, "parse_failed", str(pdf_path), error=f"{type(exc).__name__}: {exc}")

    def parse_document(self, path: str | Path) -> DoclingParseResult:
        p = Path(path)
        if p.suffix.lower() != ".pdf":
            return DoclingParseResult(self.is_available(), "unsupported_file_type", str(p), error="Docling adapter is used for digital PDFs in this project.")
        return self.parse_pdf(p)
