from app.db.session import SessionLocal
from app.models.domain import Case
from app.services.document_processing_service import CaseProcessingService
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.process_case")
def process_case(case_id: str):
    with SessionLocal() as db:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if case is None:
            return {"case_id": case_id, "status": "not_found"}
        return CaseProcessingService().process_case(db, case)
