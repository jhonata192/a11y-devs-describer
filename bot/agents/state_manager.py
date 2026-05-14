import time
import uuid
from pathlib import Path


class StateManager:
    def __init__(self):
        self._tasks: dict[str, dict] = {}

    def criar_tarefa(self, file_path: Path) -> str:
        task_id = str(uuid.uuid4())[:8]
        self._tasks[task_id] = {
            "task_id": task_id,
            "arquivo": file_path.name,
            "status": "processing",
            "progresso": 0.0,
            "etapa_atual": "",
            "erros": [],
            "resultado": None,
            "inicio": time.time(),
            "fim": None,
        }
        return task_id

    def atualizar(
        self,
        task_id: str,
        progresso: float | None = None,
        etapa: str | None = None,
        status: str | None = None,
        erro: str | None = None,
        resultado: str | None = None,
    ) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return
        if progresso is not None:
            task["progresso"] = progresso
        if etapa is not None:
            task["etapa_atual"] = etapa
        if status is not None:
            task["status"] = status
        if erro is not None:
            task["erros"].append(erro)
        if resultado is not None:
            task["resultado"] = resultado
        if status in ("done", "error"):
            task["fim"] = time.time()

    def obter(self, task_id: str) -> dict | None:
        return self._tasks.get(task_id)

    def finalizar(self, task_id: str, resultado: str) -> None:
        self.atualizar(task_id, progresso=1.0, status="done", resultado=resultado)

    def errar(self, task_id: str, erro: str) -> None:
        self.atualizar(task_id, status="error", erro=erro)


state_manager = StateManager()
