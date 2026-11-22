"""Generate a deterministic CrossDoc reconciliation animation and evidence manifest."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.document_classifier import DocumentClassifier  # noqa: E402
from app.services.extraction_engine import ExtractionEngine  # noqa: E402
from app.services.layout_detector import LayoutDetector  # noqa: E402
from app.services.reconciliation_engine import ReconciliationEngine  # noqa: E402
from app.services.risk_engine import RiskEngine  # noqa: E402


GROUND_TRUTH = ROOT / "sample_data" / "ground_truth" / "SHIP-2026-001.json"
MANIFEST = ROOT / "docs" / "animation" / "crossdoc_reconciliation_sequence.json"
REEL = ROOT / "frontend" / "public" / "animation" / "crossdoc-reconciliation-reel.html"


def document_lines(doc: dict[str, object]) -> list[str]:
    fields = doc["fields"]
    title = str(doc["type"]).replace("_", " ").title()
    markers = {
        "commercial_invoice": ["Commercial Invoice", "Subtotal and Total Amount"],
        "packing_list": ["Packing List", "Package: standard cartons", "Cartons and package quantity"],
        "bill_of_lading": ["Bill of Lading", "Vessel: synthetic carrier", "Consignee: Nexa Imports Ltd."],
        "purchase_order": ["Purchase Order", "Ship To: Jeddah", "Buyer order record"],
        "bank_payment_proof": ["Bank Payment Proof", "Bank: synthetic settlement bank", "Transaction reference"],
        "delivery_note": ["Delivery Note", "Received By: synthetic warehouse", "Delivered By: synthetic carrier"],
    }
    lines = markers.get(str(doc["type"]), [title]) + [f"Invoice Number: {fields.get('invoice_number', '')}", f"PO Number: {fields.get('po_number', '')}"]
    total_label = "Total Amount" if doc["type"] == "commercial_invoice" else "Total"
    for key, label in (("supplier_name", "Supplier"), ("buyer_name", "Buyer"), ("destination", "Destination"), ("quantity", "Quantity"), ("currency", "Currency"), ("total_amount", "Total Amount"), ("bill_of_lading_number", "Bill of Lading"), ("container_number", "Container")):
        if fields.get(key) not in {None, ""}:
            value = fields[key]
            if key == "total_amount":
                value = f"{fields.get('currency', 'USD')} {value:,}"
            lines.append(f"{total_label if key == 'total_amount' else label}: {value}")
    quantity = int(fields.get("quantity", 0) or 0)
    lines.extend(["Line Items", "SKU Description Quantity Unit Total", f"BG-100 Baguette trays {quantity} 37 {quantity * 37}"])
    return lines


def synthetic_blocks(lines: list[str], confidence: float) -> list[dict[str, object]]:
    return [
        {
            "text": line,
            "confidence": confidence if index != 0 else min(0.92, confidence + 0.06),
            "bbox": {"x": 80, "y": 90 + index * 42, "w": 900, "h": 28},
            "page_number": 1,
            "engine": "synthetic_ocr_fixture",
        }
        for index, line in enumerate(lines)
    ]


def process_documents(truth: dict[str, object]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    classifier = DocumentClassifier()
    extractor = ExtractionEngine()
    layout = LayoutDetector()
    documents = []
    layout_counts = []
    for index, doc in enumerate(truth["documents"]):
        lines = document_lines(doc)
        confidence = 0.72 if doc["type"] == "packing_list" else 0.86
        blocks = synthetic_blocks(lines, confidence)
        text = "\n".join(lines)
        classified = classifier.classify(f"{doc['type']}.png", text)
        extracted = extractor.extract(classified.document_type, blocks)
        documents.append({
            "document_type": classified.document_type,
            "filename": f"{doc['type']}.png",
            "fields": extracted["fields"],
            "tables": extracted["tables"],
            "quality_score": 0.78 if index == 1 else 0.84,
            "ocr_confidence": round(sum(float(block["confidence"]) for block in blocks) / len(blocks), 3),
            "classification_confidence": classified.confidence,
            "classification_evidence": classified.evidence,
            "template_version": extracted["template_version"],
            "missing_required_fields": extracted["missing_required_fields"],
        })
        layout_counts.append({
            "filename": f"{doc['type']}.png",
            "regions": [region.to_dict() for region in layout.detect(ocr_blocks=blocks, page_number=1)],
        })
    return documents, layout_counts


def build_manifest() -> dict[str, object]:
    truth = json.loads(GROUND_TRUTH.read_text(encoding="utf-8"))
    documents, layout_counts = process_documents(truth)
    issues = [issue.to_dict() for issue in ReconciliationEngine().reconcile(documents)]
    risk = RiskEngine().calculate(documents, issues)
    source_bytes = GROUND_TRUTH.read_bytes()
    issue_types = [issue["type"] for issue in issues]
    return {
        "schema_version": "1.0",
        "fixture": truth["case_id"],
        "source": {
            "path": GROUND_TRUTH.relative_to(ROOT).as_posix(),
            "bytes": len(source_bytes),
            "sha256": hashlib.sha256(source_bytes).hexdigest(),
            "synthetic": True,
            "document_count": len(documents),
            "intentional_issue": truth["intentional_issue"],
        },
        "model": {
            "ocr_router": "backend/app/services/ocr_router.py::OCRRouter",
            "ocr_preferred_engine": "tesseract",
            "tesseract_binary_available": bool(shutil.which("tesseract")),
            "generator_input": "synthetic OCR evidence blocks; run scripts/validate_real_ocr.py for binary-backed OCR proof",
            "classifier": "backend/app/services/document_classifier.py::DocumentClassifier",
            "extraction": "backend/app/services/extraction_engine.py::ExtractionEngine",
            "layout": "backend/app/services/layout_detector.py::LayoutDetector(mode=heuristic)",
            "reconciliation": "backend/app/services/reconciliation_engine.py::ReconciliationEngine",
            "risk": "backend/app/services/risk_engine.py::RiskEngine",
            "claim_boundary": "Deterministic post-OCR reference path; synthetic fixture metrics are not universal OCR accuracy claims.",
        },
        "pipeline": {
            "document_types": [doc["document_type"] for doc in documents],
            "ocr_confidence_average": round(sum(doc["ocr_confidence"] for doc in documents) / len(documents), 3),
            "classification_confidence_average": round(sum(doc["classification_confidence"] for doc in documents) / len(documents), 3),
            "layout_region_count": sum(len(item["regions"]) for item in layout_counts),
            "reconciliation_issue_count": len(issues),
            "reconciliation_issue_types": issue_types,
            "risk": risk,
        },
        "layout_preview": layout_counts[:2],
        "events": [
            {"id": "ingest", "short": "Ingest", "title": "Six related documents enter one case", "detail": "Invoice, packing list, B/L, purchase order, delivery note, and payment proof share one synthetic case ID.", "metric": f"{len(documents)} documents · source lineage retained", "status": "received"},
            {"id": "ocr", "short": "OCR", "title": "Evidence blocks become searchable", "detail": "The manifest preserves the OCR router boundary; this deterministic run supplies synthetic blocks so post-OCR logic stays reproducible.", "metric": f"avg confidence {sum(doc['ocr_confidence'] for doc in documents) / len(documents):.0%} · tesseract {'ready' if shutil.which('tesseract') else 'not installed'}", "status": "evidence"},
            {"id": "classify", "short": "Classify", "title": "Document types are identified", "detail": "The repository classifier assigns logistics and finance types with keyword evidence.", "metric": f"{len(set(doc['document_type'] for doc in documents))} types · template 2026.06", "status": "typed"},
            {"id": "extract", "short": "Extract", "title": "Fields and tables are normalized", "detail": "ExtractionEngine applies repository patterns, post-processing, confidence, and table reconstruction.", "metric": f"{sum(len(doc['fields']) for doc in documents)} fields · {sum(len(doc['tables']) for doc in documents)} tables", "status": "normalized"},
            {"id": "reconcile", "short": "Reconcile", "title": "Cross-document mismatches surface", "detail": "ReconciliationEngine compares quantities, amounts, references, currencies, destinations, and duplicates.", "metric": f"{len(issues)} issues · {', '.join(issue_types[:3])}", "status": "flagged"},
            {"id": "risk", "short": "Risk", "title": "Explainable risk is calculated", "detail": "RiskEngine weights the findings and returns a review action instead of hiding the reason.", "metric": f"score {risk['score']} · {risk['level']} · confidence {risk['confidence']:.0%}", "status": "scored"},
            {"id": "review", "short": "Review", "title": "Human review packet is ready", "detail": "Top factors and evidence-linked recommended actions are presented for an operator decision.", "metric": f"{len(risk['top_factors'])} top factors · action: review flagged fields", "status": "human"},
            {"id": "export", "short": "Export", "title": "Evidence can be exported safely", "detail": "The case remains a synthetic decision-support artifact; no customs, tax, payment, or carrier action is executed.", "metric": "JSON · Markdown · API-ready evidence", "status": "safe"},
        ],
    }


def reel_html(manifest: dict[str, object]) -> str:
    sequence = json.dumps(manifest, indent=2, sort_keys=True).replace("</", "<\\/")
    return dedent(
        f"""\
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>CrossDoc AI — Reconciliation reference reel</title>
          <style>
            :root {{ color-scheme: dark; --ink: #edf4fa; --muted: #99acbd; --line: #28445a; --accent: #66d5ea; --warn: #f3bd67; }}
            * {{ box-sizing: border-box; }}
            body {{ margin: 0; min-width: 320px; background: radial-gradient(circle at 18% 0%, #154b62 0, #081721 55%, #050b11 100%); color: var(--ink); font: 15px/1.5 Inter, ui-sans-serif, system-ui, sans-serif; }}
            .reel {{ max-width: 1180px; margin: 0 auto; padding: 42px 28px 34px; }}
            .eyebrow {{ color: var(--accent); font-size: 12px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }}
            h1 {{ max-width: 820px; margin: 8px 0 10px; font-size: clamp(28px, 5vw, 52px); line-height: 1.02; letter-spacing: -.04em; }}
            .lede {{ max-width: 790px; margin: 0; color: var(--muted); font-size: 17px; }}
            .model-line {{ display: flex; flex-wrap: wrap; gap: 8px 18px; margin-top: 22px; color: var(--muted); font-size: 12px; }}
            .model-line span::before {{ content: "•"; color: var(--accent); margin-right: 8px; }}
            .stage {{ margin-top: 36px; overflow: hidden; border: 1px solid var(--line); border-radius: 22px; background: linear-gradient(145deg, rgba(17,49,68,.94), rgba(7,18,27,.97)); box-shadow: 0 22px 60px rgba(0,0,0,.28); }}
            svg {{ display: block; width: 100%; height: auto; min-height: 300px; }}
            .route {{ fill: none; stroke: #2b4d63; stroke-width: 4; stroke-linecap: round; stroke-dasharray: 7 12; }}
            .station circle {{ fill: #081721; stroke: #42647c; stroke-width: 3; transition: fill .25s ease, stroke .25s ease, transform .25s ease; transform-origin: center; }}
            .station text {{ fill: #9ab1c1; font-size: 14px; text-anchor: middle; }}
            .station .index {{ fill: #d0e0ea; font-size: 13px; font-weight: 700; }}
            .station.active circle {{ fill: #14505c; stroke: var(--accent); transform: scale(1.1); }}
            .station.active text {{ fill: var(--ink); }}
            .station.done circle {{ fill: #173a4b; stroke: #5c8ba0; }}
            .token {{ fill: var(--accent); stroke: #d6fbff; stroke-width: 3; filter: drop-shadow(0 0 12px rgba(102,213,234,.6)); }}
            .token-label {{ fill: #06202a; font-size: 11px; font-weight: 800; text-anchor: middle; }}
            .panel {{ display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: end; gap: 18px; padding: 22px 24px 24px; border-top: 1px solid var(--line); }}
            .panel h2 {{ margin: 0 0 3px; font-size: 24px; letter-spacing: -.02em; }}
            .panel p {{ margin: 0; color: var(--muted); }}
            .metric {{ color: var(--accent); font-size: 13px; font-weight: 700; text-align: right; }}
            .controls {{ display: flex; gap: 8px; margin-top: 16px; }}
            button {{ border: 1px solid #3b5f76; border-radius: 999px; padding: 9px 15px; background: #102a3a; color: var(--ink); font: inherit; cursor: pointer; }}
            button:hover, button:focus-visible {{ border-color: var(--accent); outline: 2px solid rgba(102,213,234,.35); outline-offset: 2px; }}
            .timeline {{ display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 7px; margin-top: 18px; }}
            .timeline button {{ min-height: 60px; border-radius: 12px; padding: 8px; color: var(--muted); text-align: left; font-size: 12px; }}
            .timeline button[aria-current="step"] {{ border-color: var(--accent); background: #164352; color: var(--ink); }}
            .timeline strong {{ display: block; color: inherit; font-size: 11px; text-transform: uppercase; letter-spacing: .08em; }}
            .disclaimer {{ margin-top: 20px; color: var(--muted); font-size: 12px; }}
            @media (max-width: 760px) {{ .reel {{ padding: 28px 16px; }} .panel {{ grid-template-columns: 1fr; }} .metric {{ text-align: left; }} .timeline {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} svg {{ min-height: 420px; }} }}
            @media (prefers-reduced-motion: reduce) {{ *, *::before, *::after {{ scroll-behavior: auto !important; transition-duration: .01ms !important; animation-duration: .01ms !important; animation-iteration-count: 1 !important; }} }}
          </style>
        </head>
        <body>
          <main class="reel" aria-labelledby="title">
            <div class="eyebrow">CrossDoc AI · production reference reel</div>
            <h1 id="title">Six documents. One explainable risk decision.</h1>
            <p class="lede">A synthetic shipment case travels through the actual post-OCR intelligence path: classification, extraction, reconciliation, risk, and human review.</p>
            <div class="model-line" aria-label="Model and data boundary"><span id="model-name"></span><span id="source-name"></span><span>synthetic case only</span></div>
            <section class="stage" aria-label="Animated reconciliation sequence">
              <svg viewBox="0 0 1210 390" role="img" aria-labelledby="diagram-title diagram-description">
                <title id="diagram-title">Animated CrossDoc reconciliation stages</title>
                <desc id="diagram-description">A case token travels through document intake, synthetic OCR evidence, classification, extraction, reconciliation, risk scoring, human review, and safe export.</desc>
                <path class="route" d="M 80 190 C 220 82, 360 82, 510 190 S 800 298, 1130 100" />
                <g id="stations"></g>
                <g aria-hidden="true"><circle id="token" class="token" cx="80" cy="190" r="22"></circle><text id="token-label" class="token-label" x="80" y="194">CASE</text></g>
              </svg>
              <div class="panel" aria-live="polite"><div><h2 id="event-title"></h2><p id="event-detail"></p></div><div id="event-metric" class="metric"></div></div>
            </section>
            <div class="controls"><button id="toggle" type="button">Pause</button><button id="replay" type="button">Replay</button></div>
            <div id="timeline" class="timeline" role="list" aria-label="Animation stages"></div>
            <p class="disclaimer">Synthetic fixture · deterministic post-OCR services · no customs, tax, payment, or carrier action is executed.</p>
          </main>
          <script>
            const sequence = {sequence};
            const events = sequence.events;
            const points = [[80,190],[230,96],[380,96],[530,190],[680,284],[830,284],[980,190],[1130,96]];
            const stations = document.getElementById('stations'), timeline = document.getElementById('timeline');
            const token = document.getElementById('token'), tokenLabel = document.getElementById('token-label');
            const title = document.getElementById('event-title'), detail = document.getElementById('event-detail'), metric = document.getElementById('event-metric');
            const toggle = document.getElementById('toggle');
            let current = 0, started = performance.now(), playing = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            const duration = 1850;
            points.forEach((point, index) => {{
              const group = document.createElementNS('http://www.w3.org/2000/svg', 'g'); group.classList.add('station');
              group.innerHTML = `<circle cx="${{point[0]}}" cy="${{point[1]}}" r="30"></circle><text class="index" x="${{point[0]}}" y="${{point[1] + 5}}">${{index + 1}}</text><text x="${{point[0]}}" y="${{point[1] + 57}}">${{events[index].short}}</text>`;
              stations.appendChild(group);
            }});
            events.forEach((event, index) => {{
              const item = document.createElement('button'); item.type = 'button'; item.setAttribute('role', 'listitem');
              item.innerHTML = `<strong>${{String(index + 1).padStart(2, '0')}} · ${{event.status}}</strong>${{event.title}}`;
              item.addEventListener('click', () => {{ current = index; started = performance.now(); playing = false; toggle.textContent = 'Play'; render(0); }}); timeline.appendChild(item);
            }});
            document.getElementById('model-name').textContent = `services: classifier · extractor · reconciliation · risk`;
            document.getElementById('source-name').textContent = `case ${{sequence.fixture}}`;
            function render(progress) {{
              const next = (current + 1) % points.length, from = points[current], to = points[next];
              const x = from[0] + (to[0] - from[0]) * progress, y = from[1] + (to[1] - from[1]) * progress;
              token.setAttribute('cx', x); token.setAttribute('cy', y); tokenLabel.setAttribute('x', x); tokenLabel.setAttribute('y', y + 4);
              title.textContent = events[current].title; detail.textContent = events[current].detail; metric.textContent = events[current].metric;
              document.querySelectorAll('.station').forEach((node, index) => {{ node.classList.toggle('active', index === current); node.classList.toggle('done', index < current); }});
              timeline.querySelectorAll('button').forEach((node, index) => node.setAttribute('aria-current', index === current ? 'step' : 'false'));
            }}
            function animate(now) {{ if (playing) {{ const progress = Math.min(1, (now - started) / duration); render(progress); if (progress >= 1) {{ current = (current + 1) % events.length; started = now; }} }} else {{ render(0); }} requestAnimationFrame(animate); }}
            toggle.addEventListener('click', () => {{ playing = !playing; started = performance.now(); toggle.textContent = playing ? 'Pause' : 'Play'; }});
            document.getElementById('replay').addEventListener('click', () => {{ current = 0; started = performance.now(); playing = true; toggle.textContent = 'Pause'; }});
            render(0); requestAnimationFrame(animate);
          </script>
        </body>
        </html>
        """
    )


def main() -> None:
    manifest = build_manifest()
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    REEL.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REEL.write_text(reel_html(manifest), encoding="utf-8")
    print(f"wrote {MANIFEST.relative_to(ROOT)}")
    print(f"wrote {REEL.relative_to(ROOT)}")
    print(f"source checksum: {manifest['source']['sha256']}")
    print(f"documents: {manifest['source']['document_count']}")
    print(f"issues: {manifest['pipeline']['reconciliation_issue_count']}")
    print(f"risk score: {manifest['pipeline']['risk']['score']}")


if __name__ == "__main__":
    main()
