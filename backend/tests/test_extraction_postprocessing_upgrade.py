from pathlib import Path
from app.services.extraction_engine import ExtractionEngine
from app.services.ocr_router import OCRBlockResult
from app.services.postprocessor import PostProcessor


def test_extraction_templates_exist_for_document_types():
    base = Path("app/extraction_templates")
    for name in ["commercial_invoice", "packing_list", "bill_of_lading", "purchase_order", "payment_proof", "delivery_note", "receipt"]:
        assert (base / f"{name}.yaml").exists()


def test_extract_commercial_invoice_fields():
    blocks = [OCRBlockResult("Invoice Number: lNV-2O26-O017", .86, {"x":1,"y":1,"w":10,"h":10}, 1), OCRBlockResult("Supplier: Atlas Trading Co.", .9, {"x":1,"y":30,"w":10,"h":10}, 1), OCRBlockResult("Buyer: Nexa Imports Ltd.", .9, {"x":1,"y":60,"w":10,"h":10}, 1), OCRBlockResult("Total Amount USD 18,500", .88, {"x":1,"y":90,"w":10,"h":10}, 1)]
    out = ExtractionEngine().extract("commercial_invoice", blocks)
    assert out["fields"]["invoice_number"]["normalized_value"] == "INV-2026-0017"
    assert out["fields"]["total_amount"]["normalized_value"] == 18500


def test_invoice_title_does_not_capture_following_label():
    blocks = [
        OCRBlockResult("COMMERCIAL", .91, {"x": 1, "y": 1, "w": 10, "h": 10}, 1),
        OCRBlockResult("INVOICE", .92, {"x": 20, "y": 1, "w": 10, "h": 10}, 1),
        OCRBlockResult("Invoice", .94, {"x": 1, "y": 40, "w": 10, "h": 10}, 1),
        OCRBlockResult("Number:", .94, {"x": 20, "y": 40, "w": 10, "h": 10}, 1),
        OCRBlockResult("INV.2026.001", .89, {"x": 50, "y": 40, "w": 10, "h": 10}, 1),
        OCRBlockResult("Supplier:", .93, {"x": 1, "y": 80, "w": 10, "h": 10}, 1),
        OCRBlockResult("Atlas", .91, {"x": 50, "y": 80, "w": 10, "h": 10}, 1),
        OCRBlockResult("Trading", .90, {"x": 80, "y": 80, "w": 10, "h": 10}, 1),
        OCRBlockResult("Co.", .88, {"x": 120, "y": 80, "w": 10, "h": 10}, 1),
    ]
    out = ExtractionEngine().extract("commercial_invoice", blocks)
    assert out["fields"]["invoice_number"]["normalized_value"] == "INV-2026-001"
    assert out["fields"]["supplier_name"]["normalized_value"] == "Atlas Trading"


def test_company_fuzzy_matching_and_word_preservation():
    p = PostProcessor()
    assert p.company_match_score("Atlas Trading Co.", "Atlas Trading Company Limited") > .9
    assert p.repair_text_preserving_words("BOLT supplier") == "BOLT supplier"
