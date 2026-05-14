import hashlib
import json
import time
from pathlib import Path
from typing import Optional

from bot.utils.logger import logger

CACHE_DIR = Path("temp/cache")


def _ensure_cache_dir() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _file_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()[:16]


def _cache_key(path: Path, extra: str = "") -> str:
    digest = _file_hash(path)
    return f"{digest}_{extra}"


def _cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def get_cached(path: Path, extra: str = "", ttl: int = 3600) -> Optional[str]:
    _ensure_cache_dir()
    key = _cache_key(path, extra)
    cp = _cache_path(key)
    if not cp.exists():
        return None
    try:
        data = json.loads(cp.read_text(encoding="utf-8"))
        if time.time() - data["timestamp"] > ttl:
            cp.unlink(missing_ok=True)
            return None
        logger.debug("Cache hit: {}", key)
        return data["text"]
    except Exception:
        cp.unlink(missing_ok=True)
        return None


def set_cache(path: Path, text: str, extra: str = "") -> None:
    _ensure_cache_dir()
    key = _cache_key(path, extra)
    cp = _cache_path(key)
    try:
        data = {"timestamp": time.time(), "text": text}
        cp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        logger.debug("Cache set: {}", key)
    except Exception as e:
        logger.warning("Falha ao salvar cache: {}", e)


def clear_cache() -> int:
    _ensure_cache_dir()
    count = 0
    for f in CACHE_DIR.iterdir():
        if f.suffix == ".json":
            f.unlink()
            count += 1
    logger.info("Cache limpo: {} arquivos removidos", count)
    return count
