from __future__ import annotations

import base64
import os
from pathlib import Path
import time
from typing import Any, Dict, Optional

import requests


DEFAULT_HTTP_API_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
DEFAULT_COMPATIBLE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

QWEN_TTS_ENDPOINT = "/services/aigc/multimodal-generation/generation"
COSYVOICE_TTS_ENDPOINT = "/services/audio/tts/SpeechSynthesizer"


def resolve_aliyun_api_key(config: Optional[dict] = None) -> str:
    config = config or {}
    api_key = (
        config.get("ALIYUN_API_KEY")
        or config.get("DASHSCOPE_API_KEY")
        or config.get("aliyun_api_key")
        or config.get("dashscope_api_key")
    )
    if api_key:
        return str(api_key).strip()

    env_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("ALIYUN_API_KEY")
    if env_key:
        return env_key.strip()

    key_file = config.get("aliyun_api_key_file") or "aliyun.key"
    key_path = Path(key_file)
    if key_path.exists():
        return key_path.read_text(encoding="utf-8").strip()

    raise ValueError(
        "Missing Aliyun API key. Set DASHSCOPE_API_KEY or provide aliyun_api_key_file."
    )


def resolve_aliyun_http_base_url(config: Optional[dict] = None) -> str:
    config = config or {}
    return str(config.get("aliyun_base_url") or DEFAULT_HTTP_API_BASE_URL).rstrip("/")


def language_to_aliyun_language_type(language: str) -> str:
    language_map = {
        "zh-cn": "Chinese",
        "zh": "Chinese",
        "en": "English",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "es": "Spanish",
        "ja": "Japanese",
        "ko": "Korean",
        "fr": "French",
        "ru": "Russian",
    }
    return language_map.get((language or "").lower(), "Auto")


class AliyunDashScopeClient:
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.api_key = resolve_aliyun_api_key(self.config)
        self.base_url = resolve_aliyun_http_base_url(self.config)
        self.timeout = float(self.config.get("aliyun_timeout", 120))
        self.max_retries = int(self.config.get("aliyun_max_retries", 4))
        self.retry_delay = float(self.config.get("aliyun_retry_delay", 8))

    def post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        last_response = None
        for attempt in range(self.max_retries + 1):
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )
            last_response = response
            if response.status_code != 429:
                break
            if attempt < self.max_retries:
                time.sleep(self.retry_delay * (attempt + 1))

        if last_response is None:
            raise RuntimeError("Aliyun DashScope request was not sent.")
        if last_response.status_code >= 400:
            raise RuntimeError(
                "Aliyun DashScope request failed with "
                f"{last_response.status_code}: {last_response.text}"
            )
        data = last_response.json()
        status_code = data.get("status_code")
        if status_code and int(status_code) >= 400:
            raise RuntimeError(
                "Aliyun DashScope response failed with "
                f"{status_code}: {data.get('message') or data}"
            )
        return data

    def synthesize_qwen_tts(
        self,
        *,
        text: str,
        output_path: str,
        model: str,
        voice: str,
        language_type: str,
        instructions: Optional[str] = None,
        optimize_instructions: Optional[bool] = None,
    ) -> None:
        input_payload: Dict[str, Any] = {
            "text": text,
            "voice": voice,
            "language_type": language_type,
        }
        if instructions:
            input_payload["instructions"] = instructions
        if optimize_instructions is not None:
            input_payload["optimize_instructions"] = optimize_instructions

        data = self.post(
            QWEN_TTS_ENDPOINT,
            {
                "model": model,
                "input": input_payload,
            },
        )
        self.write_audio_from_response(data, output_path)

    def synthesize_cosyvoice(
        self,
        *,
        text: str,
        output_path: str,
        model: str,
        voice: str,
        audio_format: str,
        sample_rate: int,
        instruction: Optional[str] = None,
    ) -> None:
        input_payload: Dict[str, Any] = {
            "text": text,
            "voice": voice,
            "format": audio_format,
            "sample_rate": sample_rate,
        }
        if instruction:
            input_payload["instruction"] = instruction

        data = self.post(
            COSYVOICE_TTS_ENDPOINT,
            {
                "model": model,
                "input": input_payload,
            },
        )
        self.write_audio_from_response(data, output_path)

    def write_audio_from_response(self, data: Dict[str, Any], output_path: str) -> None:
        audio = data.get("output", {}).get("audio", {})
        audio_data = audio.get("data")
        if audio_data:
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(audio_data))
            return

        audio_url = audio.get("url")
        if not audio_url:
            raise RuntimeError(f"Aliyun DashScope response did not contain audio: {data}")
        self.download_file(audio_url, output_path)

    def download_file(self, url: str, output_path: str) -> None:
        with requests.get(url, stream=True, timeout=self.timeout) as response:
            response.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
