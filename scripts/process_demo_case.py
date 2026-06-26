from pathlib import Path
import json, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.reconciliation_engine import ReconciliationEngine
from app.services.risk_engine import RiskEngine
docs=[{"document_type":"commercial_invoice","fields":{"invoice_number":{"normalized_value":"INV-2026-001","confidence":.86},"supplier_name":{"normalized_value":"Atlas Trading Co.","confidence":.88},"buyer_name":{"normalized_value":"Nexa Imports Ltd.","confidence":.87},"quantity":{"normalized_value":500,"confidence":.82},"destination":{"normalized_value":"Jeddah","confidence":.78},"total_amount":{"normalized_value":18500,"confidence":.83}},"quality_score":.82},{"document_type":"packing_list","fields":{"quantity":{"normalized_value":480,"confidence":.73},"destination":{"normalized_value":"Riyadh","confidence":.72}},"quality_score":.75}]
issues=[i.to_dict() for i in ReconciliationEngine().reconcile(docs)]
out={"case_id":"SHIP-2026-001","documents":docs,"reconciliation_issues":issues,"risk":RiskEngine().calculate(docs,issues)}
Path("exports").mkdir(exist_ok=True); Path("exports/demo_case_output.json").write_text(json.dumps(out,indent=2)); print("Wrote exports/demo_case_output.json")
