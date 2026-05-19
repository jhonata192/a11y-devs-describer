import tempfile
from pathlib import Path

import httpx

from bot.utils.logger import logger
from config.settings import settings


class OpenCodeClient:
    """HTTP client for the OpenCode serve API."""

    def __init__(self):
        self.base_url = settings.opencode_url.rstrip("/")
        self.timeout = settings.request_timeout
        self._session_id: str | None = None
        self._temp_files: list[Path] = []

    async def health_check(self) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{self.base_url}/global/health")
            resp.raise_for_status()
            return resp.json()

    async def _create_session(self) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/session", json={})
            resp.raise_for_status()
            data = resp.json()
            session_id = data.get("id")
            if not session_id:
                raise RuntimeError(f"Failed to create session: {data}")
            logger.info("OpenCode session created: {}", session_id)
            return session_id

    async def _get_session(self) -> str:
        if self._session_id:
            return self._session_id
        self._session_id = await self._create_session()
        return self._session_id

    def _save_image_to_temp(self, img_bytes: bytes) -> Path:
        tmp = Path(tempfile.gettempdir())
        f = tmp / f"opencode_img_{len(self._temp_files):04d}.jpg"
        f.write_bytes(img_bytes)
        self._temp_files.append(f)
        return f

    def _cleanup_temp_files(self):
        for f in self._temp_files:
            if f.exists():
                f.unlink()
        self._temp_files.clear()

    async def send_message(
        self,
        text: str,
        images: list[bytes] | None = None,
    ) -> str:
        parts: list[dict] = []

        if images:
            for img_bytes in images:
                tmp_path = self._save_image_to_temp(img_bytes)
                file_url = tmp_path.as_uri()
                parts.append({
                    "type": "file",
                    "url": file_url,
                    "mime": "image/jpeg",
                })
                logger.debug("Image saved to temp: {}", file_url)

        parts.append({"type": "text", "text": text})

        session_id = await self._get_session()

        payload = {
            "parts": parts,
            "model": {"modelID": settings.opencode_model, "providerID": "opencode"},
        }

        logger.debug("OpenCode payload: parts={}, model={}, image_count={}", len(parts), settings.opencode_model, len(images or []))

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/session/{session_id}/message",
                    json=payload,
                )
                if resp.status_code >= 400:
                    logger.error("OpenCode error response ({}): {}", resp.status_code, resp.text[:500])
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning("Session expired, recreating...")
                self._session_id = None
                session_id = await self._get_session()
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(
                        f"{self.base_url}/session/{session_id}/message",
                        json=payload,
                    )
                    if resp.status_code >= 400:
                        logger.error("OpenCode error response ({}): {}", resp.status_code, resp.text[:500])
                    resp.raise_for_status()
                    data = resp.json()
            else:
                raise

        return self._extract_text(data)

    @staticmethod
    def _extract_text(data: dict) -> str:
        parts = data.get("parts", [])
        texts = []
        for part in parts:
            if part.get("type") == "text":
                texts.append(part.get("text", ""))
        result = "\n".join(texts).strip()
        if result:
            logger.info("OpenCode response: {} chars", len(result))
        return result

    def reset_session(self):
        self._session_id = None
        self._cleanup_temp_files()


client = OpenCodeClient()
