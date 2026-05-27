from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set
import concurrent.futures
import logging


logger = logging.getLogger(__name__)


class TTSEngine(ABC):
    """
    Abstract base class for Text-to-Speech engines.

    This class provides the interface that all TTS engines must implement.
    It handles common functionality like parallel processing and configuration validation.

    To create a new TTS engine:
    1. Inherit from this class
    2. Implement the required abstract methods
    3. Call register_engine() to make it available

    Example:
        class MyTTSEngine(TTSEngine):
            REQUIRED_CONFIG_KEYS = {"api_key", "voice_id"}
            SUPPORTED_LANGUAGES = {"en", "es", "fr"}
            SUPPORTED_FORMATS = {"wav", "mp3"}

            def __init__(self, config: dict):
                super().__init__(**config)
                self.validate_config(config)
                # Initialize your engine here

            def synthesize(self, text: str, output_path: str, format: str = "wav"):
                # Implement text-to-speech synthesis
                pass

            def parallizable(self) -> bool:
                return True  # or False if your engine doesn't support parallel processing
    """

    # Subclasses should override these class attributes
    REQUIRED_CONFIG_KEYS: Set[str] = set()
    OPTIONAL_CONFIG_KEYS: Set[str] = set()
    SUPPORTED_LANGUAGES: Set[str] = {
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
    SUPPORTED_FORMATS: Set[str] = {"wav"}
    ENGINE_NAME: str = ""
    ENGINE_DESCRIPTION: str = ""

    def __init__(self, *, speech_speed=1.0, language="en", **kwargs):
        """
        Initialize the TTS engine with common configuration.

        Args:
            speech_speed: Speed multiplier for speech (1.0 = normal speed)
            language: Language code for synthesis
            **kwargs: Additional engine-specific configuration
        """
        self.speed = speech_speed
        self.language = language
        self._config = kwargs

        # Validate language support
        if language not in self.SUPPORTED_LANGUAGES:
            logger.warning(
                f"Language '{language}' may not be supported by {self.__class__.__name__}"
            )

    def validate_config(self, config: dict) -> None:
        """
        Validate the provided configuration against engine requirements.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ValueError: If required configuration is missing or invalid
        """
        missing_keys = self.REQUIRED_CONFIG_KEYS - set(config.keys())
        if missing_keys:
            if len(missing_keys) == 1:
                missing_key = next(iter(missing_keys))
                raise ValueError(f"Missing required key: {missing_key}")
            missing_keys_text = ", ".join(sorted(missing_keys))
            raise ValueError(f"Missing required key(s): {missing_keys_text}")

        # Validate language
        language = config.get("language", "en")
        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language: {language}. Supported: {self.SUPPORTED_LANGUAGES}"
            )

    def get_engine_info(self) -> Dict[str, Any]:
        """
        Get information about this engine.

        Returns:
            Dictionary containing engine metadata
        """
        return {
            "name": self.ENGINE_NAME or self.__class__.__name__,
            "description": self.ENGINE_DESCRIPTION,
            "supported_languages": sorted(self.SUPPORTED_LANGUAGES),
            "supported_formats": sorted(self.SUPPORTED_FORMATS),
            "required_config": sorted(self.REQUIRED_CONFIG_KEYS),
            "optional_config": sorted(self.OPTIONAL_CONFIG_KEYS),
            "supports_parallel": self.parallizable(),
        }

    @abstractmethod
    def synthesize(self, text: str, output_path: str, format: str = "wav"):
        """
        Synthesize text to speech and save to file.

        Args:
            text: Text to synthesize
            output_path: Path where to save the audio file
            format: Audio format (e.g., "wav", "mp3")

        Raises:
            ValueError: If format is not supported
            RuntimeError: If synthesis fails
        """
        if format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {format}. Supported: {self.SUPPORTED_FORMATS}"
            )

    @abstractmethod
    def parallizable(self) -> bool:
        """
        Return whether this engine supports parallel processing.

        Returns:
            True if the engine can safely run multiple synthesis operations in parallel,
            False if it requires sequential processing.
        """
        pass

    def cleanup(self) -> None:
        """
        Clean up resources when the engine is no longer needed.
        Subclasses can override this to perform cleanup operations.
        """
        pass

    def par_synthesize(
        self,
        texts: List[str],
        output_paths: List[str],
        *,
        format: str = "wav",
    ):
        if self.parallizable():
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                for text, output_path in zip(texts, output_paths):
                    future = executor.submit(self.synthesize, text, output_path)
                    futures.append(future)

                    concurrent.futures.wait(futures)
        else:
            for text, output_path in zip(texts, output_paths):
                self.synthesize(text, output_path)
