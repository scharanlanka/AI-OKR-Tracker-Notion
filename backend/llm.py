import logging
import os
import json
from typing import Iterator, Optional

import requests

logger = logging.getLogger(__name__)


class AzureLLMClient:
    """Small wrapper for Azure-hosted chat completion endpoint."""

    def __init__(self):
        self.endpoint = os.getenv("AZURE_LLM_ENDPOINT", "").strip()
        self.api_key = os.getenv("AZURE_LLM_API_KEY", "").strip().strip('"')
        self.model = os.getenv("AZURE_LLM_DEPLOYMENT_NAME", "").strip().strip('"')

    @property
    def is_enabled(self) -> bool:
        return bool(self.endpoint and self.api_key and self.model)

    def chat(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Returns assistant text or None if unavailable/error."""
        if not self.is_enabled:
            return None

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
        }

        headers = {
            "Content-Type": "application/json",
            # Some endpoints use api-key, others accept bearer auth.
            "api-key": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            resp = requests.post(self.endpoint, json=payload, headers=headers, timeout=30)
            if resp.status_code >= 400:
                logger.error("Azure LLM request failed: %s - %s", resp.status_code, resp.text)
                return None
            data = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Azure LLM call error: %s", exc)
            return None

    def chat_stream(self, prompt: str, system_prompt: Optional[str] = None) -> Iterator[str]:
        """Streams assistant deltas token-by-token using the configured chat endpoint."""
        if not self.is_enabled:
            return

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            with requests.post(self.endpoint, json=payload, headers=headers, timeout=60, stream=True) as resp:
                if resp.status_code >= 400:
                    logger.error("Azure LLM stream request failed: %s - %s", resp.status_code, resp.text)
                    return

                for raw_line in resp.iter_lines(decode_unicode=True):
                    if not raw_line:
                        continue
                    line = raw_line.strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    text = self._extract_stream_text(delta)
                    if text:
                        yield text
        except Exception as exc:  # noqa: BLE001
            logger.exception("Azure LLM stream error: %s", exc)
            return

    def _extract_stream_text(self, delta) -> str:
        """
        Handle different SDK delta shapes:
        - delta.content as plain string
        - delta.content as a list of content items (dict/object) with text
        """
        content = delta.get("content") if isinstance(delta, dict) else getattr(delta, "content", None)
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                    continue
                if isinstance(item, dict):
                    txt = item.get("text") or item.get("content") or ""
                    if txt:
                        parts.append(str(txt))
                    continue
                txt = getattr(item, "text", None) or getattr(item, "content", None)
                if txt:
                    parts.append(str(txt))
            return "".join(parts)
        return str(content)
