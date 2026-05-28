from .base_engine import TTSEngine
from .registery import register_engine
from ..aliyun import (
    AliyunDashScopeClient,
    language_to_aliyun_language_type,
    language_to_minimax_language_boost,
)


class AliyunQwenTTSEngine(TTSEngine):
    ENGINE_NAME = "Aliyun Qwen-TTS"
    ENGINE_DESCRIPTION = "Non-realtime text-to-speech using Alibaba Cloud Qwen-TTS"
    REQUIRED_CONFIG_KEYS = set()
    OPTIONAL_CONFIG_KEYS = {
        "ALIYUN_API_KEY",
        "DASHSCOPE_API_KEY",
        "aliyun_api_key",
        "dashscope_api_key",
        "aliyun_api_key_file",
        "aliyun_base_url",
        "aliyun_qwen_tts_model",
        "aliyun_qwen_voice",
        "aliyun_voice",
        "voice",
        "aliyun_language_type",
        "aliyun_tts_instruction",
        "aliyun_optimize_instructions",
        "aliyun_timeout",
    }
    SUPPORTED_FORMATS = {"wav"}

    def __init__(self, config: dict):
        super().__init__(**config)
        self.validate_config(config)
        self.model = config.get("aliyun_qwen_tts_model", "qwen3-tts-flash")
        self.voice = (
            config.get("aliyun_qwen_voice")
            or config.get("aliyun_voice")
            or config.get("voice")
            or "Cherry"
        )
        self.language_type = config.get("aliyun_language_type") or (
            language_to_aliyun_language_type(self.language)
        )
        self.instruction = self._build_instruction(config)
        self.optimize_instructions = config.get("aliyun_optimize_instructions")
        self.client = AliyunDashScopeClient(config)

    def synthesize(self, text: str, output_path: str, format: str = "wav"):
        super().synthesize(text, output_path, format)
        print(f"Generating Aliyun Qwen-TTS audio for {output_path}")
        self.client.synthesize_qwen_tts(
            text=text.strip(),
            output_path=output_path,
            model=self.model,
            voice=self.voice,
            language_type=self.language_type,
            instructions=self.instruction,
            optimize_instructions=self.optimize_instructions,
        )

    def parallizable(self) -> bool:
        return False

    def _build_instruction(self, config: dict):
        instruction = config.get("aliyun_tts_instruction")
        if not instruction and "instruct" in self.model:
            instruction = "请用自然、清晰、适合技术演示的语气朗读。"
        if instruction and self.speed != 1.0:
            instruction = f"{instruction} 语速控制在约 {self.speed} 倍。"
        return instruction


class AliyunCosyVoiceEngine(TTSEngine):
    ENGINE_NAME = "Aliyun CosyVoice"
    ENGINE_DESCRIPTION = "Non-realtime text-to-speech using Alibaba Cloud CosyVoice"
    REQUIRED_CONFIG_KEYS = set()
    OPTIONAL_CONFIG_KEYS = {
        "ALIYUN_API_KEY",
        "DASHSCOPE_API_KEY",
        "aliyun_api_key",
        "dashscope_api_key",
        "aliyun_api_key_file",
        "aliyun_base_url",
        "aliyun_cosyvoice_model",
        "aliyun_cosyvoice_voice",
        "aliyun_voice",
        "voice",
        "aliyun_tts_instruction",
        "aliyun_sample_rate",
        "aliyun_timeout",
    }
    SUPPORTED_FORMATS = {"wav", "mp3"}

    def __init__(self, config: dict):
        super().__init__(**config)
        self.validate_config(config)
        self.model = config.get("aliyun_cosyvoice_model", "cosyvoice-v3-flash")
        self.voice = (
            config.get("aliyun_cosyvoice_voice")
            or config.get("aliyun_voice")
            or config.get("voice")
            or "longanyang"
        )
        self.instruction = self._build_instruction(config)
        self.sample_rate = int(config.get("aliyun_sample_rate", 24000))
        self.client = AliyunDashScopeClient(config)

    def synthesize(self, text: str, output_path: str, format: str = "wav"):
        super().synthesize(text, output_path, format)
        print(f"Generating Aliyun CosyVoice audio for {output_path}")
        self.client.synthesize_cosyvoice(
            text=text.strip(),
            output_path=output_path,
            model=self.model,
            voice=self.voice,
            audio_format=format,
            sample_rate=self.sample_rate,
            instruction=self.instruction,
        )

    def parallizable(self) -> bool:
        return False

    def _build_instruction(self, config: dict):
        instruction = config.get("aliyun_tts_instruction")
        if instruction and self.speed != 1.0:
            instruction = f"{instruction} 语速控制在约 {self.speed} 倍。"
        return instruction


class AliyunMiniMaxTTSEngine(TTSEngine):
    ENGINE_NAME = "Aliyun MiniMax TTS"
    ENGINE_DESCRIPTION = "Synchronous text-to-speech using Alibaba Cloud MiniMax"
    REQUIRED_CONFIG_KEYS = set()
    OPTIONAL_CONFIG_KEYS = {
        "ALIYUN_API_KEY",
        "DASHSCOPE_API_KEY",
        "aliyun_api_key",
        "dashscope_api_key",
        "aliyun_api_key_file",
        "aliyun_base_url",
        "aliyun_minimax_model",
        "aliyun_minimax_voice",
        "aliyun_voice",
        "voice",
        "aliyun_minimax_emotion",
        "aliyun_minimax_volume",
        "aliyun_minimax_pitch",
        "aliyun_minimax_sample_rate",
        "aliyun_minimax_bitrate",
        "aliyun_minimax_channel",
        "aliyun_minimax_language_boost",
        "aliyun_minimax_text_normalization",
        "aliyun_minimax_latex_read",
        "aliyun_minimax_subtitle_enable",
        "aliyun_minimax_output_format",
        "aliyun_minimax_aigc_watermark",
        "aliyun_timeout",
    }
    SUPPORTED_FORMATS = {"wav", "mp3", "flac"}

    def __init__(self, config: dict):
        super().__init__(**config)
        self.validate_config(config)
        self.model = config.get("aliyun_minimax_model", "MiniMax/speech-2.8-hd")
        self.voice = (
            config.get("aliyun_minimax_voice")
            or config.get("aliyun_voice")
            or config.get("voice")
            or "male-qn-qingse"
        )
        self.emotion = config.get("aliyun_minimax_emotion")
        self.volume = float(config.get("aliyun_minimax_volume", 1.0))
        self.pitch = int(config.get("aliyun_minimax_pitch", 0))
        self.sample_rate = int(config.get("aliyun_minimax_sample_rate", 32000))
        self.bitrate = int(config.get("aliyun_minimax_bitrate", 128000))
        self.channel = int(config.get("aliyun_minimax_channel", 1))
        self.language_boost = config.get(
            "aliyun_minimax_language_boost",
            language_to_minimax_language_boost(self.language),
        )
        self.text_normalization = config.get("aliyun_minimax_text_normalization")
        self.latex_read = config.get("aliyun_minimax_latex_read")
        self.subtitle_enable = config.get("aliyun_minimax_subtitle_enable")
        self.output_format = config.get("aliyun_minimax_output_format", "url")
        self.aigc_watermark = config.get("aliyun_minimax_aigc_watermark")
        self.client = AliyunDashScopeClient(config)

    def synthesize(self, text: str, output_path: str, format: str = "wav"):
        super().synthesize(text, output_path, format)
        print(f"Generating Aliyun MiniMax audio for {output_path}")
        self.client.synthesize_minimax_tts(
            text=text.strip(),
            output_path=output_path,
            model=self.model,
            voice=self.voice,
            audio_format=format,
            sample_rate=self.sample_rate,
            speed=self.speed,
            volume=self.volume,
            pitch=self.pitch,
            bitrate=self.bitrate,
            channel=self.channel,
            emotion=self.emotion,
            language_boost=self.language_boost,
            text_normalization=self.text_normalization,
            latex_read=self.latex_read,
            subtitle_enable=self.subtitle_enable,
            output_format=self.output_format,
            aigc_watermark=self.aigc_watermark,
        )

    def parallizable(self) -> bool:
        return False


register_engine("qwen-tts", AliyunQwenTTSEngine)
register_engine("cosyvoice", AliyunCosyVoiceEngine)
register_engine("minimax", AliyunMiniMaxTTSEngine)
