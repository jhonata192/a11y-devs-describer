from aiogram import Router
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

router = Router()


class FeedbackStates(StatesGroup):
    waiting_feedback = State()


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


@router.message(Command("ocr"))
async def cmd_ocr(message: Message) -> None:
    from bot.handlers.document import user_modes
    user_modes[message.chat.id] = "ocr"
    text = (
        "📄 Modo OCR ativado!\n\n"
        "Envie um PDF ou imagem e extrairei APENAS o texto, "
        "sem descricao visual. Ideal para documentos de texto puro."
    )
    await message.answer(text)


@router.message(Command("detalhado"))
async def cmd_detailed(message: Message) -> None:
    from bot.handlers.document import user_modes
    user_modes[message.chat.id] = "detalhado"
    text = (
        "🔍 Modo Detalhado ativado!\n\n"
        "Envie um PDF ou imagem e recebera uma descricao visual "
        "completa e detalhada, priorizando qualidade sobre velocidade."
    )
    await message.answer(text)


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    from bot.agents.state_manager import state_manager
    all_tasks = state_manager.listar_tarefas()
    tasks = [t for t in all_tasks if t.get("status") in ("processing",)]
    if not tasks:
        await message.answer("Nenhuma tarefa em processamento no momento.")
        return
    lines = ["📊 **Tarefas em andamento:**"]
    for t in tasks[:5]:
        pct = t.get("progresso", 0) * 100
        status_icon = {"processing": "⏳", "done": "✅", "error": "❌", "cancelled": "🚫"}.get(t.get("status", ""), "❓")
        lines.append(
            f"{status_icon} `{t['task_id']}` - {t.get('arquivo', '?')} "
            f"- {pct:.0f}% - {t.get('etapa_atual', '')}"
        )
    await message.answer("\n".join(lines))


@router.message(Command("health"))
async def cmd_health(message: Message) -> None:
    import httpx
    from config.settings import settings

    checks = []

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{settings.opencode_url}/global/health")
            if r.status_code == 200:
                data = r.json()
                version = data.get("version", "unknown")
                checks.append(f"✅ OpenCode: online (v{version})")
            else:
                checks.append(f"⚠️ OpenCode: resposta inesperada ({r.status_code})")
    except Exception as e:
        checks.append(f"❌ OpenCode: offline ({e})")

    checks.append(f"🤖 Modelo: {settings.opencode_model}")

    temp_dir = settings.temp_dir
    if temp_dir.exists():
        checks.append(f"✅ Temp dir: ok")
    else:
        checks.append(f"⚠️ Temp dir: inexistente")

    try:
        import shutil
        usage = shutil.disk_usage(temp_dir.anchor or "/")
        free_gb = usage.free / (1024**3)
        checks.append(f"💾 Disco livre: {free_gb:.1f} GB")
    except Exception:
        pass

    await message.answer("\n".join(checks))


@router.message(Command("cancelar"))
async def cmd_cancel(message: Message) -> None:
    from bot.agents.state_manager import state_manager
    tasks = state_manager.listar_tarefas_processing()
    if not tasks:
        await message.answer("Nenhuma tarefa em processamento para cancelar.")
        return
    for t in tasks:
        state_manager.cancelar(t["task_id"])
    await message.answer(f"✅ {len(tasks)} tarefa(s) cancelada(s).")


@router.message(Command("feedback"))
async def cmd_feedback(message: Message, state: FSMContext) -> None:
    text = (
        "📝 **Enviar Feedback**\n\n"
        "Digite sua opiniao sobre a qualidade do processamento, "
        "sugestoes de melhoria ou problemas encontrados.\n\n"
        "Exemplo:\n"
        "'A descricao da imagem ficou muito boa, mas o texto extraido "
        "teve alguns erros.'\n\n"
        "Seu feedback e importante para melhorarmos o bot!"
    )
    await state.set_state(FeedbackStates.waiting_feedback)
    await message.answer(text)


@router.message(StateFilter(FeedbackStates.waiting_feedback))
async def handle_feedback_text(message: Message, state: FSMContext) -> None:
    from bot.utils.logger import logger
    from datetime import datetime

    feedback = message.text or ""
    user = message.from_user
    user_info = f"{user.username or user.id}" if user else "unknown"

    logger.info("FEEDBACK de {}: {}", user_info, feedback)

    from pathlib import Path
    from config.settings import settings
    feedback_file = settings.temp_dir / "feedback.txt"
    feedback_file.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()
    with open(feedback_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {user_info}: {feedback}\n")

    await state.clear()
    await message.answer("✅ Feedback registrado! Muito obrigado pela contribuicao.")
