import tempfile
from pathlib import Path

import pytest
from PIL import Image

from bot.agents.pre_analise import PreAnalise


@pytest.mark.asyncio
async def test_pre_analise_imagem_png():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = Path(f.name)
        Image.new("RGB", (800, 600), color="red").save(f)

    pre = PreAnalise(path)
    result = await pre.analisar()
    path.unlink()

    assert result["tipo"] == "imagem"
    assert result["formato"] == "png"
    assert result["largura"] == 800
    assert result["altura"] == 600
    assert result["modo"] == "RGB"


@pytest.mark.asyncio
async def test_pre_analise_imagem_jpg():
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        path = Path(f.name)
        Image.new("RGB", (1920, 1080), color="blue").save(f, "JPEG")

    pre = PreAnalise(path)
    result = await pre.analisar()
    path.unlink()

    assert result["tipo"] == "imagem"
    assert result["largura"] == 1920
    assert result["altura"] == 1080
    assert result["proporcao"] == "16:9"


@pytest.mark.asyncio
async def test_pre_analise_pdf_com_texto():
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 10, text="Conteudo testavel", new_x="LMARGIN", new_y="NEXT")
    pdf_bytes = pdf.output()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        path = Path(f.name)
        f.write(pdf_bytes)

    pre = PreAnalise(path)
    result = await pre.analisar()
    path.unlink()

    assert result["tipo"] == "pdf"
    assert result["paginas"] >= 1
    assert result["texto_embutido"] is True
    assert result["total_chars"] > 0
    assert result["densidade_visual"] == "baixa"


@pytest.mark.asyncio
async def test_pre_analise_pdf_sem_texto_detectado():
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    _ = page
    pdf_bytes = doc.tobytes()
    doc.close()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        path = Path(f.name)
        f.write(pdf_bytes)

    pre = PreAnalise(path)
    result = await pre.analisar()
    path.unlink()

    assert result["tipo"] == "pdf"
    assert result["texto_embutido"] is False
    assert result["total_chars"] == 0
