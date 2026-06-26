from __future__ import annotations

from statistics import median
from typing import Any


def _get(block: Any, key: str, default=None):
    if isinstance(block, dict):
        return block.get(key, default)
    return getattr(block, key, default)


def _bbox(block: Any) -> dict[str, float]:
    b = _get(block, "bbox", {}) or {}
    return {"x": float(b.get("x", 0) or 0), "y": float(b.get("y", 0) or 0), "w": float(b.get("w", b.get("width", 0)) or 0), "h": float(b.get("h", b.get("height", 0)) or 0)}


def _text(block: Any) -> str:
    return str(_get(block, "text", "") or "")


class TableExtractor:
    def reconstruct(self, blocks: list[Any], y_tolerance: int = 18) -> list[dict]:
        if not blocks:
            return []
        rows = self.group_rows(blocks, y_tolerance)
        columns = self.infer_columns(rows)
        table_rows = []
        warnings = []
        for row in rows:
            cells = [_text(b).strip() for b in sorted(row, key=lambda x: _bbox(x)["x"]) if _text(b).strip()]
            if not cells:
                continue
            repaired = self.repair_row(cells)
            if repaired != cells:
                warnings.append("repaired_broken_numeric_or_amount_cells")
            table_rows.append({"cells": repaired, "raw_text": " | ".join(cells)})
        table_rows = [r for r in table_rows if any(c.strip() for c in r["cells"])]
        if not table_rows:
            return []
        header_idx = self.detect_header_row(table_rows)
        source_boxes = [_bbox(b) for b in blocks]
        source_bbox = self._union(source_boxes)
        return [{
            "table_name": "reconstructed_table",
            "columns": columns or (table_rows[header_idx]["cells"] if header_idx is not None else []),
            "rows": table_rows,
            "header_row_index": header_idx,
            "confidence": round(min(0.92, 0.45 + len(table_rows) * 0.05 + len(columns) * 0.03), 3),
            "warnings": sorted(set(warnings)),
            "source_page": int(_get(blocks[0], "page_number", 1) or 1),
            "source_bbox": source_bbox,
            "likely_totals_row": self.find_totals_row(table_rows),
        }]

    def group_rows(self, blocks: list[Any], y_tolerance: int = 18) -> list[list[Any]]:
        rows: list[list[Any]] = []
        for b in sorted(blocks, key=lambda x: (_get(x, "page_number", 1), _bbox(x)["y"], _bbox(x)["x"])):
            y = _bbox(b)["y"]
            placed = False
            for row in rows:
                row_y = median([_bbox(x)["y"] for x in row])
                if abs(row_y - y) <= y_tolerance:
                    row.append(b); placed = True; break
            if not placed:
                rows.append([b])
        return [sorted(r, key=lambda x: _bbox(x)["x"]) for r in rows if len(r) >= 1]

    def infer_columns(self, rows: list[list[Any]], x_tolerance: int = 40) -> list[str]:
        xs = sorted({_bbox(b)["x"] for row in rows for b in row})
        clusters: list[list[float]] = []
        for x in xs:
            if clusters and abs(median(clusters[-1]) - x) <= x_tolerance:
                clusters[-1].append(x)
            else:
                clusters.append([x])
        return [f"col_{i+1}" for i in range(len(clusters))]

    def repair_row(self, cells: list[str]) -> list[str]:
        repaired: list[str] = []
        i = 0
        while i < len(cells):
            cell = cells[i].strip()
            # Merge broken amount fragments such as ["18", ",500"] or ["USD", "18,500"].
            if i + 1 < len(cells) and cell.replace(",", "").isdigit() and cells[i+1].strip().startswith((",", ".")):
                repaired.append(cell + cells[i+1].strip()); i += 2; continue
            if cell.upper() in {"USD", "PKR", "SAR", "AED", "EUR"} and i + 1 < len(cells) and any(ch.isdigit() for ch in cells[i+1]):
                repaired.append(cell.upper() + " " + cells[i+1].strip()); i += 2; continue
            repaired.append(cell); i += 1
        return repaired

    def detect_header_row(self, rows: list[dict]) -> int | None:
        header_words = {"sku", "description", "qty", "quantity", "unit", "price", "total", "amount"}
        for i, row in enumerate(rows[:4]):
            tokens = " ".join(row.get("cells", [])).lower().replace("/", " ").split()
            if len(header_words.intersection(tokens)) >= 2:
                return i
        return None

    def find_totals_row(self, rows: list[dict]) -> int | None:
        for i, row in enumerate(rows):
            if any("total" in str(c).lower() for c in row.get("cells", [])):
                return i
        return None

    def _union(self, boxes: list[dict[str, float]]) -> dict[str, float]:
        if not boxes:
            return {"x": 0, "y": 0, "w": 0, "h": 0}
        x1 = min(b["x"] for b in boxes); y1 = min(b["y"] for b in boxes)
        x2 = max(b["x"] + b["w"] for b in boxes); y2 = max(b["y"] + b["h"] for b in boxes)
        return {"x": x1, "y": y1, "w": max(0, x2-x1), "h": max(0, y2-y1)}
