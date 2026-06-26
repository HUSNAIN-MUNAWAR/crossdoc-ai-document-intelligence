from fastapi import APIRouter, Response
from app.services.demo_store import DEMO_CASES, DEMO_DOCUMENTS, DEMO_FIELDS, DEMO_ISSUES
from app.services.export_service import ExportService
router=APIRouter(prefix="/api/cases/{case_id}/export", tags=["exports"]); svc=ExportService()
def payload(case_id):
    c=next((x for x in DEMO_CASES if x["case_id"]==case_id),{"case_id":case_id})
    docs=[{**d,"fields":DEMO_FIELDS.get(d["id"],{}),"tables":[]} for d in DEMO_DOCUMENTS.get(case_id,[])]
    return {**c,"documents":docs,"reconciliation_issues":DEMO_ISSUES.get(case_id,[])}
@router.get("/json")
def export_json(case_id:str): return payload(case_id)
@router.get("/csv")
def export_csv(case_id:str): return Response(svc.fields_csv(payload(case_id)["documents"]), media_type="text/csv")
@router.get("/excel")
def export_excel(case_id:str): return Response(svc.line_items_excel(payload(case_id)["documents"]), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
@router.get("/report")
def export_report(case_id:str):
    p=payload(case_id); text=f"# Risk and Reconciliation Report - {case_id}\n\nRisk: {p.get('risk_level')} ({p.get('risk_score')})\n\n" + "\n".join(f"- **{i['severity']}** {i['message']}" for i in p.get("reconciliation_issues",[]))
    return Response(text, media_type="text/markdown")
