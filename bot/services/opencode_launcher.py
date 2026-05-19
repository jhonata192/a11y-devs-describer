import asyncio
import sys

import httpx

from bot.utils.logger import logger
from config.settings import settings


async def is_running() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.opencode_url}/global/health")
            return resp.status_code == 200
    except Exception:
        return False


async def start_serve() -> asyncio.subprocess.Process:
    logger.info("Starting opencode serve...")
    process = await asyncio.create_subprocess_exec(
        "opencode.cmd", "serve",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    logger.info("opencode serve started (pid={})", process.pid)
    return process


async def wait_for_ready(max_retries: int = 10, interval: float = 2.0) -> bool:
    for attempt in range(1, max_retries + 1):
        if await is_running():
            logger.info("OpenCode serve is ready (attempt {}/{})", attempt, max_retries)
            return True
        logger.info("Waiting for OpenCode serve... ({}/{})", attempt, max_retries)
        await asyncio.sleep(interval)
    return False


async def ensure_opencode_running() -> None:
    if await is_running():
        logger.info("OpenCode serve already running at {}", settings.opencode_url)
        return

    await start_serve()

    if not await wait_for_ready():
        logger.critical("Failed to start OpenCode serve at {}", settings.opencode_url)
        sys.exit(1)
