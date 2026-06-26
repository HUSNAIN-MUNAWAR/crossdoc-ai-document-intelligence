from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.db.session import init_db, SessionLocal
from app.services.case_service import CaseService
from app.services.demo_store import DEMO_CASES
init_db(); db=SessionLocal(); svc=CaseService()
try:
    for r in DEMO_CASES:
        c=svc.create_case(db,r["case_id"],r["title"]); c.status=r["status"]; c.risk_level=r["risk_level"]; c.risk_score=r["risk_score"]; c.average_confidence=r["average_confidence"]
    db.commit(); print("Seeded demo cases")
finally: db.close()
