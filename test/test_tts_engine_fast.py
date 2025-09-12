import pytest
from unittest.mock import Mock, patch, MagicMock
from src.slide_to_video.tts_engine.base_engine import TTSEngine
from src.slide_to_video.tts_engine.registery import (
    register_engine,
    get_all_engine_names,
    create_engine,
)
from src.slide_to_video.tts_engine.local import LocalTTSEngine
from src.slide_to_video.tts_engine.playht import PlayHTEngine


class MockTTSEngine(TTSEngine):
    def __init__(self, config=None, **kwargs):
        # Handle both dict config and kwargs
        if config:
            kwargs.update(config)
        super().__init__(**kwargs)
        self.synthesize_calls = []

    def synthesize(self, text: str, output_path: str, format: str = "wav"):
        self.synthesize_calls.append((text, output_path, format))

    def parallizable(self) -> bool:
        return True


class NonParallelTTSEngine(TTSEngine):
    def __init__(self, config=None, **kwargs):
        # Handle both dict config and kwargs
        if config:
            kwargs.update(config)
        super().__init__(**kwargs)
        self.synthesize_calls = []

    def synthesize(self, text: str, output_path: str, format: str = "wav"):
        self.synthesize_calls.append((text, output_path, format))

    def parallizable(self) -> bool:
        return False


def test_tts_engine_initialization():
    engine = MockTTSEngine(speech_speed=1.5, language="es")
    assert engine.speed == 1.5
    assert engine.language == "es"


def test_tts_engine_default_values():
    engine = MockTTSEngine()
    assert engine.speed == 1.0
    assert engine.language == "en"


def test_tts_engine_abstract_methods():
    # Trying to instantiate the abstract class should fail
    with pytest.raises(TypeError):
        TTSEngine()


@patch("src.slide_to_video.tts_engine.base_engine.concurrent.futures")
def test_par_synthesize_parallel(mock_futures):
    # Mock ThreadPoolExecutor and its context manager
    mock_executor = Mock()
    mock_futures.ThreadPoolExecutor.return_value.__enter__ = Mock(
        return_value=mock_executor
    )
    mock_futures.ThreadPoolExecutor.return_value.__exit__ = Mock(return_value=None)

    # Mock futures
    mock_future1 = Mock()
    mock_future2 = Mock()
    mock_executor.submit.side_effect = [mock_future1, mock_future2]

    # Mock the wait function to return immediately
    mock_futures.wait.return_value = None

    engine = MockTTSEngine()
    texts = ["Hello", "World"]
    paths = ["out1.wav", "out2.wav"]

    engine.par_synthesize(texts, paths)

    # Verify executor was used
    mock_futures.ThreadPoolExecutor.assert_called_once()
    assert mock_executor.submit.call_count == 2

    # Verify wait was called (it might be called multiple times due to implementation)
    assert mock_futures.wait.called


def test_par_synthesize_non_parallel():
    engine = NonParallelTTSEngine()

    texts = ["Hello", "World"]
    paths = ["out1.wav", "out2.wav"]

    engine.par_synthesize(texts, paths)

    # Should call synthesize directly for non-parallel engine
    assert len(engine.synthesize_calls) == 2
    assert engine.synthesize_calls[0] == ("Hello", "out1.wav", "wav")
    assert engine.synthesize_calls[1] == ("World", "out2.wav", "wav")


# Test Registry System
def test_register_engine():
    # Clear existing registrations
    from src.slide_to_video.tts_engine.registery import __all_engine_classes_dict__

    original_dict = __all_engine_classes_dict__.copy()

    try:
        register_engine("test_engine", MockTTSEngine)

        engines = get_all_engine_names()
        assert "test_engine" in engines
    finally:
        # Restore original state
        __all_engine_classes_dict__.clear()
        __all_engine_classes_dict__.update(original_dict)


def test_get_all_engine_names():
    from src.slide_to_video.tts_engine.registery import __all_engine_classes_dict__

    original_dict = __all_engine_classes_dict__.copy()

    try:
        __all_engine_classes_dict__.clear()
        __all_engine_classes_dict__["engine1"] = MockTTSEngine
        __all_engine_classes_dict__["engine2"] = MockTTSEngine

        names = get_all_engine_names()
        assert set(names) == {"engine1", "engine2"}
    finally:
        __all_engine_classes_dict__.clear()
        __all_engine_classes_dict__.update(original_dict)


def test_create_engine():
    from src.slide_to_video.tts_engine.registery import __all_engine_classes_dict__

    original_dict = __all_engine_classes_dict__.copy()

    try:
        register_engine("mock_engine", MockTTSEngine)

        config = {"speech_speed": 1.2, "language": "fr"}
        engine = create_engine("mock_engine", config)

        assert isinstance(engine, MockTTSEngine)
        assert engine.speed == 1.2
        assert engine.language == "fr"
    finally:
        __all_engine_classes_dict__.clear()
        __all_engine_classes_dict__.update(original_dict)


def test_create_engine_unknown():
    with pytest.raises(ValueError, match="Unknown engine: nonexistent"):
        create_engine("nonexistent", {})


# Test LocalTTSEngine
def test_local_tts_engine_init():
    config = {"voice": "/path/to/voice.wav", "speech_speed": 0.8}
    engine = LocalTTSEngine(config)

    assert engine.voice_sample_path == "/path/to/voice.wav"
    assert engine.speed == 0.8
    assert engine.tts is None


def test_local_tts_engine_missing_voice():
    config = {"speech_speed": 1.0}

    with pytest.raises(ValueError, match="Missing required key: voice"):
        LocalTTSEngine(config)


def test_local_tts_engine_parallizable():
    config = {"voice": "/path/to/voice.wav"}
    engine = LocalTTSEngine(config)

    assert engine.parallizable() is False


# Test PlayHTEngine
def test_playht_engine_init():
    config = {
        "PLAY_HT_USER_ID": "user123",
        "PLAY_HT_API_KEY": "key456",
        "voice": "voice789",
        "speech_speed": 1.2,
    }
    engine = PlayHTEngine(config)

    assert engine.user_id == "user123"
    assert engine.api_key == "key456"
    assert engine.voice == "voice789"
    assert engine.speed == 1.2


def test_playht_engine_missing_keys():
    config = {"PLAY_HT_USER_ID": "user123"}

    with pytest.raises(ValueError, match="Missing required key"):
        PlayHTEngine(config)


def test_playht_engine_parallizable():
    config = {
        "PLAY_HT_USER_ID": "user123",
        "PLAY_HT_API_KEY": "key456",
        "voice": "voice789",
    }
    engine = PlayHTEngine(config)

    assert engine.parallizable() is True


@patch("src.slide_to_video.tts_engine.playht.requests.post")
def test_playht_generate_audio_job_success(mock_post):
    config = {
        "PLAY_HT_USER_ID": "user123",
        "PLAY_HT_API_KEY": "key456",
        "voice": "voice789",
        "speech_speed": 1.5,
    }
    engine = PlayHTEngine(config)

    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "_links": [{"href": "https://api.play.ht/poll/123"}]
    }
    mock_post.return_value = mock_response

    headers = {"test": "header"}
    poll_url = engine.generate_audio_job("Hello world", "voice789", headers)

    assert poll_url == "https://api.play.ht/poll/123"

    # Verify the POST request
    mock_post.assert_called_once_with(
        "https://api.play.ht/api/v2/tts",
        json={
            "text": "Hello world",
            "voice": "voice789",
            "voice_engine": "PlayHT2.0",
            "quality": "medium",
            "sample_rate": 44100,
            "output_format": "wav",
            "speed": 1.5,
        },
        headers=headers,
    )


@patch("src.slide_to_video.tts_engine.playht.requests.post")
def test_playht_generate_audio_job_failure(mock_post):
    config = {
        "PLAY_HT_USER_ID": "user123",
        "PLAY_HT_API_KEY": "key456",
        "voice": "voice789",
    }
    engine = PlayHTEngine(config)

    # Mock failed response
    mock_response = Mock()
    mock_response.status_code = 400
    mock_post.return_value = mock_response

    with pytest.raises(Exception, match="Failed to generate audio job"):
        engine.generate_audio_job("Hello world", "voice789", {})


@patch("src.slide_to_video.tts_engine.playht.time.sleep")
@patch("src.slide_to_video.tts_engine.playht.requests.get")
def test_playht_poll_status_complete(mock_get, mock_sleep):
    config = {
        "PLAY_HT_USER_ID": "user123",
        "PLAY_HT_API_KEY": "key456",
        "voice": "voice789",
    }
    engine = PlayHTEngine(config)

    # Mock response sequence: first pending, then complete
    responses = [
        Mock(json=Mock(return_value={"status": "pending"})),
        Mock(
            json=Mock(
                return_value={
                    "status": "complete",
                    "output": {"url": "https://example.com/audio.wav"},
                }
            )
        ),
    ]
    mock_get.side_effect = responses

    url = engine.poll_status_and_get_url("https://poll.url", {}, polling_interval=0.01)

    assert url == "https://example.com/audio.wav"
    assert mock_get.call_count == 2
    mock_sleep.assert_called_with(0.01)  # Fast polling for tests


@patch("src.slide_to_video.tts_engine.playht.requests.get")
def test_playht_poll_status_failed(mock_get):
    config = {
        "PLAY_HT_USER_ID": "user123",
        "PLAY_HT_API_KEY": "key456",
        "voice": "voice789",
    }
    engine = PlayHTEngine(config)

    mock_response = Mock()
    mock_response.json.return_value = {"status": "failed"}
    mock_get.return_value = mock_response

    with pytest.raises(Exception, match="The job failed"):
        engine.poll_status_and_get_url("https://poll.url", {})


@patch("src.slide_to_video.tts_engine.playht.requests.get")
def test_playht_download_file(mock_get):
    config = {
        "PLAY_HT_USER_ID": "user123",
        "PLAY_HT_API_KEY": "key456",
        "voice": "voice789",
    }
    engine = PlayHTEngine(config)

    # Mock the streaming response
    mock_response = Mock()
    mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=None)
    mock_get.return_value = mock_response

    # Mock file writing
    with patch("builtins.open", create=True) as mock_open:
        mock_file = Mock()
        mock_open.return_value.__enter__ = Mock(return_value=mock_file)
        mock_open.return_value.__exit__ = Mock(return_value=None)

        engine.download_file("https://example.com/audio.wav", "output.wav")

        mock_get.assert_called_once_with("https://example.com/audio.wav", stream=True)
        mock_response.raise_for_status.assert_called_once()

        # Verify file was written
        mock_open.assert_called_once_with("output.wav", "wb")
        assert mock_file.write.call_count == 2
        mock_file.write.assert_any_call(b"chunk1")
        mock_file.write.assert_any_call(b"chunk2")


@patch.object(PlayHTEngine, "playht_tts")
def test_playht_synthesize(mock_playht_tts):
    config = {
        "PLAY_HT_USER_ID": "user123",
        "PLAY_HT_API_KEY": "key456",
        "voice": "voice789",
    }
    engine = PlayHTEngine(config)

    engine.synthesize("Hello world", "output.wav", "wav")

    mock_playht_tts.assert_called_once_with("Hello world", "output.wav")


@patch.object(PlayHTEngine, "generate_audio_job")
@patch.object(PlayHTEngine, "poll_status_and_get_url")
@patch.object(PlayHTEngine, "download_file")
def test_playht_tts_integration(mock_download, mock_poll, mock_generate):
    config = {
        "PLAY_HT_USER_ID": "user123",
        "PLAY_HT_API_KEY": "key456",
        "voice": "voice789",
    }
    engine = PlayHTEngine(config)

    # Mock the chain of calls
    mock_generate.return_value = "https://poll.url"
    mock_poll.return_value = "https://final.url/audio.wav"

    engine.playht_tts("Hello world", "output.wav")

    # Verify the chain of method calls
    expected_headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "AUTHORIZATION": "key456",
        "X-USER-ID": "user123",
    }

    mock_generate.assert_called_once_with("Hello world", "voice789", expected_headers)
    mock_poll.assert_called_once_with("https://poll.url", expected_headers)
    mock_download.assert_called_once_with("https://final.url/audio.wav", "output.wav")
