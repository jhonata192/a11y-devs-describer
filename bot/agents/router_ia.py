import json

from bot.agents.base import BaseAgent
from config.settings import settings

ROUTER_PROMPT = """\
You are an accessibility router. Analyze the file metadata below and return a JSON \
plan describing HOW to process it for accessibility in Brazilian Portuguese.

METADATA:
{metadata}

Return ONLY valid JSON with these fields:
- "pipeline": "simple" | "detailed" | "full_accessibility"
- "steps": list of strings from ["image_description", "translation", "summarize"]
- "detail_level": "baixo" | "medio" | "alto"
- "priority": "speed" | "quality"

Rules:
- PDF without embedded text ALWAYS needs "image_description"
- Simple single images use pipeline "simple"
- Complex PDFs with many images use pipeline "detailed"
- Translation is ALWAYS needed (output is pt-br)
- Summarize only when pages > 10"""


class RouterIA(BaseAgent):
    def __init__(self):
        super().__init__(
            model=settings.router_model,
            prompt=ROUTER_PROMPT,
            keep_alive=0,
        )

    async def rotear(self, metadata: dict) -> dict:
        prompt_actual = self.prompt.format(metadata=json.dumps(metadata, indent=2))
        result = await self._call_raw(prompt_actual, is_image=False)
        return self._parse_plan(result)

    async def _call_raw(self, prompt: str, is_image: bool = False) -> str:
        import httpx

        url = f"{settings.ollama_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }
        if is_image:
            payload["images"] = [prompt]
        else:
            payload["prompt"] = prompt

        async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()

    def _parse_plan(self, text: str) -> dict:
        json_start = text.find("{")
        json_end = text.rfind("}")
        if json_start != -1 and json_end != -1:
            text = text[json_start : json_end + 1]
        try:
            plan = json.loads(text)
        except json.JSONDecodeError:
            plan = {
                "pipeline": "simple",
                "steps": ["image_description", "translation"],
                "detail_level": "medio",
                "priority": "speed",
            }
        if "steps" not in plan or "pipeline" not in plan:
            plan["pipeline"] = "simple"
            plan["steps"] = ["image_description", "translation"]
        if "translation" not in plan.get("steps", []):
            plan.setdefault("steps", []).append("translation")
        return plan
