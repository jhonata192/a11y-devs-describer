import shutil
import asyncio
import time
from pathlib import Path

from bot.utils.logger import logger
from config.settings import settings


CLEANUP_INTERVAL = 3600
FILE_MAX_AGE = 1800


async def periodic_cleanup() -> None:
    while True:
        try:
            _clean_temp_directory()
        except Exception:
            logger.exception("Erro na limpeza periódica")
        await asyncio.sleep(CLEANUP_INTERVAL)


def _clean_temp_directory() -> None:
    temp_dir = settings.temp_dir
    if not temp_dir.exists():
        return

    now = time.time()
    for item in temp_dir.iterdir():
        if item.is_file():
            mtime = item.stat().st_mtime
            if (now - mtime) > FILE_MAX_AGE:
                item.unlink()
                logger.debug("Arquivo temporário removido: {}", item.name)
        elif item.is_dir() and item.name != "output":
            shutil.rmtree(item, ignore_errors=True)
            logger.debug("Diretório temporário removido: {}", item.name)
