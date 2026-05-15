from bot.agents.base import BaseAgent
from config.settings import settings

SUMMARIZE_PROMPT = """\
Summarize the following text in Brazilian Portuguese. Create a concise executive summary
with the main topics covered. Focus on the key information, data, and conclusions.
Return the summary in clear, well-structured paragraphs.

Text to summarize:
{text}
"""


class Summarizer(BaseAgent):
    def __init__(self):
        super().__init__(
            model=settings.translation_model,
            prompt=SUMMARIZE_PROMPT,
            keep_alive=0,
        )

    async def executar(self, entrada: str, is_image: bool = False) -> str:
        prompt = self.prompt.format(text=entrada)
        result = await super().executar(prompt, is_image=False)
        return result
