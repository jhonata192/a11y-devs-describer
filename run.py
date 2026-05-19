#!/usr/bin/env python3
import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

from bot.main import start_polling
from bot.services.opencode_launcher import ensure_opencode_running
from bot.utils.logger import setup_logger, logger
from config.settings import settings


async def startup():
    setup_logger()

    if not settings.bot_token_valid:
        logger.critical("BOT_TOKEN nao configurado")
        sys.exit(1)

    await ensure_opencode_running()

    logger.info("Iniciando bot...")
    await start_polling()


if __name__ == "__main__":
    try:
        asyncio.run(startup())
    except KeyboardInterrupt:
        logger.info("Bot interrompido pelo usuario")
    except Exception:
        logger.exception("Erro fatal no bot")
        sys.exit(1)
