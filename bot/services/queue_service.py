import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Coroutine

from bot.utils.logger import logger


@dataclass
class QueueItem:
    user_id: int
    chat_id: int
    file_path: Path
    mode: str
    status_callback: Callable[[str], Coroutine] | None = None
    task_id: str = ""
    added_at: float = field(default_factory=time.time)


class ProcessingQueue:
    def __init__(self, max_concurrent: int = 1):
        self._queue: deque[QueueItem] = deque()
        self._processing: dict[str, QueueItem] = {}
        self._max_concurrent = max_concurrent
        self._lock = asyncio.Lock()
        self._cancel_events: dict[str, asyncio.Event] = {}

    async def enqueue(self, item: QueueItem) -> str:
        async with self._lock:
            self._queue.append(item)
            logger.info(
                "Fila: {} enfileirado (fila: {})",
                item.file_path.name,
                len(self._queue),
            )
        return item.task_id

    async def process_next(self, processor: Callable) -> None:
        async with self._lock:
            if len(self._processing) >= self._max_concurrent:
                return
            if not self._queue:
                return
            item = self._queue.popleft()
            self._processing[item.task_id] = item

        if item.status_callback:
            pos = self._queue_position(item.task_id)
            if pos > 0:
                await item.status_callback(f"⏳ Voce esta na fila. Posicao: {pos}")

    def _queue_position(self, task_id: str) -> int:
        for i, item in enumerate(self._queue):
            if item.task_id == task_id:
                return i + 1
        return 0

    def cancelar(self, task_id: str) -> bool:
        self._queue = deque(
            item for item in self._queue if item.task_id != task_id
        )
        if task_id in self._processing:
            del self._processing[task_id]
            return True
        return False

    def is_processing(self, task_id: str) -> bool:
        return task_id in self._processing

    def fila_tamanho(self) -> int:
        return len(self._queue)

    def em_processamento(self) -> int:
        return len(self._processing)

    async def marcar_concluido(self, task_id: str) -> None:
        async with self._lock:
            self._processing.pop(task_id, None)


processing_queue = ProcessingQueue(max_concurrent=1)
