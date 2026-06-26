from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.domain import Case, ReconciliationIssue, RiskReport
from app.services.document_processing_service import DocumentProcessingService
from app.services.demo_store import DEMO_CASES, DEMO_ISSUES
from app.services.risk_engine import RiskEngine

router=APIRouter(prefix="/api/cases/{case_id}", tags=["risk"])

@router.get("/risk")
def get_risk(case_id: str, db: Session=Depends(get_db)):
    case=db.query(Case).filter(Case.case_id==case_id).first()
    if case:
        report=db.query(RiskReport).filter(RiskReport.case_id_fk==case.id).order_by(RiskReport.id.desc()).first()
        if report:
            return {"score":report.score,"level":report.level,"factors":report.factors,"top_factors":sorted(report.factors,key=lambda factor:factor.get("points",0),reverse=True)[:5],"recommended_actions":report.recommended_actions}
        return {"score":case.risk_score,"level":case.risk_level,"factors":[],"top_factors":[],"recommended_actions":["Process the case to calculate risk."]}
    c=next((x for x in DEMO_CASES if x["case_id"]==case_id),{"risk_score":0,"risk_level":"unknown"})
    issues=DEMO_ISSUES.get(case_id,[])
    return {"score":c["risk_score"],"level":c["risk_level"],"factors":issues,"recommended_actions":["Review high severity mismatches","Correct low-confidence fields"] if issues else ["Spot-check extracted fields"]}

@router.post("/risk/recalculate")
def recalc(case_id: str, db: Session=Depends(get_db)):
    case=db.query(Case).filter(Case.case_id==case_id).first()
    if not case: raise HTTPException(404,"Case not found")
    service=DocumentProcessingService()
    documents=[service.serialize_document(db,document) for document in case.documents if document.status=="processed"]
    issues=[{"type":row.issue_type,"issue_type":row.issue_type,"severity":row.severity,"message":row.message} for row in db.query(ReconciliationIssue).filter(ReconciliationIssue.case_id_fk==case.id).all()]
    risk=RiskEngine().calculate(documents,issues)
    db.query(RiskReport).filter(RiskReport.case_id_fk==case.id).delete(synchronize_session=False)
    db.add(RiskReport(case_id_fk=case.id,score=risk["score"],level=risk["level"],factors=risk["factors"],recommended_actions=risk["recommended_actions"]))
    case.risk_score=risk["score"]; case.risk_level=risk["level"]
    db.commit()
    return risk
