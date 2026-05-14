import re

from bot.agents.base import BaseAgent
from config.settings import settings


TRANSLATE_PROMPT = """\
Traduza o texto abaixo para o português brasileiro. \
Preserve nomes próprios, marcas, números e códigos \
exatamente como estão. Retorne APENAS a tradução.\
"""


class Tradutor(BaseAgent):
    def __init__(self):
        super().__init__(
            model=settings.translation_model,
            prompt=TRANSLATE_PROMPT,
            keep_alive=0,
        )

    async def executar(self, entrada: str, is_image: bool = False) -> str:
        result = await super().executar(entrada, is_image=False)
        if result:
            result = _clean_translation(result)
        return result


def _clean_translation(text: str) -> str:
    lines = text.strip().splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if re.match(
            r"^(aqui está|aqui está a tradução|tradução|com certeza|claro|aqui vai|aqui está o texto)",
            stripped,
            re.IGNORECASE,
        ):
            continue
        cleaned.append(line)
    result = "\n".join(cleaned).strip()
    return result if result else text.strip()
