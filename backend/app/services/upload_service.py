from pathlib import Path
from uuid import uuid4

from app.core.config import get_settings
from app.models.domain import Document

ALLOWED_SUFFIXES={".pdf",".png",".jpg",".jpeg",".tif",".tiff"}

class UploadService:
    def save_uploads(self, db, case, files):
        root=get_settings().storage_path/case.case_id; root.mkdir(parents=True,exist_ok=True); saved=[]
        for file in files:
            safe_name=Path(file.filename or "").name
            suffix=Path(safe_name).suffix.lower()
            if suffix not in ALLOWED_SUFFIXES: raise ValueError(f"Unsupported file type: {suffix}")
            path=root/safe_name
            if path.exists():
                path=root/f"{path.stem}-{uuid4().hex[:8]}{suffix}"
            path.write_bytes(file.file.read())
            d=Document(case_id_fk=case.id, filename=safe_name or path.name, content_type=file.content_type or "application/octet-stream", storage_path=str(path), status="uploaded")
            db.add(d); saved.append(d)
        db.commit()
        for d in saved: db.refresh(d)
        return saved
