from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_health(): assert client.get("/health").json()["status"]=="ok"
def test_list_cases(): assert isinstance(client.get("/api/cases").json(), list)
def test_export_json(): assert client.get("/api/cases/SHIP-2026-001/export/json").json()["case_id"]=="SHIP-2026-001"
