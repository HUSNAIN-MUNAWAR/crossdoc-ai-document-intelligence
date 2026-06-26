from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from rapidfuzz import fuzz

NUMERIC_REPAIRS = str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1", "L": "1", "S": "5", "B": "8"})
ALPHA_REPAIRS = str.maketrans({"0": "O", "1": "I"})

class PostProcessor:
    def repair_numeric_context(self, value: str) -> str:
        # Only repair tokens that contain digits or are clearly numeric fragments.
        def repl(match: re.Match) -> str:
            token = match.group(0)
            if re.search(r"\d", token) or re.search(r"[OIlLSB]", token) and re.search(r"[-.,/]|^[$]?$", token):
                return token.translate(NUMERIC_REPAIRS)
            return token
        parts = []
        for token in re.split(r"(\s+)", str(value)):
            if re.search(r"\d", token) or re.fullmatch(r"[OIlLSB,./-]+", token):
                parts.append(token.translate(NUMERIC_REPAIRS))
            else:
                parts.append(token)
        return "".join(parts)

    def repair_text_preserving_words(self, value: str) -> str:
        return self.repair_numeric_context(value)

    def normalize_invoice_number(self, value: str) -> str:
        text = str(value).strip().replace(" ", "").replace(".", "-").upper()
        text = text.replace("LNV", "INV").replace("1NV", "INV").replace("LNVOICE", "INVOICE")
        out = []
        for part in re.split(r"([-_/])", text):
            if part in {"-", "_", "/"}:
                out.append("-"); continue
            if re.search(r"\d|[OILSB]", part) and not part in {"INV", "PO", "BL"}:
                out.append(part.translate(NUMERIC_REPAIRS))
            else:
                out.append(part)
        return re.sub(r"-+", "-", "".join(out)).replace("1NV", "INV")

    def normalize_po_number(self, value: str) -> str:
        text = str(value).strip().replace(" ", "").upper().replace("P0", "PO")
        return self.normalize_invoice_number(text).replace("P0", "PO")

    def normalize_date(self, value: str) -> str:
        text = self.repair_numeric_context(str(value)).replace("/", "-").replace(".", "-").strip()
        text = re.sub(r"[^0-9A-Za-z-]", "", text)
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y", "%Y%m%d", "%d%b%Y", "%d%B%Y"):
            try:
                return datetime.strptime(text, fmt).date().isoformat()
            except ValueError:
                pass
        m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}" if m else str(value).strip()

    def normalize_amount(self, value: str):
        repaired = self.repair_numeric_context(str(value))
        text = re.sub(r"[^0-9.,-]", "", repaired).replace(",", "")
        if not text or text in {"-", "."}:
            return None
        try:
            d = Decimal(text)
            return int(d) if d == d.to_integral() else float(d)
        except InvalidOperation:
            return None

    def normalize_currency(self, value: str) -> str:
        text = str(value).upper()
        mapping = {"$": "USD", "US$": "USD", "USD": "USD", "PKR": "PKR", "RS": "PKR", "SAR": "SAR", "AED": "AED", "EUR": "EUR", "GBP": "GBP"}
        for k, v in mapping.items():
            if k in text:
                return v
        m = re.search(r"\b[A-Z]{3}\b", text)
        return m.group(0) if m else text.strip()

    def normalize_quantity(self, value: str):
        n = self.normalize_amount(value)
        return int(n) if n is not None else None

    def normalize_unit_price(self, value: str):
        return self.normalize_amount(value)

    def normalize_container_number(self, value: str) -> dict:
        raw = re.sub(r"[^A-Za-z0-9]", "", str(value))
        prefix = raw[:4].upper().translate(ALPHA_REPAIRS)
        suffix = raw[4:].upper().translate(NUMERIC_REPAIRS)
        normalized = prefix + suffix
        ok = bool(re.fullmatch(r"[A-Z]{4}\d{7}", normalized))
        return {"value": normalized, "valid_format": ok, "warning": "checksum_not_implemented" if ok else "invalid_container_format"}

    def validate_hs_code(self, value: str) -> dict:
        code = re.sub(r"\D", "", self.repair_numeric_context(str(value)))
        return {"value": code, "valid_format": 6 <= len(code) <= 10, "warning": None if 6 <= len(code) <= 10 else "invalid_hs_code_length"}

    def cleanup_company_name(self, value: str) -> str:
        text = re.sub(r"\s+", " ", str(value)).strip(" .,-").lower()
        text = re.sub(r"\b(private|pvt\.?|limited|ltd\.?|company|co\.?)\b", "", text)
        text = re.sub(r"[^a-z0-9 ]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text.title()

    def company_match_score(self, a: str, b: str) -> float:
        ca, cb = self.cleanup_company_name(a), self.cleanup_company_name(b)
        if not ca or not cb:
            return 0.0
        return round(fuzz.token_set_ratio(ca, cb) / 100, 3)

    def merge_duplicate_line_items(self, rows: list[dict]) -> list[dict]:
        merged = {}
        for r in rows:
            k = str(r.get("sku") or r.get("description") or f"row-{len(merged)}").lower()
            if k not in merged:
                merged[k] = dict(r)
            else:
                merged[k]["quantity"] = int(merged[k].get("quantity", 0) or 0) + int(r.get("quantity", 0) or 0)
                if "total" in r and "total" in merged[k]:
                    merged[k]["total"] = (merged[k].get("total") or 0) + (r.get("total") or 0)
        return list(merged.values())
