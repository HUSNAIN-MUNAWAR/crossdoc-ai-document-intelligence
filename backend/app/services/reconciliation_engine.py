from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any

from app.services.postprocessor import PostProcessor

@dataclass
class ReconciliationIssue:
    type: str
    severity: str
    message: str
    source_documents: list[str]
    recommended_action: str
    evidence: dict[str, Any] = field(default_factory=dict)
    affected_fields: list[str] = field(default_factory=list)

    @property
    def issue_type(self) -> str:
        return self.type

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["issue_type"] = self.type
        return d

class ReconciliationEngine:
    def __init__(self):
        self.post = PostProcessor()

    def reconcile(self, documents: list[dict]) -> list[ReconciliationIssue]:
        by_type = {d.get("document_type", "unknown"): d for d in documents}
        issues: list[ReconciliationIssue] = []
        self._quantity(by_type, issues)
        self._amount(by_type, issues)
        self._destination(by_type, issues)
        self._currency(by_type, issues)
        self._container(by_type, issues)
        self._po_reference(by_type, issues)
        self._invoice_reference(by_type, issues)
        self._company_match(by_type, issues, "supplier_name")
        self._company_match(by_type, issues, "buyer_name")
        self._date_sequence(by_type, issues)
        self._duplicate_invoice(documents, issues)
        self._missing_required(by_type, issues)
        return issues

    def _field(self, by_type: dict, doc_type: str, name: str):
        return by_type.get(doc_type, {}).get("fields", {}).get(name, {}).get("normalized_value")

    def _issue(self, issues: list, issue_type: str, severity: str, message: str, docs: list[str], fields: list[str], action: str, evidence: dict | None = None):
        issues.append(ReconciliationIssue(issue_type, severity, message, docs, action, evidence or {}, fields))

    def _quantity(self, by_type, issues):
        pairs = [("commercial_invoice", "packing_list"), ("commercial_invoice", "delivery_note"), ("packing_list", "bill_of_lading")]
        for a, b in pairs:
            av, bv = self._field(by_type, a, "quantity"), self._field(by_type, b, "quantity")
            if av is not None and bv is not None and int(float(av)) != int(float(bv)):
                self._issue(issues, "quantity_mismatch", "high", f"{a} quantity is {av} but {b} quantity is {bv}.", [a, b], ["quantity"], "Review quantity fields and confirm shipped/paid quantity.", {a: av, b: bv})

    def _amount(self, by_type, issues):
        pairs = [("commercial_invoice", "purchase_order"), ("commercial_invoice", "bank_payment_proof")]
        for a, b in pairs:
            av, bv = self._field(by_type, a, "total_amount"), self._field(by_type, b, "total_amount")
            if av is not None and bv is not None and abs(float(av) - float(bv)) > 1:
                self._issue(issues, "amount_mismatch", "high", f"{a} total is {av} but {b} total is {bv}.", [a, b], ["total_amount"], "Review invoice total, PO total, and payment proof amount.", {a: av, b: bv})

    def _destination(self, by_type, issues):
        docs = ["commercial_invoice", "packing_list", "bill_of_lading", "delivery_note"]
        values = {d: str(self._field(by_type, d, "destination")).strip().lower() for d in docs if self._field(by_type, d, "destination")}
        if len(set(values.values())) > 1:
            self._issue(issues, "destination_mismatch", "medium", "Destination differs across shipment documents.", list(values), ["destination"], "Confirm final destination across invoice, packing list, B/L, and delivery note.", values)

    def _currency(self, by_type, issues):
        values = {d: self._field(by_type, d, "currency") for d in ["commercial_invoice", "purchase_order", "bank_payment_proof"] if self._field(by_type, d, "currency")}
        if len(set(values.values())) > 1:
            self._issue(issues, "currency_mismatch", "high", "Currency differs across financial documents.", list(values), ["currency"], "Verify payment currency and invoice currency.", values)

    def _container(self, by_type, issues):
        values = {d: self._field(by_type, d, "container_number") for d in ["packing_list", "bill_of_lading", "delivery_note"] if self._field(by_type, d, "container_number")}
        if len(set(values.values())) > 1:
            self._issue(issues, "container_number_mismatch", "medium", "Container number differs across shipment documents.", list(values), ["container_number"], "Check the container number on B/L and packing list.", values)
        for d, v in values.items():
            if not self.post.normalize_container_number(str(v))["valid_format"]:
                self._issue(issues, "invalid_container_number", "medium", f"{d} has invalid container number format: {v}.", [d], ["container_number"], "Re-check OCR region and container number format.", {d: v})

    def _po_reference(self, by_type, issues):
        values = {d: self._field(by_type, d, "po_number") for d in ["commercial_invoice", "packing_list", "purchase_order"] if self._field(by_type, d, "po_number")}
        if len(set(values.values())) > 1:
            self._issue(issues, "po_reference_mismatch", "medium", "PO reference differs across documents.", list(values), ["po_number"], "Confirm PO number across invoice, packing list and purchase order.", values)

    def _invoice_reference(self, by_type, issues):
        values = {d: self._field(by_type, d, "invoice_number") for d in ["commercial_invoice", "bank_payment_proof", "delivery_note"] if self._field(by_type, d, "invoice_number")}
        if len(set(values.values())) > 1:
            self._issue(issues, "invoice_reference_mismatch", "high", "Invoice reference differs across documents.", list(values), ["invoice_number"], "Confirm invoice reference before approving payment/shipment case.", values)

    def _company_match(self, by_type, issues, field):
        docs = ["commercial_invoice", "packing_list", "purchase_order", "bill_of_lading"]
        vals = {d: self._field(by_type, d, field) for d in docs if self._field(by_type, d, field)}
        if len(vals) < 2:
            return
        items = list(vals.items())
        base_doc, base_val = items[0]
        for d, v in items[1:]:
            score = self.post.company_match_score(str(base_val), str(v))
            if score < 0.82:
                self._issue(issues, f"{field}_mismatch", "medium", f"{field.replace('_',' ').title()} differs between {base_doc} and {d}.", [base_doc, d], [field], "Review company names; fuzzy match score is below threshold.", {base_doc: base_val, d: v, "match_score": score})

    def _date_sequence(self, by_type, issues):
        inv = self._field(by_type, "commercial_invoice", "invoice_date")
        ship = self._field(by_type, "bill_of_lading", "shipment_date") or self._field(by_type, "delivery_note", "shipment_date")
        if inv and ship:
            try:
                if date.fromisoformat(str(ship)) < date.fromisoformat(str(inv)):
                    self._issue(issues, "date_sequence_issue", "medium", "Shipment date appears earlier than invoice date.", ["commercial_invoice", "bill_of_lading"], ["invoice_date", "shipment_date"], "Confirm date extraction and document chronology.", {"invoice_date": inv, "shipment_date": ship})
            except Exception:
                pass

    def _duplicate_invoice(self, documents, issues):
        seen = {}
        for d in documents:
            inv = d.get("fields", {}).get("invoice_number", {}).get("normalized_value")
            if not inv:
                continue
            if inv in seen:
                self._issue(issues, "duplicate_invoice_reference", "medium", f"Invoice number {inv} appears in multiple documents/cases.", [seen[inv], d.get("document_type", "unknown")], ["invoice_number"], "Check whether documents are duplicates or legitimate references.", {"invoice_number": inv})
            seen[inv] = d.get("document_type", "unknown")

    def _missing_required(self, by_type, issues):
        required = {"commercial_invoice": ["invoice_number", "supplier_name", "buyer_name", "total_amount"], "purchase_order": ["po_number"], "bill_of_lading": ["bill_of_lading_number", "container_number"]}
        for doc, fields in required.items():
            if doc not in by_type:
                continue
            for f in fields:
                if self._field(by_type, doc, f) in [None, ""]:
                    self._issue(issues, "missing_required_field", "medium", f"{doc} is missing required field {f}.", [doc], [f], "Send field to human review or improve extraction template.", {"document": doc, "field": f})
