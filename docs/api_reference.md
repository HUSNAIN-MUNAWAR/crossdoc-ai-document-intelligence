# API Reference

FastAPI publishes interactive OpenAPI documentation at `http://localhost:8000/docs`.

## Cases

| Method | Route | Behavior |
|---|---|---|
| `POST` | `/api/cases` | Create or return a case by business ID |
| `GET` | `/api/cases` | List persisted cases, with sample fallback for an empty database |
| `GET` | `/api/cases/{case_id}` | Read case metadata and documents |
| `DELETE` | `/api/cases/{case_id}` | Delete a case and related document records |
| `POST` | `/api/cases/{case_id}/process` | Run the full local processing pipeline |
| `GET` | `/api/cases/{case_id}/status` | Read lifecycle status and progress |

## Documents

| Method | Route | Behavior |
|---|---|---|
| `POST` | `/api/cases/{case_id}/documents` | Upload supported PDFs/images |
| `GET` | `/api/cases/{case_id}/documents` | List documents for a case |
| `GET` | `/api/documents/{document_id}` | Read document summary, fields, and tables |
| `GET` | `/api/documents/{document_id}/ocr` | Read persisted OCR blocks |
| `GET` | `/api/documents/{document_id}/fields` | Read normalized extracted fields |
| `GET` | `/api/documents/{document_id}/tables` | Read reconstructed tables |
| `GET` | `/api/documents/{document_id}/docling-parse` | Run the optional Docling adapter |
| `POST` | `/api/documents/{document_id}/reprocess` | Clear and rebuild processing results |

## Decisions

| Method | Route | Behavior |
|---|---|---|
| `GET` | `/api/cases/{case_id}/reconciliation` | Read persisted issues |
| `POST` | `/api/cases/{case_id}/reconcile` | Re-run reconciliation from saved fields |
| `GET` | `/api/cases/{case_id}/risk` | Read the latest risk report |
| `POST` | `/api/cases/{case_id}/risk/recalculate` | Recalculate and persist risk |
| `GET` | `/api/review/tasks` | List persisted review tasks |
| `GET` | `/api/review/tasks/{task_id}` | Read a review task |
| `PATCH` | `/api/review/tasks/{task_id}` | Save a correction and audit record |
| `POST` | `/api/review/tasks/{task_id}/approve` | Approve a task |

## Operations

| Method | Route | Behavior |
|---|---|---|
| `GET` | `/health` | Service liveness |
| `GET` | `/api/system/ocr-health` | Runtime engine discovery |
| `GET` | `/api/system/ocr-engines` | Configured engine roles |
| `GET` | `/api/system/settings` | Non-secret runtime settings |

## Example

```bash
curl -X POST http://localhost:8000/api/cases \
  -H "Content-Type: application/json" \
  -d '{"case_id":"CASE-001","title":"Shipment review"}'

curl -X POST http://localhost:8000/api/cases/CASE-001/documents \
  -F "files=@sample_data/generated_cases/SHIP-2026-001/commercial_invoice.pdf"

curl -X POST http://localhost:8000/api/cases/CASE-001/process
curl http://localhost:8000/api/cases/CASE-001/risk
```

## Error Behavior

- Unsupported file types return HTTP 400.
- Missing cases/documents return HTTP 404.
- A case without uploaded documents returns HTTP 400 when processing is requested.
- Missing real OCR engines return HTTP 503 unless explicit demo OCR is enabled.
