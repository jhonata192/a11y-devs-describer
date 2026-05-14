from bot.agents.descritor_visual import VISUAL_PROMPT, TEXT_EXTRACT_PROMPT


def test_visual_prompt_defined():
    assert "analisador visual especializado" in VISUAL_PROMPT
    assert "NAO transcreva o conteudo de textos" in VISUAL_PROMPT
    assert "neutralidade absoluta" in VISUAL_PROMPT


def test_text_extract_prompt_defined():
    assert "OCR avancado e extracao estruturada" in TEXT_EXTRACT_PROMPT
    assert "fidelidade absoluta ao conteudo original" in TEXT_EXTRACT_PROMPT


def test_visual_prompt_length():
    assert len(VISUAL_PROMPT) > 100
