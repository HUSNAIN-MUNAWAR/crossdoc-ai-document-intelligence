from fastapi.testclient import TestClient
from app.main import app
from app.services.ocr_router import OCRBlockResult, OCRRouter, calibrate_confidence

client = TestClient(app)

def test_ocr_health_endpoint_shape():
    data = client.get("/api/system/ocr-health").json()
    assert "paddleocr" in data and "tesseract" in data and "demo_mode" in data
    assert "available" in data["paddleocr"]

def test_ocr_result_schema_and_confidence_range():
    block = OCRBlockResult("Total USD 1,25O", 87, {"x": -1, "y": 2, "w": 10, "h": 5}, 1, engine="tesseract")
    d = block.to_dict()
    assert 0 <= d["confidence"] <= 1
    assert d["bbox"]["x"] == 0
    assert d["engine"] == "tesseract"
    assert d["engine_name"] == "tesseract"

def test_confidence_calibration():
    assert calibrate_confidence(95, "tesseract") == .95
    assert calibrate_confidence(1.2, "paddleocr") == 1.0
    assert calibrate_confidence(.9, "demo_ocr") <= .68

def test_demo_mode_disabled_does_not_fake(monkeypatch, tmp_path):
    router = OCRRouter()
    monkeypatch.setattr(router.settings, "enable_paddleocr", False)
    monkeypatch.setattr(router.settings, "enable_tesseract", False)
    monkeypatch.setattr(router.settings, "crossdoc_demo_ocr", False)
    monkeypatch.setattr(router.settings, "crossdoc_demo_mode", False)
    assert router.run(tmp_path / "missing.png") == []


def test_engine_failure_is_recorded_without_breaking_fallback():
    router = OCRRouter()
    router._record_error("optional_engine", ModuleNotFoundError("not installed"))
    assert router.errors == [{
        "engine": "optional_engine",
        "error_type": "ModuleNotFoundError",
        "error_message": "not installed",
    }]
