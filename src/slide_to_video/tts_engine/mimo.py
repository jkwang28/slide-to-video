from .base_engine import TTSEngine
from .registery import register_engine
from ..mimo import MimoClient


class MimoTTSEngine(TTSEngine):
    ENGINE_NAME = "Xiaomi MiMo TTS"
    ENGINE_DESCRIPTION = "Cloud-based text-to-speech using Xiaomi MiMo TTS"
    REQUIRED_CONFIG_KEYS = set()
    OPTIONAL_CONFIG_KEYS = {
        "MIMO_API_KEY",
        "mimo_api_key",
        "mimo_api_key_file",
        "mimo_base_url",
        "mimo_tts_model",
        "mimo_voice",
        "mimo_tts_instruction",
        "voice",
        "mimo_timeout",
    }
    SUPPORTED_LANGUAGES = {
        "en",
        "es",
        "fr",
        "de",
        "it",
        "pt",
        "pl",
        "tr",
        "ru",
        "nl",
        "cs",
        "ar",
        "zh-cn",
        "hu",
        "ko",
        "ja",
        "hi",
    }
    SUPPORTED_FORMATS = {"wav", "mp3"}

    def __init__(self, config: dict):
        super().__init__(**config)
        self.validate_config(config)
        self.model = config.get("mimo_tts_model", "mimo-v2.5-tts")
        self.voice = config.get("mimo_voice") or config.get("voice") or "mimo_default"
        self.instruction = config.get(
            "mimo_tts_instruction",
            "请用自然、清晰、适合技术演示的语气朗读，语速稳定，关键英文术语读清楚。",
        )
        if self.speed != 1.0:
            self.instruction = f"{self.instruction} 语速控制在约 {self.speed} 倍。"
        self.client = MimoClient(config)

    def synthesize(self, text: str, output_path: str, format: str = "wav"):
        super().synthesize(text, output_path, format)
        print(f"Generating MiMo audio for {output_path}")
        self.client.synthesize_speech(
            text=text.strip(),
            output_path=output_path,
            instruction=self.instruction,
            model=self.model,
            voice=self.voice,
            audio_format=format,
        )

    def parallizable(self) -> bool:
        return True


register_engine("mimo", MimoTTSEngine)
