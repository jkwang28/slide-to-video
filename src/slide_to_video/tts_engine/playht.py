import time
import requests
from .base_engine import TTSEngine
from .registery import register_engine


class PlayHTEngine(TTSEngine):
    """
    Play.ht TTS engine for cloud-based text-to-speech synthesis.

    This engine uses the Play.ht API for high-quality voice synthesis
    with support for custom voices and multiple languages.
    """

    # Engine metadata
    ENGINE_NAME = "Play.ht TTS"
    ENGINE_DESCRIPTION = (
        "Cloud-based text-to-speech using Play.ht API with custom voices"
    )
    REQUIRED_CONFIG_KEYS = {"PLAY_HT_USER_ID", "PLAY_HT_API_KEY", "voice"}
    OPTIONAL_CONFIG_KEYS = {"quality", "voice_engine", "sample_rate"}
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
        """
        Initialize the Play.ht TTS engine.

        Args:
            config: Configuration dictionary containing:
                - PLAY_HT_USER_ID: Play.ht user ID
                - PLAY_HT_API_KEY: Play.ht API key
                - voice: Voice ID or name to use
                - quality: Audio quality (optional, default: "medium")
                - voice_engine: Voice engine to use (optional, default: "PlayHT2.0")
                - sample_rate: Audio sample rate (optional, default: 44100)
        """
        super().__init__(**config)
        self.validate_config(config)

        self.user_id = config["PLAY_HT_USER_ID"]
        self.api_key = config["PLAY_HT_API_KEY"]
        self.voice = config["voice"]
        self.quality = config.get("quality", "medium")
        self.voice_engine = config.get("voice_engine", "PlayHT2.0")
        self.sample_rate = config.get("sample_rate", 44100)

    def parallizable(self) -> bool:
        """Play.ht supports parallel processing since it's a cloud API."""
        return True

    def generate_audio_job(self, text, voice, headers):
        """
        Send a POST request to generate an audio job with the provided text and voice.

        :param text: The text to be converted to speech.
        :param voice: The voice to use for the speech.
        :param headers: The headers to use for the request.
        :return: The URL to poll for the status of the job.
        """
        url = "https://api.play.ht/api/v2/tts"
        payload = {
            "text": text,
            "voice": voice,
            "voice_engine": self.voice_engine,
            "quality": self.quality,
            "sample_rate": self.sample_rate,
            "output_format": "wav",
            "speed": self.speed,
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 201:
            print(response)
            raise Exception("Failed to generate audio job.")
        data = response.json()
        poll_url = data["_links"][0]["href"]
        return poll_url

    def poll_status_and_get_url(self, poll_url, headers, polling_interval=0.5):
        """
        Poll the given URL until the status becomes 'complete' and then fetch the URL from the response.

        :param poll_url: The URL to poll for the status.
        :param headers: The headers to use for the request.
        :param polling_interval: The interval in seconds between each poll request.
        :return: The URL from the response when the status is 'complete'.
        """
        while True:
            response = requests.get(poll_url, headers=headers)
            data = response.json()

            status = data.get("status")
            if status == "complete":
                output_url = data["output"]["url"]
                return output_url
            elif status == "failed":
                raise Exception("The job failed.")

            # Wait before polling again
            time.sleep(polling_interval)

    def download_file(self, url, local_filename):
        """
        Download a file from a URL to a local file.

        :param url: The URL of the file to download.
        :param local_filename: The local file path to save the downloaded file.
        """
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"File downloaded successfully and saved as {local_filename}")

    def playht_tts(self, text, output_path):
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "AUTHORIZATION": self.api_key,
            "X-USER-ID": self.user_id,
        }
        print(f"Generating audio job for text: {text}")
        poll_url = self.generate_audio_job(text, self.voice, headers)

        # Poll the status and get the final URL
        final_url = self.poll_status_and_get_url(poll_url, headers)

        # Download the file
        local_filename = output_path
        self.download_file(final_url, local_filename)

    def synthesize(self, text: str, output_path: str, format: str = "wav"):
        """Synthesize text to speech using Play.ht API."""
        # Call parent to validate format
        super().synthesize(text, output_path, format)
        self.playht_tts(text, output_path)


register_engine("playht", PlayHTEngine)
