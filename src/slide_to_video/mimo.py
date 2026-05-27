from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


DEFAULT_API_BASE_URL = "https://api.xiaomimimo.com/v1"
TOKEN_PLAN_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"


def resolve_mimo_api_key(config: Optional[dict] = None) -> str:
    config = config or {}
    api_key = config.get("MIMO_API_KEY") or config.get("mimo_api_key")
    if api_key:
        return str(api_key).strip()

    env_key = os.environ.get("MIMO_API_KEY")
    if env_key:
        return env_key.strip()

    key_file = config.get("mimo_api_key_file") or "mimo.key"
    key_path = Path(key_file)
    if key_path.exists():
        return key_path.read_text(encoding="utf-8").strip()

    raise ValueError(
        "Missing MiMo API key. Set MIMO_API_KEY or provide mimo_api_key_file."
    )


def resolve_mimo_base_url(config: Optional[dict], api_key: str) -> str:
    config = config or {}
    explicit_base_url = config.get("mimo_base_url")
    if explicit_base_url:
        return str(explicit_base_url).rstrip("/")
    if api_key.startswith("tp-"):
        return TOKEN_PLAN_BASE_URL
    return DEFAULT_API_BASE_URL


class MimoClient:
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.api_key = resolve_mimo_api_key(self.config)
        self.base_url = resolve_mimo_base_url(self.config, self.api_key)
        self.timeout = float(self.config.get("mimo_timeout", 120))

    def chat_completions(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "api-key": self.api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"MiMo API request failed with {response.status_code}: {response.text}"
            )
        return response.json()

    def generate_text(
        self,
        *,
        messages: List[Dict[str, str]],
        model: str = "mimo-v2.5",
        temperature: float = 0.2,
        max_completion_tokens: int = 4096,
    ) -> str:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_completion_tokens,
        }
        data = self.chat_completions(payload)
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"MiMo text response did not contain content: {data}") from exc
        if isinstance(content, list):
            return "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            ).strip()
        return str(content).strip()

    def synthesize_speech(
        self,
        *,
        text: str,
        output_path: str,
        instruction: str,
        model: str = "mimo-v2.5-tts",
        voice: str = "mimo_default",
        audio_format: str = "wav",
    ) -> None:
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": instruction},
                {"role": "assistant", "content": text},
            ],
            "audio": {
                "format": audio_format,
                "voice": voice,
            },
        }
        data = self.chat_completions(payload)
        try:
            audio_data = data["choices"][0]["message"]["audio"]["data"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"MiMo TTS response did not contain audio data: {data}") from exc

        audio_bytes = base64.b64decode(audio_data)
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
