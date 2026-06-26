from app.services.postprocessor import PostProcessor
def test_invoice_number_repair(): assert PostProcessor().normalize_invoice_number("lNV-2O26-O017") == "INV-2026-0017"
def test_amount_normalization(): assert PostProcessor().normalize_amount("PKR 1,25O,OOO") == 1250000
def test_date_normalization(): assert PostProcessor().normalize_date("2O26-O6-27") == "2026-06-27"
def test_container_normalization_warning():
    r=PostProcessor().normalize_container_number("MSCU l234567")
    assert r["value"]=="MSCU1234567"
    assert r["warning"] in {"checksum_not_implemented","invalid_container_format"}
