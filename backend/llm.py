import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class AzureLLMClient:
    """Small wrapper for Azure-hosted chat completion endpoint."""

    def __init__(self):
        self.endpoint = os.getenv("AZURE_LLM_ENDPOINT", "").strip()
        self.api_key = os.getenv("AZURE_LLM_API_KEY", "").strip().strip('"')
        self.model = os.getenv("AZURE_LLM_DEPLOYMENT_NAME", "")

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
            "temperature": 0.2,
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
