from app.services.risk_engine import RiskEngine
def test_risk_score_calculation():
    report=RiskEngine().calculate([{"document_type":"commercial_invoice","fields":{"invoice_number":{"confidence":.6}},"quality_score":.4}],[{"type":"quantity_mismatch","severity":"high","message":"Mismatch"}])
    assert report["score"]>25 and report["level"] in {"medium","high","critical"}
