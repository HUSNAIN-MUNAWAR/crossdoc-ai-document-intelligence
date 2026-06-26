from dataclasses import dataclass
@dataclass
class ClassificationResult:
    document_type: str
    confidence: float
    evidence: list[str]

class DocumentClassifier:
    def classify(self, filename: str, text: str = "", layout_clues: dict | None = None):
        h = f"{filename} {text}".lower()
        rules = {
            "commercial_invoice":["commercial invoice","invoice","inv-","subtotal","total amount"],
            "packing_list":["packing list","gross weight","cartons","package"],
            "bill_of_lading":["bill of lading","bol","vessel","consignee"],
            "purchase_order":["purchase order","po-","ship to"],
            "delivery_note":["delivery note","received by","delivered by"],
            "bank_payment_proof":["payment proof","bank","transaction","iban"],
            "customs_declaration":["customs","hs code","declaration"],
            "inspection_report":["inspection report","qc","defect"],
            "receipt":["receipt","paid","cash"],
        }
        best=("unknown",0,[])
        for dt,kws in rules.items():
            ev=[k for k in kws if k in h]
            if len(ev)>best[1]: best=(dt,len(ev),ev)
        return ClassificationResult(best[0], min(.95,.35+.15*best[1]) if best[0]!="unknown" else .25, best[2])
