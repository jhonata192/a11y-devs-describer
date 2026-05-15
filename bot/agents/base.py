import base64

import httpx

from bot.utils.image_utils import compress_image
from bot.utils.logger import logger
from config.settings import settings


class BaseAgent:
    def __init__(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        keep_alive: int | str = 0,
    ):
        self.model = model
        self.prompt = prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.keep_alive = keep_alive

    async def executar(self, entrada: str, is_image: bool = False, prompt: str | None = None) -> str:
        url = f"{settings.ollama_url}/api/generate"
        prompt_final = prompt if prompt else self.prompt
        payload = {
            "model": self.model,
            "prompt": prompt_final,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }
        if is_image:
            img_bytes = base64.b64decode(entrada)
            compressed = compress_image(img_bytes)
            payload["images"] = [base64.b64encode(compressed).decode("utf-8")]
        else:
            payload["prompt"] = f"{prompt_final}\n\nTexto: {entrada}"

        async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            result = data.get("response", "")
            if result.strip():
                logger.info(
                    "{}: modelo respondeu ({} tokens)",
                    self.__class__.__name__,
                    data.get("eval_count", 0),
                )
            return result.strip()
