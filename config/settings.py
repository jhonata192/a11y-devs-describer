import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    max_pages: int = int(os.getenv("MAX_PAGES", "50"))
    temp_dir: Path = Path(os.getenv("TEMP_DIR", "temp"))
    logs_dir: Path = Path(os.getenv("LOGS_DIR", "logs"))
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    vision_model: str = os.getenv("VISION_MODEL", "llava:7b")
    router_model: str = os.getenv("ROUTER_MODEL", "phi3:mini")
    translation_model: str = os.getenv("TRANSLATION_MODEL", "qwen2.5:1.5b")
    keep_alive: int = int(os.getenv("KEEP_ALIVE", "0"))
    ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT", "3600"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    allowed_extensions: set[str] = field(default_factory=lambda: _default_extensions())

    @property
    def bot_token_valid(self) -> bool:
        return bool(self.bot_token)

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


def _default_extensions() -> set[str]:
    return {
        ".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif",
        ".bmp", ".gif", ".webp",
    }


settings = Settings()
