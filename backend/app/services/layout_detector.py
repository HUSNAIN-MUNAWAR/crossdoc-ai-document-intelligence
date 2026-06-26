from __future__ import annotations

import itertools
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

VALID_LABELS = {"header", "footer", "table", "key_value_area", "signature", "stamp", "line_items_area", "paragraph"}


@dataclass
class LayoutRegion:
    region_id: str
    label: str
    bbox: dict[str, float]
    confidence: float
    page_number: int
    method: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _bbox(block: Any) -> dict[str, float]:
    b = getattr(block, "bbox", block.get("bbox", {}) if isinstance(block, dict) else {}) or {}
    return {"x": float(b.get("x", 0) or 0), "y": float(b.get("y", 0) or 0), "w": float(b.get("w", b.get("width", 0)) or 0), "h": float(b.get("h", b.get("height", 0)) or 0)}


def _text(block: Any) -> str:
    return str(getattr(block, "text", block.get("text", "") if isinstance(block, dict) else ""))


def _union(boxes: list[dict[str, float]]) -> dict[str, float]:
    if not boxes:
        return {"x": 0, "y": 0, "w": 0, "h": 0}
    x1 = min(b["x"] for b in boxes); y1 = min(b["y"] for b in boxes)
    x2 = max(b["x"] + b["w"] for b in boxes); y2 = max(b["y"] + b["h"] for b in boxes)
    return {"x": x1, "y": y1, "w": max(0, x2-x1), "h": max(0, y2-y1)}


class LayoutDetector:
    def detect(self, image_path: str | Path | None = None, ocr_blocks: list[Any] | None = None, image_size: tuple[int, int] = (1000, 1400), page_number: int = 1, mode: str = "heuristic") -> list[LayoutRegion]:
        if mode == "model":
            model_regions = self._try_layoutparser(image_path, page_number)
            if model_regions:
                return model_regions
        return self._heuristic(ocr_blocks or [], image_size, page_number)

    def _try_layoutparser(self, image_path: str | Path | None, page_number: int) -> list[LayoutRegion]:
        if not image_path:
            return []
        try:
            import cv2
            import layoutparser as lp
            image = cv2.imread(str(image_path))
            if image is None:
                return []
            # Optional model hook. We do not download weights automatically.
            # Users can replace this with a locally configured LayoutParser model.
            return []
        except Exception:
            return []

    def _heuristic(self, blocks: list[Any], image_size: tuple[int, int], page_number: int) -> list[LayoutRegion]:
        width, height = image_size
        regions: list[LayoutRegion] = []
        boxes = [_bbox(b) for b in blocks]
        texts = [_text(b).lower() for b in blocks]
        if not blocks:
            return [
                LayoutRegion("r-header-empty", "header", {"x": 0, "y": 0, "w": width, "h": height * 0.15}, 0.35, page_number, "heuristic"),
                LayoutRegion("r-footer-empty", "footer", {"x": 0, "y": height * 0.88, "w": width, "h": height * 0.12}, 0.35, page_number, "heuristic"),
            ]
        top = [b for b in boxes if b["y"] < height * 0.18]
        bottom = [b for b in boxes if b["y"] > height * 0.82]
        if top:
            regions.append(LayoutRegion("r-header", "header", _union(top), 0.70, page_number, "heuristic"))
        if bottom:
            regions.append(LayoutRegion("r-footer", "footer", _union(bottom), 0.62, page_number, "heuristic"))
        kv = [boxes[i] for i, t in enumerate(texts) if any(k in t for k in ["invoice", "po", "supplier", "buyer", "destination", "container", "amount", "date"])]
        if kv:
            regions.append(LayoutRegion("r-key-values", "key_value_area", _union(kv), 0.74, page_number, "heuristic"))
        table_markers = [boxes[i] for i, t in enumerate(texts) if any(k in t for k in ["qty", "quantity", "unit", "total", "description", "sku", "line item"])]
        if table_markers:
            regions.append(LayoutRegion("r-table", "table", _union(table_markers), 0.68, page_number, "heuristic"))
            regions.append(LayoutRegion("r-line-items", "line_items_area", _union(table_markers), 0.66, page_number, "heuristic"))
        visual = [boxes[i] for i, t in enumerate(texts) if any(k in t for k in ["stamp", "seal", "signature", "signed"])]
        if visual:
            regions.append(LayoutRegion("r-signature-stamp", "signature", _union(visual), 0.58, page_number, "heuristic"))
        # Add a paragraph fallback for remaining content.
        if boxes:
            regions.append(LayoutRegion("r-body", "paragraph", _union(boxes), 0.55, page_number, "heuristic"))
        return regions
