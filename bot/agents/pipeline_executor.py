import asyncio
import base64
from pathlib import Path
from typing import Callable, Coroutine

from bot.agents.descritor_visual import DescritorVisual
from bot.agents.tradutor import Tradutor
from bot.utils.logger import logger
from config.settings import settings


class PipelineExecutor:
    def __init__(self):
        self.descritor = DescritorVisual()
        self.tradutor = Tradutor()

    async def executar(
        self,
        plan: dict,
        file_path: Path,
        metadata: dict,
        status_callback: Callable[[str], Coroutine] | None = None,
    ) -> str:
        steps = plan.get("steps", [])
        detail = plan.get("detail_level", "medio")

        logger.info(
            "Executando pipeline: {} ({} etapas, detalhe: {})",
            plan.get("pipeline", "?"),
            len(steps),
            detail,
        )

        result = await self._executar_steps(steps, file_path, metadata, detail, status_callback)
        return result

    async def _executar_steps(
        self,
        steps: list,
        file_path: Path,
        metadata: dict,
        detail: str,
        status_callback: Callable[[str], Coroutine] | None = None,
    ) -> str:
        ext = file_path.suffix.lower()
        is_pdf = ext == ".pdf"

        descricao_visual = ""
        texto_extraido = ""

        if "image_description" in steps:
            if status_callback:
                await status_callback("👁️ Descrevendo elementos visuais...")
            try:
                if is_pdf:
                    descricao_visual = await asyncio.wait_for(
                        self._descrever_pdf(file_path), timeout=3600
                    )
                else:
                    descricao_visual = await asyncio.wait_for(
                        self._descrever_imagem(file_path), timeout=3600
                    )
            except asyncio.TimeoutError:
                logger.warning("Timeout na descricao visual para {}", file_path.name)
                descricao_visual = ""

        if "text_extraction" in steps:
            if status_callback:
                await status_callback("📖 Extraindo texto...")
            try:
                if is_pdf:
                    texto_extraido = await asyncio.wait_for(
                        self._extrair_texto_pdf(file_path), timeout=3600
                    )
                else:
                    texto_extraido = await asyncio.wait_for(
                        self._extrair_texto_imagem(file_path), timeout=3600
                    )
            except asyncio.TimeoutError:
                logger.warning("Timeout na extracao de texto para {}", file_path.name)
                texto_extraido = ""

        if not descricao_visual.strip() and not texto_extraido.strip():
            return ""

        combined = self._combinar_resultados(descricao_visual, texto_extraido, metadata)

        if "translation" in steps:
            if status_callback:
                await status_callback("🌐 Traduzindo para portugues...")
            combined = await self.tradutor.executar(combined)

        return combined

    def _combinar_resultados(
        self, descricao: str, texto: str, metadata: dict
    ) -> str:
        parts = []
        if descricao.strip():
            parts.append(descricao.strip())
        if texto.strip():
            parts.append(f"\n---\n\n**Texto extraido:**\n{texto.strip()}")
        if not parts:
            if metadata.get("texto_embutido"):
                parts.append(metadata.get("texto_extraido", ""))
        return "\n\n".join(parts)

    async def _descrever_pdf(self, file_path: Path) -> str:
        import fitz

        doc = fitz.open(file_path)
        try:
            total = len(doc)
            pages_to_process = min(total, settings.max_pages)
            texts = []
            for i in range(pages_to_process):
                page = doc[i]
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                page_text = await self.descritor.executar(img_b64, is_image=True)
                if page_text:
                    texts.append(f"--- Pagina {i + 1} ---\n{page_text}")
                logger.info("Descricao visual pagina {}/{}", i + 1, pages_to_process)
            return "\n\n".join(texts) if texts else ""
        finally:
            doc.close()

    async def _descrever_imagem(self, file_path: Path) -> str:
        with open(file_path, "rb") as f:
            img_bytes = f.read()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        return await self.descritor.executar(img_b64, is_image=True)

    async def _extrair_texto_pdf(self, file_path: Path) -> str:
        import fitz

        doc = fitz.open(file_path)
        try:
            total = len(doc)
            pages_to_process = min(total, settings.max_pages)
            texts = []
            for i in range(pages_to_process):
                page = doc[i]
                pix = page.get_pixmap(dpi=200)
                img_bytes = pix.tobytes("png")
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                page_text = await self.descritor.extrair_texto(img_b64)
                if page_text:
                    texts.append(f"--- Pagina {i + 1} ---\n{page_text}")
                logger.info("Extracao de texto pagina {}/{}", i + 1, pages_to_process)
            return "\n\n".join(texts) if texts else ""
        finally:
            doc.close()

    async def _extrair_texto_imagem(self, file_path: Path) -> str:
        with open(file_path, "rb") as f:
            img_bytes = f.read()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        return await self.descritor.extrair_texto(img_b64)
