import asyncio
from pathlib import Path

import pytesseract
from bot.utils.logger import logger

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class OCRAgent:
    def __init__(self, lang: str = "por"):
        self.lang = lang

    async def executar(self, file_path: Path, dpi: int = 300) -> str:
        ext = file_path.suffix.lower()
        try:
            if ext == ".pdf":
                return await self._ocr_pdf(file_path, dpi)
            return await self._ocr_imagem(file_path)
        except Exception as e:
            logger.error("Erro no OCR para {}: {}: {}", file_path.name, type(e).__name__, e)
            return ""

    async def _ocr_imagem(self, file_path: Path) -> str:
        from PIL import Image

        logger.info("OCR iniciado: {} (async)", file_path.name)
        loop = asyncio.get_running_loop()

        def _sync_ocr():
            with Image.open(file_path) as img:
                return pytesseract.image_to_string(img, lang=self.lang).strip()

        text = await loop.run_in_executor(None, _sync_ocr)
        logger.info("OCR concluido: {} caracteres extraidos", len(text))
        return text

    async def _ocr_pdf(self, file_path: Path, dpi: int) -> str:
        import fitz
        from PIL import Image

        logger.info("OCR PDF iniciado: {} (dpi={})", file_path.name, dpi)
        doc = fitz.open(file_path)
        try:
            total = len(doc)
            from config.settings import settings

            pages_to_process = min(total, settings.max_pages)
            texts = []
            loop = asyncio.get_running_loop()

            for i in range(pages_to_process):
                page = doc[i]
                pix = page.get_pixmap(dpi=dpi)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                def _ocr_page(img_copy=img):
                    return pytesseract.image_to_string(img_copy, lang=self.lang).strip()

                page_text = await loop.run_in_executor(None, _ocr_page)
                if page_text:
                    texts.append(f"--- Pagina {i + 1} ---\n{page_text}")
                logger.info("OCR pagina {}/{} processada", i + 1, pages_to_process)

            return "\n\n".join(texts) if texts else ""
        finally:
            doc.close()
