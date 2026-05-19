import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    max_pages: int = int(os.getenv("MAX_PAGES", "50"))
    temp_dir: Path = Path(os.getenv("TEMP_DIR", "temp"))
    data_dir: Path = Path(os.getenv("DATA_DIR", "data"))
    logs_dir: Path = Path(os.getenv("LOGS_DIR", "logs"))
    opencode_url: str = os.getenv("OPENCODE_URL", "http://127.0.0.1:4096")
    opencode_model: str = os.getenv("OPENCODE_MODEL", "qwen3.6-plus-free")
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "3600"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    allowed_extensions: set[str] = field(default_factory=lambda: _default_extensions())
    tesseract_cmd: str = os.getenv("TESSERACT_CMD", "tesseract")
    max_page_width: int = int(os.getenv("MAX_PAGE_WIDTH", "1600"))
    jpg_quality: int = int(os.getenv("JPG_QUALITY", "85"))
    pdf_split_dpi: int = int(os.getenv("PDF_SPLIT_DPI", "150"))

    @property
    def bot_token_valid(self) -> bool:
        return bool(self.bot_token)

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def db_path(self) -> Path:
        return self.data_dir / "history.db"


def _default_extensions() -> set[str]:
    return {
        ".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif",
        ".bmp", ".gif", ".webp", ".docx", ".html",
    }


settings = Settings()
