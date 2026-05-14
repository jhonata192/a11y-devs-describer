from bot.agents.tradutor import _clean_translation


def test_clean_translation_removes_preamble():
    text = "Aqui está a tradução do texto para o português brasileiro:\n\nImagem mostra um gato."
    result = _clean_translation(text)
    assert "Imagem mostra um gato" in result
    assert "Aqui está" not in result


def test_clean_translation_keeps_clean_text():
    text = "Imagem mostra um cachorro."
    result = _clean_translation(text)
    assert result == "Imagem mostra um cachorro."


def test_clean_translation_multiline():
    text = "Tradução:\nLinha 1\nLinha 2"
    result = _clean_translation(text)
    assert "Linha 1" in result
    assert "Tradução" not in result
