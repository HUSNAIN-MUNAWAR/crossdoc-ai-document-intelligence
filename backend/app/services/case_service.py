from app.models.domain import Case
class CaseService:
    def create_case(self, db, case_id, title):
        c=db.query(Case).filter(Case.case_id==case_id).first()
        if c: return c
        c=Case(case_id=case_id,title=title,status="created"); db.add(c); db.commit(); db.refresh(c); return c
    def list_cases(self, db): return db.query(Case).order_by(Case.created_at.desc()).all()
    def get_case(self, db, case_id): return db.query(Case).filter(Case.case_id==case_id).first()
    def delete_case(self, db, case_id):
        c=self.get_case(db,case_id)
        if not c: return False
        db.delete(c); db.commit(); return True
