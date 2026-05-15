import json
import base64
import io
from pathlib import Path

import pytest
import respx
from httpx import Response
from PIL import Image

from bot.agents.base import BaseAgent
from bot.agents.descritor_visual import DescritorVisual
from bot.agents.tradutor import Tradutor
from bot.agents.router_ia import RouterIA
from bot.agents.pre_analise import PreAnalise
from bot.agents.policies import aplicar_politicas


def _valid_image_b64() -> str:
    img = Image.new("RGB", (10, 10), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


@pytest.fixture
def mock_ollama():
    with respx.mock as mock:
        yield mock


@pytest.mark.asyncio
async def test_base_agent_call(mock_ollama):
    route = mock_ollama.post("http://localhost:11434/api/generate").respond(
        json={"response": "resposta simulada", "eval_count": 10}
    )

    agent = BaseAgent(model="test-model", prompt="test prompt")
    result = await agent.executar("entrada")

    assert route.called
    assert result == "resposta simulada"
    call_body = json.loads(route.calls[0].request.content)
    assert call_body["model"] == "test-model"
    assert call_body["prompt"] == "test prompt\n\nTexto: entrada"


@pytest.mark.asyncio
async def test_base_agent_with_image(mock_ollama):
    route = mock_ollama.post("http://localhost:11434/api/generate").respond(
        json={"response": "descricao visual simulada", "eval_count": 20}
    )

    agent = BaseAgent(model="test-model", prompt="test prompt")
    img_b64 = _valid_image_b64()
    result = await agent.executar(img_b64, is_image=True)

    assert route.called
    call_body = json.loads(route.calls[0].request.content)
    assert "images" in call_body
    assert len(call_body["images"]) == 1
    assert isinstance(call_body["images"][0], str)


@pytest.mark.asyncio
async def test_tradutor_clean_with_preamble(mock_ollama):
    mock_ollama.post("http://localhost:11434/api/generate").respond(
        json={"response": "Aqui está a tradução:\nOlá mundo", "eval_count": 5}
    )

    tradutor = Tradutor()
    result = await tradutor.executar("Hello world")

    assert result == "Olá mundo"


@pytest.mark.asyncio
async def test_router_ia_parse_valid_json(mock_ollama):
    valid_plan = json.dumps({
        "pipeline": "detailed",
        "steps": ["image_description", "translation"],
        "detail_level": "alto",
        "priority": "quality",
    })
    mock_ollama.post("http://localhost:11434/api/generate").respond(
        json={"response": valid_plan}
    )

    router = RouterIA()
    metadata = {"tipo": "pdf", "paginas": 5, "texto_embutido": False}
    plan = await router.rotear(metadata)

    assert plan["pipeline"] == "detailed"
    assert plan["detail_level"] == "alto"
    assert "translation" in plan["steps"]


@pytest.mark.asyncio
async def test_router_ia_fallback_on_invalid_json(mock_ollama):
    mock_ollama.post("http://localhost:11434/api/generate").respond(
        json={"response": "invalid json response"}
    )

    router = RouterIA()
    metadata = {"tipo": "imagem", "largura": 800, "altura": 600}
    plan = await router.rotear(metadata)

    assert plan["pipeline"] == "simple"
    assert "translation" in plan["steps"]


class TestPolicies:
    def test_force_image_description_for_pdf_without_text(self):
        plan = {"pipeline": "simple", "steps": ["translation"], "detail_level": "baixo", "priority": "speed"}
        metadata = {"tipo": "pdf", "texto_embutido": False}
        result = aplicar_politicas(plan, metadata)
        assert "image_description" in result["steps"]
        assert result["detail_level"] != "baixo"

    def test_always_has_translation(self):
        plan = {"pipeline": "simple", "steps": ["image_description"], "detail_level": "medio", "priority": "speed"}
        metadata = {"tipo": "imagem"}
        result = aplicar_politicas(plan, metadata)
        assert "translation" in result["steps"]

    def test_preserves_valid_plan(self):
        plan = {"pipeline": "detailed", "steps": ["image_description", "text_extraction", "translation"], "detail_level": "alto", "priority": "quality"}
        metadata = {"tipo": "pdf", "texto_embutido": False}
        result = aplicar_politicas(plan, metadata)
        assert result["pipeline"] == "detailed"
        assert result["detail_level"] == "alto"


class TestPreAnalise:
    def test_image_analysis(self, tmp_path):
        img_path = tmp_path / "test.png"
        Image.new("RGB", (100, 200), color="red").save(img_path)

        pre = PreAnalise(img_path)
        import asyncio
        data = asyncio.run(pre.analisar())
        assert data["tipo"] == "imagem"
        assert data["largura"] == 100
        assert data["altura"] == 200

    def test_pdf_without_text_analysis(self, tmp_path):
        import fitz
        pdf_path = tmp_path / "empty.pdf"
        doc = fitz.open()
        doc.insert_page(-1, width=300, height=400)
        doc.save(str(pdf_path))
        doc.close()

        pre = PreAnalise(pdf_path)
        import asyncio
        data = asyncio.run(pre.analisar())
        assert data["tipo"] == "pdf"
        assert data["texto_embutido"] is False
