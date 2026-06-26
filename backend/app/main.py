from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import cases, documents, evaluation, exports, reconciliation, review, risk, system
from app.core.config import get_settings
from app.db.session import init_db

settings = get_settings()
init_db()

app = FastAPI(
    title="CrossDoc AI API",
    version="1.0.0",
    description=(
        "Multi-document OCR, structured extraction, reconciliation, "
        "risk scoring, and human review API."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in [
    system.router,
    cases.router,
    documents.router,
    reconciliation.router,
    risk.router,
    review.router,
    exports.router,
    evaluation.router,
]:
    app.include_router(router)
