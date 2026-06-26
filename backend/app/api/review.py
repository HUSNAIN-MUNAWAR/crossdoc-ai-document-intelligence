from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.domain import Case, ExtractedField, ReviewCorrection, ReviewTask
from app.schemas.domain import ReviewUpdate

router=APIRouter(prefix="/api/review", tags=["review"])
TASKS=[{"id":1,"case_id":"SHIP-2026-001","document_id":2,"field_name":"quantity","original_value":"48O","suggested_value":"480","confidence":.71,"reason":"Low OCR confidence and quantity mismatch.","status":"open"},{"id":2,"case_id":"SHIP-2026-001","document_id":2,"field_name":"destination","original_value":"Riyadh","suggested_value":"Riyadh","confidence":.73,"reason":"Destination mismatch.","status":"open"},{"id":3,"case_id":"FIN-2026-003","document_id":9,"field_name":"total_amount","original_value":"PKR 1,20O,OOO","suggested_value":"1200000","confidence":.74,"reason":"Payment amount mismatch.","status":"open"}]

def _serialize(task: ReviewTask):
    return {"id":task.id,"case_id":task.case_id_fk,"document_id":task.document_id,"field_name":task.field_name,"original_value":task.original_value,"suggested_value":task.suggested_value,"confidence":task.confidence,"reason":task.reason,"status":task.status}

@router.get("/tasks")
def list_tasks(db: Session=Depends(get_db)):
    tasks=db.query(ReviewTask).order_by(ReviewTask.id.desc()).all()
    if tasks:
        return [_serialize(task) for task in tasks]
    return [] if db.query(Case).count() else TASKS

@router.get("/tasks/{task_id}")
def get_task(task_id:int, db: Session=Depends(get_db)):
    row=db.get(ReviewTask,task_id)
    if row: return _serialize(row)
    t=next((x for x in TASKS if x["id"]==task_id),None)
    if not t: raise HTTPException(404,"Review task not found")
    return t

@router.patch("/tasks/{task_id}")
def update_task(task_id:int, payload: ReviewUpdate, db: Session=Depends(get_db)):
    task=db.get(ReviewTask,task_id)
    if task:
        corrected=payload.corrected_value if payload.corrected_value is not None else task.suggested_value
        db.add(ReviewCorrection(task_id=task.id,original_value=task.original_value,corrected_value=corrected,reviewer_note=payload.reviewer_note or ""))
        field=db.query(ExtractedField).filter(ExtractedField.document_id==task.document_id,ExtractedField.field_name==task.field_name).first()
        if field:
            import json
            field.normalized_value=json.dumps(corrected,ensure_ascii=True)
            field.confidence=max(field.confidence,.95)
        task.suggested_value=corrected
        task.status=payload.status
        db.commit(); db.refresh(task)
        return {**_serialize(task),"corrected_value":corrected,"reviewer_note":payload.reviewer_note}
    t=next((x for x in TASKS if x["id"]==task_id),None)
    if not t: raise HTTPException(404,"Review task not found")
    t.update({"corrected_value":payload.corrected_value,"reviewer_note":payload.reviewer_note,"status":payload.status}); return t

@router.post("/tasks/{task_id}/approve")
def approve(task_id:int, db: Session=Depends(get_db)):
    task=db.get(ReviewTask,task_id)
    if task:
        task.status="approved"; db.commit(); db.refresh(task); return _serialize(task)
    t=next((x for x in TASKS if x["id"]==task_id),None)
    if not t: raise HTTPException(404,"Review task not found")
    t["status"]="approved"; return t
