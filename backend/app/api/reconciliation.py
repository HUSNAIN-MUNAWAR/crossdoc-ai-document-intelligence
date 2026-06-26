from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.domain import Case, ReconciliationIssue
from app.services.document_processing_service import DocumentProcessingService
from app.services.demo_store import DEMO_ISSUES
from app.services.reconciliation_engine import ReconciliationEngine

router=APIRouter(prefix="/api/cases/{case_id}", tags=["reconciliation"])

def _serialize(row: ReconciliationIssue):
    return {"issue_type":row.issue_type,"type":row.issue_type,"severity":row.severity,"message":row.message,"source_documents":row.source_documents,"recommended_action":row.recommended_action,"resolved":row.resolved}

@router.get("/reconciliation")
def get_reconciliation(case_id: str, db: Session=Depends(get_db)):
    case=db.query(Case).filter(Case.case_id==case_id).first()
    if case:
        return [_serialize(row) for row in db.query(ReconciliationIssue).filter(ReconciliationIssue.case_id_fk==case.id).all()]
    return DEMO_ISSUES.get(case_id,[])

@router.post("/reconcile")
def reconcile(case_id: str, db: Session=Depends(get_db)):
    case=db.query(Case).filter(Case.case_id==case_id).first()
    if not case: raise HTTPException(404,"Case not found")
    service=DocumentProcessingService()
    documents=[service.serialize_document(db,document) for document in case.documents if document.status=="processed"]
    issues=[issue.to_dict() for issue in ReconciliationEngine().reconcile(documents)]
    db.query(ReconciliationIssue).filter(ReconciliationIssue.case_id_fk==case.id).delete(synchronize_session=False)
    for issue in issues:
        db.add(ReconciliationIssue(case_id_fk=case.id,issue_type=issue["issue_type"],severity=issue["severity"],message=issue["message"],source_documents=issue["source_documents"],recommended_action=issue["recommended_action"]))
    db.commit()
    return {"case_id":case_id,"issues":issues,"status":"completed"}
