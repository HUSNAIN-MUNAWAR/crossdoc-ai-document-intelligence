from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.domain import CaseCreate
from app.services.case_service import CaseService
from app.services.demo_store import DEMO_CASES, DEMO_DOCUMENTS, DEMO_ISSUES
from app.services.document_processing_service import CaseProcessingService
router=APIRouter(prefix="/api/cases", tags=["cases"])
svc=CaseService()
@router.post("")
def create_case(payload: CaseCreate, db: Session=Depends(get_db)):
    c=svc.create_case(db,payload.case_id,payload.title); return {"case_id":c.case_id,"title":c.title,"status":c.status,"risk_level":c.risk_level,"risk_score":c.risk_score,"average_confidence":c.average_confidence,"document_count":len(c.documents)}
@router.get("")
def list_cases(db: Session=Depends(get_db)):
    rows=[{"case_id":c.case_id,"title":c.title,"status":c.status,"risk_level":c.risk_level,"risk_score":c.risk_score,"average_confidence":c.average_confidence,"document_count":len(c.documents)} for c in svc.list_cases(db)]
    return rows or DEMO_CASES
@router.get("/{case_id}")
def get_case(case_id: str, db: Session=Depends(get_db)):
    c=svc.get_case(db,case_id)
    if c: return {"case_id":c.case_id,"title":c.title,"status":c.status,"risk_level":c.risk_level,"risk_score":c.risk_score,"average_confidence":c.average_confidence,"documents":[{"id":d.id,"filename":d.filename,"document_type":d.document_type,"status":d.status,"quality_score":d.quality_score,"ocr_confidence":d.ocr_confidence} for d in c.documents]}
    demo=next((x for x in DEMO_CASES if x["case_id"]==case_id),None)
    if not demo: raise HTTPException(404,"Case not found")
    return {**demo,"documents":DEMO_DOCUMENTS.get(case_id,[]),"reconciliation_issues":DEMO_ISSUES.get(case_id,[])}
@router.delete("/{case_id}")
def delete_case(case_id: str, db: Session=Depends(get_db)):
    if svc.delete_case(db,case_id): return {"deleted":True}
    raise HTTPException(404,"Case not found")
@router.post("/{case_id}/process")
def process_case(case_id: str, db: Session=Depends(get_db)):
    case=svc.get_case(db,case_id)
    if not case: raise HTTPException(404,"Case not found")
    try:
        return CaseProcessingService().process_case(db,case)
    except ValueError as exc:
        raise HTTPException(400,str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503,str(exc)) from exc
@router.get("/{case_id}/status")
def case_status(case_id: str, db: Session=Depends(get_db)):
    case=svc.get_case(db,case_id)
    if case: return {"case_id":case_id,"status":case.status,"pipeline_stage":"complete" if case.status in {"processed","needs_review"} else case.status,"progress":1 if case.status in {"processed","needs_review"} else 0}
    return {"case_id":case_id,"status":next((x["status"] for x in DEMO_CASES if x["case_id"]==case_id),"queued"),"pipeline_stage":"risk_scoring","progress":.86}
