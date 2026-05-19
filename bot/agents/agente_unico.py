import io
import time
from pathlib import Path
from typing import Callable, Coroutine

from PIL import Image

from bot.clients.opencode import client as opencode_client
from bot.utils.image_converter import convert_pdf_to_png
from bot.utils.logger import logger
from bot.utils.pdf_splitter import split_pdf
from config.settings import settings

SYSTEM_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompt.txt"


def _load_system_prompt() -> str:
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    logger.warning("Prompt file not found at {}, using fallback", SYSTEM_PROMPT_PATH)
    return (
        "Voce e um sistema de acessibilidade digital. Converta as imagens recebidas "
        "em texto acessivel para leitores de tela em portugues brasileiro. "
        "Descreva elementos visuais e extraia todo o texto presente."
    )


def _compress_to_jpg(image_bytes: bytes, max_width: int = None, quality: int = None) -> bytes:
    max_width = max_width or settings.max_page_width
    quality = quality or settings.jpg_quality

    img = Image.open(io.BytesIO(image_bytes))

    if img.mode in ("RGBA", "P", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    w, h = img.size
    if w > max_width:
        ratio = max_width / w
        new_h = int(h * ratio)
        img = img.resize((max_width, new_h), Image.LANCZOS)

    output = io.BytesIO()
    img.save(output, format="JPEG", quality=quality, optimize=True)
    return output.getvalue()


def _image_to_jpg(file_path: Path, tmpdir: Path) -> Path:
    with open(file_path, "rb") as f:
        img_bytes = f.read()

    jpg_bytes = _compress_to_jpg(img_bytes)
    jpg_path = tmpdir / "imagem.jpg"
    jpg_path.write_bytes(jpg_bytes)
    logger.info("Imagem convertida para JPG: {} -> {} bytes", len(img_bytes), len(jpg_bytes))
    return jpg_path


class AgenteUnico:
    """Agente unico que processa PDF/imagem pagina por pagina via OpenCode."""

    def __init__(self):
        self.system_prompt = _load_system_prompt()

    async def executar(
        self,
        file_path: Path,
        tmpdir: Path,
        status_callback: Callable[[str], Coroutine] | None = None,
    ) -> str:
        ext = file_path.suffix.lower()
        is_pdf = ext == ".pdf"

        if is_pdf:
            if status_callback:
                await status_callback("📄 Separando PDF em paginas...")
            page_pdfs = split_pdf(file_path, tmpdir, settings.max_pages)
        else:
            if status_callback:
                await status_callback("🖼️ Preparando imagem...")
            page_pdfs = [file_path]

        total_pages = len(page_pdfs)
        if total_pages == 0:
            raise RuntimeError("Nenhuma pagina gerada a partir do arquivo")

        logger.info("Processando {} pagina(s) para {}", total_pages, file_path.name)

        results = []
        for i, page_path in enumerate(page_pdfs):
            page_num = i + 1

            if status_callback:
                label = f"📷 Processando pagina {page_num} de {total_pages}..."
                await status_callback(label)

            try:
                if is_pdf:
                    logger.debug("[pag {}] convert_pdf_to_png: {}", page_num, page_path)
                    png_bytes = convert_pdf_to_png(page_path, settings.pdf_split_dpi)
                    logger.debug("[pag {}] PNG gerado: {} bytes", page_num, len(png_bytes))
                else:
                    logger.debug("[pag {}] lendo imagem: {}", page_num, page_path)
                    with open(page_path, "rb") as f:
                        raw_bytes = f.read()
                    logger.debug("[pag {}] imagem lida: {} bytes", page_num, len(raw_bytes))
                    png_bytes = raw_bytes

                logger.debug("[pag {}] comprimindo para JPG...", page_num)
                jpg_bytes = _compress_to_jpg(png_bytes)
                logger.debug("[pag {}] JPG comprimido: {} bytes", page_num, len(jpg_bytes))

                logger.info("Enviando pagina {} para OpenCode ({} bytes)", page_num, len(jpg_bytes))

                page_prompt = self.system_prompt
                if is_pdf:
                    page_prompt += f"\n\nEste e o documento de {total_pages} paginas. Voce esta processando a pagina {page_num} de {total_pages}."

                logger.debug("[pag {}] chamando opencode_client.send_message()", page_num)
                response = await opencode_client.send_message(text=page_prompt, images=[jpg_bytes])
                logger.debug("[pag {}] resposta recebida: {} chars", page_num, len(response))
            except UnicodeDecodeError as e:
                import traceback
                tb = traceback.format_exc()
                logger.critical(
                    "[pag {}] UnicodeDecodeError: {} | Traceback:\n{}",
                    page_num, e, tb
                )
                raise
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                logger.critical(
                    "[pag {}] Erro inesperado: tipo={} | msg={} | Traceback:\n{}",
                    page_num, type(e).__name__, e, tb
                )
                raise

            if not response.strip():
                logger.warning("Resposta vazia para pagina {}", page_num)
                response = f"[Pagina {page_num}: resposta vazia do modelo]"

            output_file = tmpdir / f"imagen{page_num:03d}.txt"
            output_file.write_text(response, encoding="utf-8")
            logger.info("Resposta da pagina {} salva em {}", page_num, output_file.name)

            results.append(response)

        texto_final = "\n\n".join(
            f"=== Pagina {i + 1} ===\n{r}" for i, r in enumerate(results)
        )

        logger.info(
            "AgenteUnico: {} paginas processadas, {} chars no total",
            total_pages,
            len(texto_final),
        )

        return texto_final
