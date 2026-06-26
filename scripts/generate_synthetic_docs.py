from __future__ import annotations
import argparse, json, random
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

CASES = {
 "SHIP-2026-001": {"invoice_number":"INV-2026-001","po_number":"PO-2026-077","supplier_name":"Atlas Trading Co.","buyer_name":"Nexa Imports Ltd.","origin":"Karachi","destination":"Jeddah","quantity":500,"packing_quantity":480,"currency":"USD","total_amount":18500,"payment_amount":18000,"container_number":"MSCU1234567","issue":"quantity_destination_amount_mismatch"},
 "SHIP-2026-002": {"invoice_number":"INV-2026-002","po_number":"PO-2026-088","supplier_name":"Green Valley Foods","buyer_name":"Riyadh Retail Co.","origin":"Lahore","destination":"Riyadh","quantity":220,"packing_quantity":220,"currency":"USD","total_amount":7600,"payment_amount":7600,"container_number":"TCLU7654321","issue":"low"},
 "FIN-2026-003": {"invoice_number":"INV-2026-300","po_number":"PO-2026-300","supplier_name":"Metro Supplies Pvt Ltd","buyer_name":"Nexa Imports Ltd.","origin":"Islamabad","destination":"Dubai","quantity":100,"packing_quantity":100,"currency":"PKR","total_amount":1250000,"payment_amount":1200000,"container_number":"MSCU1234567","issue":"amount_mismatch"},
 "SHIP-2026-004": {"invoice_number":"INV-2026-004","po_number":"","supplier_name":"Blue Ocean Exporters Ltd","buyer_name":"Jeddah Market LLC","origin":"Gwadar","destination":"Jeddah","quantity":900,"packing_quantity":900,"currency":"SAR","total_amount":91000,"payment_amount":91000,"container_number":"OOLU7654321","issue":"missing_po"},
 "SHIP-2026-005": {"invoice_number":"INV-2026-005","po_number":"PO-2026-105","supplier_name":"Atlas Trading Company","buyer_name":"Nexa Imports Limited","origin":"Karachi","destination":"Dammam","quantity":350,"packing_quantity":350,"currency":"USD","total_amount":12250,"payment_amount":12250,"container_number":"MSCU12X4567","issue":"invalid_container"},
}
DOCS = [("commercial_invoice","Commercial Invoice"),("packing_list","Packing List"),("bill_of_lading","Bill of Lading"),("purchase_order","Purchase Order"),("bank_payment_proof","Bank Payment Proof"),("delivery_note","Delivery Note")]
NOISE_VARIANTS = ["clean", "noisy_scanned", "rotated", "low_contrast", "stamp_signature"]

def draw_pdf(path: Path, doc_type: str, title: str, d: dict):
    c = canvas.Canvas(str(path), pagesize=A4); w, h = A4
    c.setFont("Helvetica-Bold", 18); c.drawString(50, h-60, title)
    c.setFont("Helvetica", 9); c.drawString(50, h-78, "Synthetic demo document - generated locally, no private data")
    y = h-120
    dest = d["destination"]
    if d["issue"] == "quantity_destination_amount_mismatch" and doc_type == "packing_list": dest = "Riyadh"
    rows = [("Invoice Number",d["invoice_number"]),("PO Number",d["po_number"] or ""),("Supplier",d["supplier_name"]),("Buyer",d["buyer_name"]),("Origin",d["origin"]),("Destination", dest),("Container",d["container_number"]),("Currency",d["currency"]),("Invoice Date","2026-06-27"),("Shipment Date","2026-06-28")]
    qty = d["packing_quantity"] if doc_type == "packing_list" else d["quantity"]
    amt = d["payment_amount"] if doc_type == "bank_payment_proof" else d["total_amount"]
    if doc_type in {"commercial_invoice","packing_list","purchase_order","delivery_note","bill_of_lading"}: rows.append(("Quantity", str(qty)))
    if doc_type in {"commercial_invoice","purchase_order","bank_payment_proof","receipt"}: rows.append(("Total Amount", f"{d['currency']} {amt:,}"))
    if doc_type == "bill_of_lading": rows.append(("Bill of Lading", "BL-2026-445"))
    for k, v in rows:
        c.setFont("Helvetica-Bold", 10); c.drawString(55, y, k + ":")
        c.setFont("Helvetica", 10); c.drawString(185, y, str(v)); y -= 22
    y -= 15; c.setFont("Helvetica-Bold", 11); c.drawString(55, y, "Line Items"); y -= 24
    headers = ["SKU", "Description", "Qty", "Unit", "Total"]
    for x, hdr in zip([55, 140, 330, 405, 480], headers): c.drawString(x, y, hdr)
    y -= 18
    vals = ["BG-100", "Baguette trays", qty, 37, qty*37]
    for x, val in zip([55, 140, 330, 405, 480], vals): c.drawString(x, y, str(val))
    c.setFont("Helvetica-Oblique", 8); c.drawString(55, 55, "Generated for CrossDoc AI demo and evaluation."); c.save()

def draw_variant_png(path: Path, title: str, d: dict, variant: str):
    img = Image.new("RGB", (1240, 1754), "white"); dr = ImageDraw.Draw(img)
    dr.rectangle([60, 60, 1180, 1690], outline=(180, 190, 200), width=3)
    dr.text((90, 90), title.upper(), fill=(15, 23, 42))
    y = 180
    rows = [f"Invoice Number: {d['invoice_number']}", f"PO Number: {d['po_number']}", f"Supplier: {d['supplier_name']}", f"Buyer: {d['buyer_name']}", f"Destination: {d['destination']}", f"Quantity: {d['quantity']}", f"Total Amount: {d['currency']} {d['total_amount']:,}"]
    for row in rows:
        dr.text((90, y), row, fill=(20, 32, 50)); dr.line([90, y+32, 1080, y+32], fill=(220, 224, 230), width=2); y += 52
    dr.text((90, y+40), "SKU     Description             Qty    Unit    Total", fill=(15,23,42))
    dr.text((90, y+90), f"BG-100  Baguette trays          {d['quantity']}    37      {d['quantity']*37}", fill=(15,23,42))
    if variant in {"stamp_signature", "noisy_scanned"}:
        dr.ellipse([780, 210, 1010, 330], outline=(220, 70, 70), width=6); dr.text((815, 255), "CHECKED", fill=(200, 60, 60))
        dr.line([760, 1350, 1000, 1300, 1060, 1360], fill=(30, 40, 60), width=5)
    if variant == "noisy_scanned":
        for _ in range(600):
            x, y = random.randint(60, 1180), random.randint(60, 1690); dr.point((x, y), fill=(random.randint(150,230),)*3)
        img = img.filter(ImageFilter.GaussianBlur(.45))
    if variant == "rotated": img = img.rotate(2.2, expand=True, fillcolor="white")
    if variant == "low_contrast": img = ImageEnhance.Contrast(img).enhance(.52)
    if variant == "stamp_signature": img = img.filter(ImageFilter.GaussianBlur(.2))
    img.save(path)

def documents_for_case(cid: str):
    if cid == "FIN-2026-003": return [("commercial_invoice","Commercial Invoice"),("bank_payment_proof","Bank Payment Proof"),("receipt","Receipt")]
    if cid == "SHIP-2026-002": return [("commercial_invoice","Commercial Invoice"),("packing_list","Packing List"),("bank_payment_proof","Bank Payment Proof")]
    return DOCS

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="sample_data/generated_cases"); ap.add_argument("--truth", default="sample_data/ground_truth"); args = ap.parse_args()
    out = Path(args.out); truth = Path(args.truth); out.mkdir(parents=True, exist_ok=True); truth.mkdir(parents=True, exist_ok=True)
    for cid, d in CASES.items():
        cdir = out / cid; cdir.mkdir(parents=True, exist_ok=True); docs = []
        for doc_type, title in documents_for_case(cid):
            draw_pdf(cdir / f"{doc_type}.pdf", doc_type, title, d)
            for variant in NOISE_VARIANTS: draw_variant_png(cdir / f"{doc_type}_{variant}.png", title, d, variant)
            fields = {"invoice_number": d["invoice_number"], "po_number": d["po_number"], "supplier_name": d["supplier_name"], "buyer_name": d["buyer_name"], "destination": d["destination"], "quantity": d["packing_quantity"] if doc_type == "packing_list" else d["quantity"], "currency": d["currency"], "total_amount": d["payment_amount"] if doc_type == "bank_payment_proof" else d["total_amount"]}
            if doc_type == "bill_of_lading": fields.update({"bill_of_lading_number":"BL-2026-445", "container_number": d["container_number"]})
            docs.append({"type": doc_type, "fields": fields})
        (truth / f"{cid}.json").write_text(json.dumps({"case_id": cid, "documents": docs, "intentional_issue": d["issue"]}, indent=2), encoding="utf-8")
    print(f"Generated {len(CASES)} synthetic cases in {out}")

if __name__ == "__main__": main()
