import pytest
from src.slide_to_video.tts_engine import create_engine, get_all_engine_names
from src.slide_to_video.tts_engine.local import LocalTTSEngine
from src.slide_to_video.tts_engine.playht import PlayHTEngine


def test_tts_engine_imports():
    # Test that all imports work correctly
    from src.slide_to_video.tts_engine import (
        TTSEngine,
        create_engine,
        PlayHTEngine,
        LocalTTSEngine,
        get_all_engine_names,
    )

    assert TTSEngine is not None
    assert create_engine is not None
    assert PlayHTEngine is not None
    assert LocalTTSEngine is not None
    assert get_all_engine_names is not None


def test_get_all_engine_names_includes_defaults():
    # Since local.py and playht.py call register_engine on import
    names = get_all_engine_names()
    assert "local" in names
    assert "playht" in names
    assert "qwen-tts" in names
    assert "cosyvoice" in names
    assert "minimax" in names


def test_create_local_engine():
    config = {"voice": "/path/to/voice.wav", "speech_speed": 1.2}
    engine = create_engine("local", config)

    assert isinstance(engine, LocalTTSEngine)
    assert engine.voice_sample_path == "/path/to/voice.wav"
    assert engine.speed == 1.2


def test_create_playht_engine():
    config = {
        "PLAY_HT_USER_ID": "user123",
        "PLAY_HT_API_KEY": "key456",
        "voice": "voice789",
        "language": "es",
    }
    engine = create_engine("playht", config)

    assert isinstance(engine, PlayHTEngine)
    assert engine.user_id == "user123"
    assert engine.api_key == "key456"
    assert engine.voice == "voice789"
    assert engine.language == "es"


def test_create_engine_unknown_error():
    with pytest.raises(ValueError, match="Unknown engine: nonexistent"):
        create_engine("nonexistent", {})


def test_local_engine_missing_voice_key():
    config = {"speech_speed": 1.0}  # Missing "voice" key

    with pytest.raises(ValueError, match="Missing required key: voice"):
        LocalTTSEngine(config)


def test_playht_engine_missing_keys():
    # Test each missing required key
    for missing_key in ["PLAY_HT_USER_ID", "PLAY_HT_API_KEY", "voice"]:
        config = {
            "PLAY_HT_USER_ID": "user123",
            "PLAY_HT_API_KEY": "key456",
            "voice": "voice789",
        }
        del config[missing_key]

        with pytest.raises(ValueError, match=f"Missing required key: {missing_key}"):
            PlayHTEngine(config)


def test_playht_engine_full_init():
    config = {
        "PLAY_HT_USER_ID": "test_user",
        "PLAY_HT_API_KEY": "test_key",
        "voice": "test_voice",
        "speech_speed": 1.5,
        "language": "fr",
    }

    engine = PlayHTEngine(config)

    assert engine.user_id == "test_user"
    assert engine.api_key == "test_key"
    assert engine.voice == "test_voice"
    assert engine.speed == 1.5
    assert engine.language == "fr"
    assert engine.parallizable() is True


def test_local_engine_full_init():
    config = {"voice": "/path/to/sample.wav", "speech_speed": 0.8, "language": "de"}

    engine = LocalTTSEngine(config)

    assert engine.voice_sample_path == "/path/to/sample.wav"
    assert engine.speed == 0.8
    assert engine.language == "de"
    assert engine.parallizable() is False
    assert engine.tts is None  # Should be None until get_tts is called
