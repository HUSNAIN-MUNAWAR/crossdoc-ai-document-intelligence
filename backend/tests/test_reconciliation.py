from app.services.reconciliation_engine import ReconciliationEngine
def test_quantity_mismatch():
    docs=[{"document_type":"commercial_invoice","fields":{"quantity":{"normalized_value":500}}},{"document_type":"packing_list","fields":{"quantity":{"normalized_value":480}}}]
    assert any(i.type=="quantity_mismatch" for i in ReconciliationEngine().reconcile(docs))
