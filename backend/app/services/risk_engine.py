from __future__ import annotations

class RiskEngine:
    weights = {
        "missing_required_field": 12,
        "low_confidence_fields": 10,
        "ocr_quality": 10,
        "amount_mismatch": 25,
        "quantity_mismatch": 25,
        "destination_mismatch": 15,
        "currency_mismatch": 18,
        "invalid_container_number": 12,
        "invalid_hs_code": 8,
        "review_task_count": 3,
        "duplicate_document_risk": 10,
        "duplicate_invoice_reference": 10,
        "date_sequence_issue": 12,
    }

    def calculate(self, documents, issues, review_tasks: list | None = None):
        score = 0
        factors = []
        review_tasks = review_tasks or []
        for d in documents:
            fields = d.get("fields", {})
            required = ["invoice_number", "supplier_name", "buyer_name", "total_amount"] if d.get("document_type") == "commercial_invoice" else []
            for r in required:
                if r not in fields or fields.get(r, {}).get("normalized_value") in [None, ""]:
                    score += self.weights["missing_required_field"]
                    factors.append({"type": "missing_required_field", "field": r, "points": self.weights["missing_required_field"], "explanation": f"{d.get('document_type')} is missing {r}."})
            conf = [float(v.get("confidence", 1)) for v in fields.values() if isinstance(v, dict) and v.get("confidence") is not None]
            if conf and sum(conf)/len(conf) < .75:
                pts = self.weights["low_confidence_fields"]
                score += pts
                factors.append({"type": "low_confidence_fields", "points": pts, "average_confidence": round(sum(conf)/len(conf), 3), "explanation": "Average field confidence is below review threshold."})
            if float(d.get("quality_score", 1) or 1) < .55:
                pts = self.weights["ocr_quality"]
                score += pts
                factors.append({"type": "ocr_quality", "points": pts, "quality_score": d.get("quality_score"), "explanation": "Document image quality may reduce OCR reliability."})
            for field_name, payload in fields.items():
                warnings = payload.get("warnings", []) if isinstance(payload, dict) else []
                if "invalid_hs_code_length" in warnings:
                    pts = self.weights["invalid_hs_code"]
                    score += pts; factors.append({"type":"invalid_hs_code", "field": field_name, "points": pts, "explanation":"HS code failed basic length validation."})
                if "invalid_container_format" in warnings:
                    pts = self.weights["invalid_container_number"]
                    score += pts; factors.append({"type":"invalid_container_number", "field": field_name, "points": pts, "explanation":"Container number failed format validation."})
        for i in issues:
            typ = i.get("type") or i.get("issue_type") if isinstance(i, dict) else getattr(i, "type", getattr(i, "issue_type", "unknown"))
            severity = i.get("severity") if isinstance(i, dict) else getattr(i, "severity", None)
            message = i.get("message") if isinstance(i, dict) else getattr(i, "message", "")
            pts = self.weights.get(typ, 8)
            score += pts
            factors.append({"type": typ, "severity": severity, "points": pts, "message": message, "explanation": self._explain_issue(typ)})
        if review_tasks:
            pts = min(15, len(review_tasks) * self.weights["review_task_count"])
            score += pts
            factors.append({"type": "review_task_count", "points": pts, "count": len(review_tasks), "explanation": "Many fields need human review."})
        score = min(100, int(score))
        level = "low" if score <= 25 else "medium" if score <= 50 else "high" if score <= 75 else "critical"
        top = sorted(factors, key=lambda f: f.get("points", 0), reverse=True)[:5]
        action = "Approve after spot-check." if level == "low" else "Review flagged fields before approval." if level in {"medium", "high"} else "Block approval until critical mismatches are resolved."
        confidence = round(max(0.35, 1 - (len(factors) * 0.04)), 3)
        return {"score": score, "level": level, "top_factors": top, "factors": factors, "explanation": self._summary(level, top), "recommended_action": action, "recommended_actions": [action], "confidence": confidence}

    def _explain_issue(self, typ: str) -> str:
        return {
            "quantity_mismatch": "Quantity does not agree across shipment/commercial documents.",
            "amount_mismatch": "Financial amount differs across invoice, PO, or payment proof.",
            "destination_mismatch": "Destination differs across logistics documents.",
            "duplicate_invoice_reference": "Repeated invoice reference can indicate duplicate processing risk.",
        }.get(typ, "Rule-based risk factor was triggered.")

    def _summary(self, level: str, top: list[dict]) -> str:
        if not top:
            return "No major risk factors were detected by the rule-based engine."
        names = ", ".join(f.get("type", "unknown") for f in top[:3])
        return f"Risk level is {level} due mainly to: {names}."
