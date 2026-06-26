from app.services.reconciliation_engine import ReconciliationEngine
from app.services.risk_engine import RiskEngine


def fld(v, c=.9): return {"normalized_value": v, "confidence": c}


def test_amount_destination_supplier_and_date_issues():
    docs = [
        {"document_type":"commercial_invoice","fields":{"invoice_number":fld("INV-1"),"supplier_name":fld("Atlas Trading"),"buyer_name":fld("Nexa"),"destination":fld("Jeddah"),"total_amount":fld(100),"currency":fld("USD"),"invoice_date":fld("2026-06-28")}},
        {"document_type":"purchase_order","fields":{"po_number":fld("PO-1"),"supplier_name":fld("Different Supplier"),"total_amount":fld(120),"currency":fld("USD")}},
        {"document_type":"bill_of_lading","fields":{"destination":fld("Riyadh"),"shipment_date":fld("2026-06-27"),"container_number":fld("MSCU1234567")}},
    ]
    issues = ReconciliationEngine().reconcile(docs)
    types = {i.type for i in issues}
    assert "amount_mismatch" in types
    assert "destination_mismatch" in types
    assert "supplier_name_mismatch" in types
    assert "date_sequence_issue" in types


def test_risk_levels_and_explanation():
    low = RiskEngine().calculate([{"document_type":"commercial_invoice","fields":{"invoice_number":fld("INV"),"supplier_name":fld("A"),"buyer_name":fld("B"),"total_amount":fld(1)},"quality_score":.9}], [])
    assert low["level"] == "low"
    high = RiskEngine().calculate([{"document_type":"commercial_invoice","fields":{"invoice_number":fld("INV", .5)},"quality_score":.4}], [{"type":"amount_mismatch","severity":"high","message":"x"}, {"type":"quantity_mismatch","severity":"high","message":"y"}])
    assert high["level"] in {"high", "critical"}
    assert high["top_factors"] and high["explanation"]
    critical = RiskEngine().calculate([{"document_type":"commercial_invoice","fields":{},"quality_score":.2}], [{"type":"amount_mismatch"},{"type":"quantity_mismatch"},{"type":"destination_mismatch"},{"type":"currency_mismatch"}], review_tasks=[1,2,3,4,5])
    assert critical["level"] == "critical"
