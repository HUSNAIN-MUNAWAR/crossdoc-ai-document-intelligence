# Architecture

CrossDoc AI separates interaction, orchestration, document processing, decision
logic, and persistence so each part can be tested and replaced independently.

## Component View

```mermaid
flowchart TB
    subgraph Client["Client layer"]
        UI[Next.js operations UI]
        SDK[HTTP clients and OpenAPI]
    end

    subgraph API["FastAPI boundary"]
        Cases[Cases and uploads]
        Documents[Document results]
        Decisions[Reconciliation, risk, review]
        Operations[Health, evaluation, exports]
    end

    subgraph Pipeline["Document intelligence"]
        Loader[PDF and image loader]
        Preprocess[OpenCV preprocessing]
        OCR[OCR router]
        Classify[Document classifier]
        Layout[Layout regions]
        Fields[Field extraction and normalization]
        Tables[Table reconstruction]
    end

    subgraph Rules["Decision support"]
        Reconciliation[Cross-document rules]
        Risk[Weighted explainable risk]
        Human[Human review and corrections]
    end

    subgraph Data["Data plane"]
        DB[(PostgreSQL or SQLite)]
        Objects[(Local storage or MinIO)]
        Queue[(Redis)]
    end

    UI --> Cases
    UI --> Documents
    UI --> Decisions
    SDK --> API
    Cases --> Objects
    Cases --> DB
    Documents --> DB
    Cases --> Loader
    Loader --> Preprocess --> OCR --> Classify
    Classify --> Layout
    Layout --> Fields
    Layout --> Tables
    Fields --> DB
    Tables --> DB
    Fields --> Reconciliation --> Risk --> Human
    Reconciliation --> DB
    Risk --> DB
    Human --> DB
    API -. asynchronous deployment path .-> Queue
    Queue -. Celery tasks .-> Pipeline
```

## Deployment View

```mermaid
flowchart LR
    Browser[Browser] -->|3000| Frontend[Next.js container]
    Frontend -->|8000 HTTP| Backend[FastAPI container]
    Backend --> Postgres[(PostgreSQL 16)]
    Backend --> Redis[(Redis 7)]
    Backend --> MinIO[(MinIO)]
    Worker[Celery worker] --> Redis
    Worker --> Postgres
    Worker --> MinIO
    Flower[Flower monitor] --> Redis
```

The local API currently executes the pipeline synchronously so a clone works without
a running queue. Celery and Redis remain the scaling boundary for moving expensive
case processing out of request/response handling.

## Processing State

```mermaid
stateDiagram-v2
    [*] --> Created
    Created --> Uploaded: files accepted
    Uploaded --> Processing: process requested
    Processing --> Processed: OCR and decisions saved
    Processing --> Failed: no usable OCR or processing error
    Processed --> NeedsReview: risk or confidence threshold
    NeedsReview --> Processed: corrections accepted
    Processed --> Reprocessing: document reprocess requested
    Reprocessing --> Processed
    Reprocessing --> Failed
```

## Persisted Evidence

The SQLAlchemy model records:

- `Case` and `Document` lifecycle metadata
- rendered `Page` records with image quality measurements
- `OCRBlock` text, confidence, page, engine, and bounding box
- normalized `ExtractedField` values and source metadata
- reconstructed `ExtractedTable` rows
- `ReconciliationIssue` evidence and resolution state
- `RiskReport` factors and recommended actions
- `ReviewTask` and immutable `ReviewCorrection` records
- export and evaluation job metadata

## Extension Points

- Add an OCR engine behind the standard `OCRBlockResult` schema.
- Add document extraction templates without changing API contracts.
- Replace heuristic layout detection with a LayoutParser-backed model.
- Add new reconciliation checks without coupling them to OCR.
- Move `CaseProcessingService` calls into Celery tasks for production scale.
- Replace local storage with object storage while preserving document metadata.

## Reliability Decisions

- Real OCR is attempted before any demo fallback.
- Demo OCR requires an explicit environment switch and its confidence is capped.
- Reprocessing clears stale document results before persisting a new run.
- OCR engine failures fall through to the next configured engine.
- Normalized identifiers and totals have regression coverage for title and currency
  parsing edge cases.
- A standalone smoke test rejects demo OCR and validates known PDF fields.

## Production Gaps

The current design intentionally leaves authentication, tenancy, malware scanning,
encryption policy, quotas, retention, distributed tracing, and queue-based progress
events for the roadmap. See [`limitations.md`](limitations.md).
