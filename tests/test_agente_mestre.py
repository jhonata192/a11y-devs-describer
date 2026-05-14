import tempfile
from pathlib import Path

from bot.agents.policies import aplicar_politicas
from bot.agents.state_manager import StateManager


def test_policies_force_image_description_for_pdf_sem_texto():
    plan = {"pipeline": "simple", "steps": ["translation"], "detail_level": "baixo"}
    meta = {"tipo": "pdf", "texto_embutido": False, "paginas": 5}
    result = aplicar_politicas(plan, meta)
    assert "image_description" in result["steps"]
    assert result["detail_level"] in ("medio", "alto")


def test_policies_does_not_add_unnecessary_image_description():
    plan = {"pipeline": "simple", "steps": ["translation"], "detail_level": "baixo"}
    meta = {"tipo": "pdf", "texto_embutido": True, "paginas": 5}
    result = aplicar_politicas(plan, meta)
    assert "image_description" not in result["steps"]


def test_policies_always_adds_translation():
    plan = {"pipeline": "simple", "steps": ["image_description"], "detail_level": "medio"}
    meta = {"tipo": "imagem", "largura": 100, "altura": 100}
    result = aplicar_politicas(plan, meta)
    assert "translation" in result["steps"]


def test_policies_sanitizes_invalid_detail_level():
    plan = {"pipeline": "simple", "steps": ["translation"], "detail_level": "extremo"}
    meta = {"tipo": "imagem", "largura": 100, "altura": 100}
    result = aplicar_politicas(plan, meta)
    assert result["detail_level"] == "medio"


def test_policies_preserves_valid_detail_level():
    plan = {"pipeline": "simple", "steps": ["translation"], "detail_level": "alto"}
    meta = {"tipo": "imagem", "largura": 100, "altura": 100}
    result = aplicar_politicas(plan, meta)
    assert result["detail_level"] == "alto"


def test_state_manager_criar_tarefa():
    sm = StateManager()
    task_id = sm.criar_tarefa(Path("teste.pdf"))
    task = sm.obter(task_id)
    assert task is not None
    assert task["status"] == "processing"
    assert task["arquivo"] == "teste.pdf"
    assert task["progresso"] == 0.0


def test_state_manager_atualizar():
    sm = StateManager()
    task_id = sm.criar_tarefa(Path("teste.png"))
    sm.atualizar(task_id, progresso=0.5, etapa="Pré-análise")
    task = sm.obter(task_id)
    assert task["progresso"] == 0.5
    assert task["etapa_atual"] == "Pré-análise"


def test_state_manager_finalizar():
    sm = StateManager()
    task_id = sm.criar_tarefa(Path("teste.pdf"))
    sm.finalizar(task_id, "resultado final")
    task = sm.obter(task_id)
    assert task["status"] == "done"
    assert task["resultado"] == "resultado final"
    assert task["progresso"] == 1.0
    assert task["fim"] is not None


def test_state_manager_errar():
    sm = StateManager()
    task_id = sm.criar_tarefa(Path("teste.pdf"))
    sm.errar(task_id, "Falha na conexão com Ollama")
    task = sm.obter(task_id)
    assert task["status"] == "error"
    assert "Falha na conexão com Ollama" in task["erros"]


def test_state_manager_tarefa_inexistente():
    sm = StateManager()
    assert sm.obter("nao_existe") is None
    sm.atualizar("nao_existe", status="done")
    sm.finalizar("nao_existe", "x")
    sm.errar("nao_existe", "x")
