from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    app_env: str = "local"
    frontend_origin: str = "http://localhost:3000"
    database_url: str = "sqlite:///./crossdoc_local.sqlite3"
    redis_url: str = "redis://localhost:6379/0"
    local_storage_dir: str = ".storage"

    # CROSSDOC_DEMO_OCR is the explicit switch for deterministic demo OCR.
    # CROSSDOC_DEMO_MODE is kept for compatibility with earlier MVP builds.
    crossdoc_demo_ocr: bool = False
    crossdoc_demo_mode: bool = False

    enable_paddleocr: bool = True
    enable_tesseract: bool = True
    enable_docling: bool = True
    enable_layoutparser: bool = True
    ocr_lang: str = "en"
    ocr_confidence_threshold: float = 0.72
    review_confidence_threshold: float = 0.75
    layout_mode: str = "heuristic"
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    @property
    def demo_ocr_enabled(self) -> bool:
        return bool(self.crossdoc_demo_ocr or self.crossdoc_demo_mode)

    @property
    def storage_path(self) -> Path:
        p = Path(self.local_storage_dir)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        p.mkdir(parents=True, exist_ok=True)
        return p

@lru_cache
def get_settings() -> Settings:
    return Settings()
