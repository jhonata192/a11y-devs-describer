import tempfile
from pathlib import Path

from aiogram import Router, F
from aiogram.types import FSInputFile, Message, Document, PhotoSize

from bot.services.file_service import download_file
from bot.agente_mestre import process
from bot.utils.logger import logger
from bot.utils.validators import validate_file
from bot.exporters.txt_exporter import export_txt
from bot.exporters.docx_exporter import export_docx
from bot.exporters.pdf_exporter import export_pdf
from config.settings import settings

router = Router()

OUTPUT_DIR = settings.temp_dir / "output"


@router.message(F.document)
async def handle_document(message: Message) -> None:
    document: Document | None = message.document
    if document is None:
        return

    filename = document.file_name or "documento"
    file_size = document.file_size or 0

    valid, error_msg = validate_file(filename, file_size)
    if not valid:
        await message.answer(error_msg)
        return

    status = await message.answer("📄 Arquivo recebido!")
    await process_file(message, document.file_id, filename, status)


@router.message(F.photo)
async def handle_photo(message: Message) -> None:
    photo: PhotoSize | None = message.photo[-1] if message.photo else None
    if photo is None:
        return

    status = await message.answer("📷 Foto recebida!")
    await process_file(message, photo.file_id, "imagem.png", status)


async def process_file(
    message: Message,
    file_id: str,
    filename: str,
    status: Message,
    mode: str = "normal",
) -> None:
    with tempfile.TemporaryDirectory(dir=settings.temp_dir) as tmpdir:
        try:
            input_path = Path(tmpdir) / filename

            await status.edit_text("⬇️ Baixando arquivo...")
            await download_file(message.bot, file_id, input_path)

            async def atualizar_status(msg: str) -> None:
                try:
                    await status.edit_text(msg)
                except Exception:
                    pass

            extracted_text = await process(input_path, status_callback=atualizar_status, mode=mode)

            await status.edit_text("✅ Conteudo extraido com sucesso! Preparando exportacao...")

            await status.edit_text("📝 Gerando versao acessivel...")

            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

            base_name = Path(filename).stem
            txt_path = OUTPUT_DIR / f"{base_name}.txt"
            docx_path = OUTPUT_DIR / f"{base_name}.docx"
            pdf_path = OUTPUT_DIR / f"{base_name}.pdf"

            export_txt(extracted_text, txt_path)
            export_docx(extracted_text, docx_path, filename)
            export_pdf(extracted_text, pdf_path, filename)

            await status.edit_text("📤 Enviando arquivos...")

            caption = "Versao acessivel gerada."

            for out_path in [txt_path, docx_path, pdf_path]:
                if out_path.exists():
                    await message.answer_document(
                        document=FSInputFile(out_path),
                        caption=caption,
                    )

            await status.edit_text("✅ Conversao concluida! Arquivos gerados em TXT, DOCX e PDF.")

        except Exception:
            logger.exception("Erro ao processar arquivo")
            await status.edit_text(
                "❌ Erro ao processar o arquivo. Tente novamente mais tarde."
            )
