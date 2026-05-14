from pathlib import Path

from bot.utils.logger import logger


def export_txt(text: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    logger.debug("TXT exportado: {}", output_path)
    return output_path
