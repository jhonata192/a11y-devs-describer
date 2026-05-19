import asyncio
import time
from pathlib import Path
from typing import Callable, Coroutine

from bot.agents.agente_unico import AgenteUnico
from bot.agents.state_manager import TaskCancelledError, state_manager
from bot.services.cache import get_cached, set_cache
from bot.services.history_service import finalizar_conversao, registrar_conversao
from bot.services.queue_service import QueueItem, processing_queue
from bot.utils.logger import logger

agente = AgenteUnico()
CACHE_VERSION = "opencode-v1"


def _limpar_tarefas_orfas():
    try:
        from bot.services.history_service import get_connection

        conn = get_connection()
        conn.execute(
            "UPDATE conversoes SET status='error', erro='Stale: process interrupted' "
            "WHERE status='processing' AND criado_em < datetime('now', '-1 hours')"
        )
        conn.commit()
        conn.close()
        logger.info("Tarefas orfas limpas")
    except Exception as e:
        logger.warning("Falha ao limpar tarefas orfas: {}", e)


_limpar_tarefas_orfas()


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
        state_manager.atualizar(task_id, etapa="Preparando arquivo", progresso=0.1)
        state_manager.verificar_cancelamento(task_id)

        if status_callback:
            await status_callback("📄 Analisando arquivo...")

        state_manager.atualizar(task_id, etapa="Processando com IA", progresso=0.3)
        state_manager.verificar_cancelamento(task_id)

        resultado = await agente.executar(file_path, file_path.parent, status_callback)

        state_manager.verificar_cancelamento(task_id)
        if not resultado.strip():
            raise RuntimeError("Resposta vazia do agente")

        state_manager.finalizar(task_id, resultado)
        set_cache(file_path, resultado, CACHE_VERSION)

        finalizar_conversao(
            task_id=task_id,
            status="done",
            pipeline="opencode-unico",
            resultado_resumo=resultado[:200],
            tempo_segundos=time.time() - inicio,
        )

        if status_callback:
            await status_callback("✅ Processamento finalizado com sucesso!")
        return resultado

    except TaskCancelledError:
        logger.info("Tarefa {} cancelada pelo usuario", task_id)
        finalizar_conversao(
            task_id=task_id,
            status="cancelled",
            erro="Cancelado pelo usuario",
            tempo_segundos=time.time() - inicio,
        )
        raise

    except Exception as e:
        logger.error("Erro no pipeline: {}: {}", type(e).__name__, e)
        state_manager.errar(task_id, str(e))
        fallback = _fallback_texto_simples(file_path)
        state_manager.atualizar(task_id, resultado=fallback)
        set_cache(file_path, fallback, CACHE_VERSION)

        finalizar_conversao(
            task_id=task_id,
            status="error",
            erro=str(e),
            resultado_resumo=fallback[:200],
            tempo_segundos=time.time() - inicio,
        )

        if status_callback:
            await status_callback("❌ Nao foi possivel processar o arquivo.")
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
        if state_manager.foi_cancelada(task_id):
            await processing_queue.cancelar(task_id)
            raise TaskCancelledError(f"Tarefa {task_id} cancelada na fila")
        async with processing_queue._lock:
            if task_id in processing_queue._processing:
                break
            can_process = (
                processing_queue.em_processamento() < processing_queue._max_concurrent
                and processing_queue._queue
                and processing_queue._queue[0].task_id == task_id
            )
            if can_process:
                processing_queue._processing[task_id] = processing_queue._queue.popleft()
                break
        await asyncio.sleep(1)

    try:
        result = await process(file_path, status_callback, mode)
        return result
    finally:
        await processing_queue.marcar_concluido(task_id)


def _fallback_texto_simples(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        try:
            import fitz

            doc = fitz.open(file_path)
            texts = []
            for i in range(min(len(doc), 10)):
                text = doc[i].get_text().strip()
                if text:
                    texts.append(f"--- Pagina {i + 1} ---\n{text}")
            doc.close()
            if texts:
                return "\n\n".join(texts)
        except Exception:
            pass
    return (
        "Nao foi possivel processar o arquivo automaticamente. "
        "Tente enviar em formato diferente."
    )
