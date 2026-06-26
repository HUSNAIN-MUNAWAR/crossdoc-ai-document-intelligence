from app.services.layout_detector import LayoutDetector, LayoutRegion

class LayoutService:
    def detect_regions(self, image_path=None, ocr_blocks=None, image_size=(1000, 1400), page_number=1, mode="heuristic"):
        return [r.to_dict() for r in LayoutDetector().detect(image_path=image_path, ocr_blocks=ocr_blocks, image_size=image_size, page_number=page_number, mode=mode)]
