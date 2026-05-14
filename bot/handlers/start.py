from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text = (
        "Olá! Envie um PDF, imagem ou documento escaneado."
        "\n\n"
        "Enviarei de volta uma versão acessível para leitores de tela."
        "\n\n"
        "Formatos aceitos: PDF, PNG, JPG, TIFF, BMP, WEBP"
    )
    await message.answer(text)


@router.message(Command("ajuda"))
@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = (
        "Comandos disponíveis:"
        "\n/start - Iniciar o bot"
        "\n/ajuda  - Mostrar esta mensagem"
        "\n/formatos - Listar formatos suportados"
        "\n\n"
        "Basta enviar um arquivo que eu processo automaticamente."
    )
    await message.answer(text)


@router.message(Command("formatos"))
async def cmd_formats(message: Message) -> None:
    text = (
        "Formatos de entrada aceitos:"
        "\n• PDF (escaneado ou digital)"
        "\n• PNG, JPG, JPEG"
        "\n• TIFF, TIF"
        "\n• BMP"
        "\n• WEBP"
        "\n\n"
        "Formatos de saída disponíveis:"
        "\n• TXT estruturado"
        "\n• DOCX acessível"
        "\n• HTML semântico"
        "\n• Markdown"
        "\n• PDF pesquisável"
    )
    await message.answer(text)
