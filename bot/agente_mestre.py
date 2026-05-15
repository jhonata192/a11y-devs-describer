import asyncio
import time
from pathlib import Path
from typing import Callable, Coroutine

from bot.agents import DescritorVisual, Tradutor
from bot.agents.pipeline_executor import PipelineExecutor
from bot.agents.policies import aplicar_politicas
from bot.agents.pre_analise import PreAnalise
from bot.agents.router_ia import RouterIA
from bot.agents.state_manager import state_manager
from bot.services.cache import get_cached, set_cache
from bot.services.history_service import finalizar_conversao, registrar_conversao
from bot.services.queue_service import QueueItem, processing_queue
from bot.utils.image_utils import compress_image
from bot.utils.logger import logger

router = RouterIA()
executor = PipelineExecutor()
CACHE_VERSION = "hibrido-v4"


async def process(
    file_path: Path,
    status_callback: Callable[[str], Coroutine] | None = None,
    mode: str = "normal",
) -> str:
    cached = get_cached(file_path, CACHE_VERSION)
    if cached is not None:
        logger.info("Cache hit para {}", file_path.name)
        return cached

    task_id = state_manager.criar_tarefa(file_path)
    inicio = time.time()
    registrar_conversao(
        task_id=task_id,
        arquivo=file_path.name,
        extensao=file_path.suffix,
        tamanho_bytes=file_path.stat().st_size,
        modo=mode,
    )

    try:
        if status_callback:
            await status_callback("📄 Analisando estrutura do arquivo...")
        state_manager.atualizar(task_id, etapa="Pre-analise", progresso=0.1)
        pre = PreAnalise(file_path)
        metadata = await pre.analisar()

        if status_callback:
            await status_callback("🧠 Planejando roteamento inteligente...")
        state_manager.atualizar(task_id, etapa="Roteamento IA", progresso=0.3)
        plan = await router.rotear(metadata)
        plan = aplicar_politicas(plan, metadata)
        logger.info("Plano: {}", plan)

        if mode == "ocr":
            plan["steps"] = ["text_extraction"]
            if "translation" not in plan.get("steps", []):
                plan.setdefault("steps", []).append("translation")
        elif mode == "detalhado":
            plan["detail_level"] = "alto"
            if "summarize" not in plan.get("steps", []):
                plan.setdefault("steps", []).append("summarize")

        state_manager.atualizar(
            task_id,
            etapa=f"Executando pipeline: {plan['pipeline']}",
            progresso=0.5,
        )
        resultado = await executor.executar(plan, file_path, metadata, status_callback)

        if not resultado.strip():
            logger.warning("Pipeline vazio, tentando fallback")
            if status_callback:
                await status_callback("⚠️ Usando rota alternativa de processamento...")
            resultado = await _fallback_com_llava(file_path, status_callback)

        state_manager.finalizar(task_id, resultado)
        set_cache(file_path, resultado, CACHE_VERSION)

        finalizar_conversao(
            task_id=task_id,
            status="done",
            pipeline=plan.get("pipeline", ""),
            resultado_resumo=resultado[:200],
            tempo_segundos=time.time() - inicio,
        )

        if status_callback:
            await status_callback("✅ Processamento finalizado com sucesso!")
        return resultado

    except Exception as e:
        logger.error("Erro no pipeline: {}: {}", type(e).__name__, e)
        state_manager.errar(task_id, str(e))
        if status_callback:
            await status_callback("⚠️ Erro no pipeline principal. Tentando rota alternativa...")
        try:
            fallback = await _fallback_com_llava(file_path, status_callback)
        except Exception as e2:
            logger.error("Fallback tambem falhou: {}: {}", type(e2).__name__, e2)
            fallback = _fallback_texto_simples(file_path)
            if status_callback:
                await status_callback("❌ Nao foi possivel processar o arquivo.")
        state_manager.atualizar(task_id, resultado=fallback)
        set_cache(file_path, fallback, CACHE_VERSION)

        finalizar_conversao(
            task_id=task_id,
            status="error",
            erro=str(e),
            resultado_resumo=fallback[:200],
            tempo_segundos=time.time() - inicio,
        )
        return fallback


async def process_with_queue(
    file_path: Path,
    status_callback: Callable[[str], Coroutine] | None = None,
    user_id: int = 0,
    chat_id: int = 0,
    mode: str = "normal",
) -> str:
    task_id = state_manager.criar_tarefa(file_path)
    item = QueueItem(
        user_id=user_id,
        chat_id=chat_id,
        file_path=file_path,
        mode=mode,
        status_callback=status_callback,
        task_id=task_id,
    )

    async with processing_queue._lock:
        processing_queue._queue.append(item)

    while True:
        async with processing_queue._lock:
            if task_id in processing_queue._processing:
                break
            if (
                processing_queue.em_processamento() < processing_queue._max_concurrent
                and processing_queue._queue
                and processing_queue._queue[0].task_id == task_id
            ):
                processing_queue._processing[task_id] = processing_queue._queue.popleft()
                break
        await asyncio.sleep(1)

    result = await process(file_path, status_callback, mode)
    await processing_queue.marcar_concluido(task_id)
    return result


def _fallback_texto_simples(file_path: Path) -> str:
    return (
        "Nao foi possivel processar a imagem automaticamente. "
        "Tente enviar uma imagem mais clara ou em formato diferente."
    )


async def _fallback_com_llava(
    file_path: Path,
    status_callback: Callable[[str], Coroutine] | None = None,
) -> str:
    ext = file_path.suffix.lower()
    descricao = ""
    texto = ""

    if status_callback:
        await status_callback("👁️ Descrevendo elementos visuais...")
    try:
        if ext == ".pdf":
            descricao = await asyncio.wait_for(
                _fallback_descrever_pdf(file_path, status_callback), timeout=600
            )
        else:
            descricao = await asyncio.wait_for(
                _fallback_descrever_imagem(file_path), timeout=600
            )
    except Exception as e:
        logger.error("Erro descricao fallback: {}", e)

    if status_callback:
        await status_callback("📖 Extraindo texto...")
    try:
        texto = await asyncio.wait_for(
            _fallback_extrair_texto(file_path, status_callback), timeout=600
        )
    except Exception as e:
        logger.error("Erro extracao texto fallback: {}", e)

    parts = []
    if descricao.strip():
        parts.append(descricao.strip())
    if texto.strip():
        parts.append(f"\n---\n\n**Texto extraido:**\n{texto.strip()}")

    raw = "\n\n".join(parts)
    if not raw.strip():
        return _fallback_texto_simples(file_path)

    if status_callback:
        await status_callback("🌐 Traduzindo para portugues...")
    try:
        raw = await asyncio.wait_for(tradutor.executar(raw), timeout=120)
    except Exception as e:
        logger.error("Erro traducao fallback: {}", e)

    if status_callback:
        await status_callback("✅ Processamento finalizado!")
    return raw


async def _fallback_descrever_pdf(file_path: Path, status_callback=None) -> str:
    import base64
    import fitz

    doc = fitz.open(file_path)
    try:
        total = len(doc)
        pages_to_process = min(total, 5)
        textos = []
        for i in range(pages_to_process):
            page = doc[i]
            pix = page.get_pixmap(dpi=150)
            img_bytes = compress_image(pix.tobytes("png"))
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            if status_callback:
                await status_callback(f"👁️ Descrevendo pagina {i+1} de {pages_to_process}...")
            desc = await descritor.executar(img_b64, is_image=True)
            if desc:
                textos.append(f"--- Pagina {i + 1} ---\n{desc}")
        return "\n\n".join(textos) if textos else ""
    finally:
        doc.close()


async def _fallback_descrever_imagem(file_path: Path) -> str:
    import base64

    with open(file_path, "rb") as f:
        img_bytes = f.read()
    img_bytes = compress_image(img_bytes)
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    return await descritor.executar(img_b64, is_image=True)


async def _fallback_extrair_texto(file_path: Path, status_callback=None) -> str:
    import base64

    if file_path.suffix.lower() == ".pdf":
        return await _fallback_extrair_texto_pdf(file_path, status_callback)

    with open(file_path, "rb") as f:
        img_bytes = f.read()
    img_bytes = compress_image(img_bytes)
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    return await descritor.extrair_texto(img_b64)


async def _fallback_extrair_texto_pdf(file_path: Path, status_callback=None) -> str:
    import base64
    import fitz

    doc = fitz.open(file_path)
    try:
        total = len(doc)
        pages_to_process = min(total, 5)
        textos = []
        for i in range(pages_to_process):
            page = doc[i]
            pix = page.get_pixmap(dpi=200)
            img_bytes = compress_image(pix.tobytes("png"))
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            if status_callback:
                await status_callback(f"📖 Extraindo texto pagina {i+1} de {pages_to_process}...")
            text = await descritor.extrair_texto(img_b64)
            if text:
                textos.append(f"--- Pagina {i + 1} ---\n{text}")
        return "\n\n".join(textos) if textos else ""
    finally:
        doc.close()


descritor = DescritorVisual()
tradutor = Tradutor()
