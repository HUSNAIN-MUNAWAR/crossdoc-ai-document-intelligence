from app.services.docling_adapter import DoclingAdapter
from app.services.layout_detector import LayoutDetector, VALID_LABELS
from app.services.ocr_router import OCRBlockResult
from app.services.table_extractor import TableExtractor


def test_docling_unavailable_or_available_graceful(tmp_path):
    pdf = tmp_path / "sample.pdf"; pdf.write_bytes(b"%PDF-1.4\n%%EOF")
    result = DoclingAdapter().parse_pdf(pdf).to_dict()
    assert result["status"] in {"not_installed", "parsed", "parse_failed"}
    assert "text_blocks" in result and "tables" in result


def test_layout_heuristic_regions_valid():
    blocks = [OCRBlockResult("Invoice Number INV-001", .9, {"x":50,"y":50,"w":200,"h":20}, 1), OCRBlockResult("SKU Qty Total", .9, {"x":50,"y":500,"w":300,"h":20}, 1)]
    regions = LayoutDetector().detect(ocr_blocks=blocks, image_size=(1000, 1400))
    assert regions
    assert all(r.label in VALID_LABELS for r in regions)
    assert all(r.bbox["w"] >= 0 and r.bbox["h"] >= 0 for r in regions)


def test_layout_empty_document_does_not_crash():
    regions = LayoutDetector().detect(ocr_blocks=[], image_size=(1000, 1400))
    assert regions[0].label == "header"


def test_table_grouping_and_repair():
    blocks = [
        OCRBlockResult("SKU", .9, {"x":50,"y":100,"w":30,"h":10}, 1), OCRBlockResult("Qty", .9, {"x":250,"y":100,"w":30,"h":10}, 1), OCRBlockResult("Total", .9, {"x":350,"y":100,"w":50,"h":10}, 1),
        OCRBlockResult("BG-100", .9, {"x":50,"y":130,"w":70,"h":10}, 1), OCRBlockResult("500", .9, {"x":250,"y":132,"w":30,"h":10}, 1), OCRBlockResult("USD", .9, {"x":350,"y":132,"w":30,"h":10}, 1), OCRBlockResult("18,500", .9, {"x":390,"y":132,"w":60,"h":10}, 1),
    ]
    table = TableExtractor().reconstruct(blocks)[0]
    assert table["header_row_index"] == 0
    assert any("USD 18,500" in cell for row in table["rows"] for cell in row["cells"])


def test_empty_ocr_blocks_table():
    assert TableExtractor().reconstruct([]) == []
