"""
Example TTS Engine Implementation

This file demonstrates how to create a new TTS engine by extending the base TTSEngine class.
This example shows integration with OpenAI's TTS API.

To create your own engine:
1. Copy this file and rename it
2. Update the class name and metadata
3. Implement the required methods
4. Register your engine at the bottom
5. Add any required dependencies to requirements

This engine won't work without OpenAI API credentials - it's for demonstration only.
"""

import requests
from .base_engine import TTSEngine
from .registery import register_engine


class OpenAITTSEngine(TTSEngine):
    """
    Example TTS engine using OpenAI's Text-to-Speech API.

    This demonstrates how to integrate with a REST API-based TTS service.
    """

    # Engine metadata - this information helps users understand the engine
    ENGINE_NAME = "OpenAI TTS"
    ENGINE_DESCRIPTION = "High-quality text-to-speech using OpenAI's TTS API"

    # Define what configuration is required vs optional
    REQUIRED_CONFIG_KEYS = {"api_key"}  # API key is required
    OPTIONAL_CONFIG_KEYS = {"model", "voice_name"}  # These have defaults

    # Define supported languages and formats
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
    SUPPORTED_FORMATS = {"mp3", "opus", "aac", "flac"}

    def __init__(self, config: dict):
        """
        Initialize the OpenAI TTS engine.

        Args:
            config: Configuration dictionary containing:
                - api_key: OpenAI API key (required)
                - model: TTS model to use (optional, default: "tts-1")
                - voice_name: Voice to use (optional, default: "alloy")
                - speech_speed: Speed multiplier (inherited from base)
                - language: Language code (inherited from base)
        """
        # Always call parent constructor first
        super().__init__(**config)

        # Validate configuration using the base class method
        self.validate_config(config)

        # Store engine-specific configuration
        self.api_key = config["api_key"]
        self.model = config.get("model", "tts-1")
        self.voice_name = config.get("voice_name", "alloy")

        # Set up API headers
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def synthesize(self, text: str, output_path: str, format: str = "mp3"):
        """
        Synthesize text to speech using OpenAI's API.

        This method shows the standard pattern:
        1. Call parent method to validate format
        2. Make API request
        3. Handle response and save file
        4. Handle errors appropriately
        """
        # Always call parent to validate format support
        super().synthesize(text, output_path, format)

        # Prepare API request
        url = "https://api.openai.com/v1/audio/speech"
        payload = {
            "model": self.model,
            "input": text.strip(),
            "voice": self.voice_name,
            "response_format": format,
            "speed": self.speed,
        }

        try:
            # Make API request
            response = requests.post(url, headers=self.headers, json=payload)

            if response.status_code == 200:
                # Save audio file
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"Audio saved to {output_path}")
            else:
                # Handle API errors
                error_msg = f"OpenAI API error {response.status_code}: {response.text}"
                raise RuntimeError(error_msg)

        except requests.RequestException as e:
            raise RuntimeError(f"Network error calling OpenAI API: {e}")
        except Exception as e:
            raise RuntimeError(f"Error generating speech: {e}")

    def parallizable(self) -> bool:
        """
        OpenAI API supports parallel requests, so return True.

        For engines that have rate limits or can't handle parallel requests,
        return False to force sequential processing.
        """
        return True

    def cleanup(self) -> None:
        """
        Clean up any resources.

        For API-based engines, this usually means clearing credentials
        or closing persistent connections.
        """
        # Clear sensitive data
        self.api_key = None
        self.headers = {}
        super().cleanup()


# Register the engine - this makes it available to the system
# Users can now use --model openai-tts in the CLI
register_engine("openai-tts", OpenAITTSEngine)


# Example of a simple local engine that just creates silence
class MockTTSEngine(TTSEngine):
    """
    Mock TTS engine for testing - generates silence instead of speech.

    This is useful for testing the pipeline without requiring API keys
    or heavy dependencies.
    """

    ENGINE_NAME = "Mock TTS"
    ENGINE_DESCRIPTION = "Mock engine that generates silence (for testing)"
    REQUIRED_CONFIG_KEYS = set()  # No configuration required
    SUPPORTED_LANGUAGES = {"en"}  # Only English for simplicity
    SUPPORTED_FORMATS = {"wav"}

    def __init__(self, config: dict):
        super().__init__(**config)
        # No additional setup needed for mock engine

    def synthesize(self, text: str, output_path: str, format: str = "wav"):
        """Generate a silent audio file."""
        super().synthesize(text, output_path, format)

        try:
            import wave
            import struct

            # Create a 1-second silent WAV file
            duration = len(text) * 0.1  # Rough estimate based on text length
            sample_rate = 44100
            num_samples = int(sample_rate * duration)

            with wave.open(output_path, "w") as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)

                # Write silence
                for _ in range(num_samples):
                    wav_file.writeframesraw(struct.pack("<h", 0))

            print(f"Mock audio (silence) saved to {output_path}")

        except ImportError:
            # Fallback: create empty file
            with open(output_path, "wb") as f:
                f.write(b"")
            print(f"Empty file created at {output_path} (wave module not available)")

    def parallizable(self) -> bool:
        return True  # Mock engine is very fast


# Register the mock engine for testing
register_engine("mock", MockTTSEngine)
