from pathlib import Path
from PIL import Image

class DocumentLoader:
    def load_pages(self, file_path, out_dir):
        file_path, out_dir = Path(file_path), Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        if file_path.suffix.lower()==".pdf":
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(str(file_path), dpi=180)
            except Exception:
                images = [Image.new("RGB",(1240,1754),"white")]
        else:
            images = [Image.open(file_path).convert("RGB")]
        pages=[]
        for i,img in enumerate(images,1):
            p = out_dir / f"{file_path.stem}_page_{i}.png"
            img.save(p)
            pages.append({"page_number":i,"image_path":str(p),"width":img.width,"height":img.height})
        return pages
