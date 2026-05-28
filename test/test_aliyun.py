import base64
from unittest.mock import Mock, patch

import pytest

from src.slide_to_video.aliyun import (
    AliyunDashScopeClient,
    language_to_aliyun_language_type,
    language_to_minimax_language_boost,
    resolve_aliyun_api_key,
    resolve_aliyun_http_base_url,
)
from src.slide_to_video.tts_engine.aliyun import (
    AliyunCosyVoiceEngine,
    AliyunMiniMaxTTSEngine,
    AliyunQwenTTSEngine,
)


def test_resolve_aliyun_api_key_from_file(tmp_path):
    key_file = tmp_path / "aliyun.key"
    key_file.write_text("sk-test\n", encoding="utf-8")

    assert resolve_aliyun_api_key({"aliyun_api_key_file": str(key_file)}) == "sk-test"


def test_resolve_aliyun_http_base_url_defaults_to_beijing():
    assert resolve_aliyun_http_base_url({}) == "https://dashscope.aliyuncs.com/api/v1"


def test_resolve_aliyun_http_base_url_can_be_overridden():
    assert (
        resolve_aliyun_http_base_url({"aliyun_base_url": "https://example.com/api/v1/"})
        == "https://example.com/api/v1"
    )


def test_language_to_aliyun_language_type():
    assert language_to_aliyun_language_type("zh-cn") == "Chinese"
    assert language_to_aliyun_language_type("en") == "English"
    assert language_to_aliyun_language_type("pl") == "Auto"


def test_language_to_minimax_language_boost():
    assert language_to_minimax_language_boost("zh-cn") == "Chinese"
    assert language_to_minimax_language_boost("en") == "English"
    assert language_to_minimax_language_boost("pl") == "Polish"
    assert language_to_minimax_language_boost("xx") == "auto"


@patch("src.slide_to_video.aliyun.requests.post")
def test_qwen_tts_posts_expected_payload(mock_post, tmp_path):
    audio = b"fake wav bytes"
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "output": {
            "audio": {"data": base64.b64encode(audio).decode("ascii")},
        }
    }
    mock_post.return_value = mock_response

    output_path = tmp_path / "audio.wav"
    client = AliyunDashScopeClient({"ALIYUN_API_KEY": "sk-test"})
    client.synthesize_qwen_tts(
        text="hello",
        output_path=str(output_path),
        model="qwen3-tts-flash",
        voice="Cherry",
        language_type="English",
    )

    assert output_path.read_bytes() == audio
    mock_post.assert_called_once()
    assert mock_post.call_args.args[0].endswith(
        "/services/aigc/multimodal-generation/generation"
    )
    payload = mock_post.call_args.kwargs["json"]
    assert payload["model"] == "qwen3-tts-flash"
    assert payload["input"]["voice"] == "Cherry"
    assert payload["input"]["language_type"] == "English"


@patch("src.slide_to_video.aliyun.requests.get")
@patch("src.slide_to_video.aliyun.requests.post")
def test_cosyvoice_downloads_audio_url(mock_post, mock_get, tmp_path):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "output": {
            "audio": {"url": "https://example.com/audio.wav"},
        }
    }
    mock_post.return_value = mock_response

    mock_download = Mock()
    mock_download.__enter__ = Mock(return_value=mock_download)
    mock_download.__exit__ = Mock(return_value=None)
    mock_download.raise_for_status.return_value = None
    mock_download.iter_content.return_value = [b"abc", b"def"]
    mock_get.return_value = mock_download

    output_path = tmp_path / "audio.wav"
    client = AliyunDashScopeClient({"ALIYUN_API_KEY": "sk-test"})
    client.synthesize_cosyvoice(
        text="hello",
        output_path=str(output_path),
        model="cosyvoice-v3-flash",
        voice="longanyang",
        audio_format="wav",
        sample_rate=24000,
    )

    assert output_path.read_bytes() == b"abcdef"
    assert mock_post.call_args.args[0].endswith(
        "/services/audio/tts/SpeechSynthesizer"
    )
    mock_get.assert_called_once_with(
        "https://example.com/audio.wav", stream=True, timeout=120.0
    )


@patch("src.slide_to_video.aliyun.requests.get")
@patch("src.slide_to_video.aliyun.requests.post")
def test_minimax_tts_posts_expected_payload_and_downloads_url(
    mock_post, mock_get, tmp_path
):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "output": {
            "base_resp": {"status_code": 0, "status_msg": "success"},
            "data": {"audio": "https://example.com/minimax.wav", "status": 2},
        }
    }
    mock_post.return_value = mock_response

    mock_download = Mock()
    mock_download.__enter__ = Mock(return_value=mock_download)
    mock_download.__exit__ = Mock(return_value=None)
    mock_download.raise_for_status.return_value = None
    mock_download.iter_content.return_value = [b"abc", b"def"]
    mock_get.return_value = mock_download

    output_path = tmp_path / "audio.wav"
    client = AliyunDashScopeClient({"ALIYUN_API_KEY": "sk-test"})
    client.synthesize_minimax_tts(
        text="你好",
        output_path=str(output_path),
        model="MiniMax/speech-2.8-hd",
        voice="male-qn-qingse",
        audio_format="wav",
        sample_rate=32000,
        speed=1.25,
        volume=1.0,
        pitch=0,
        bitrate=128000,
        channel=1,
        emotion="happy",
        language_boost="Chinese",
    )

    assert output_path.read_bytes() == b"abcdef"
    assert mock_post.call_args.args[0].endswith(
        "/services/aigc/multimodal-generation/generation"
    )
    payload = mock_post.call_args.kwargs["json"]
    assert payload["model"] == "MiniMax/speech-2.8-hd"
    assert payload["input"]["text"] == "你好"
    assert payload["input"]["voice_setting"] == {
        "voice_id": "male-qn-qingse",
        "speed": 1.25,
        "vol": 1.0,
        "pitch": 0,
        "emotion": "happy",
    }
    assert payload["input"]["audio_setting"] == {
        "sample_rate": 32000,
        "format": "wav",
        "channel": 1,
    }
    assert payload["input"]["language_boost"] == "Chinese"
    assert payload["input"]["output_format"] == "url"
    mock_get.assert_called_once_with(
        "https://example.com/minimax.wav", stream=True, timeout=120.0
    )


def test_minimax_hex_audio_response_is_still_supported(tmp_path):
    audio = b"fake wav bytes"
    output_path = tmp_path / "audio.wav"
    client = AliyunDashScopeClient({"ALIYUN_API_KEY": "sk-test"})

    client.write_audio_from_response(
        {
            "output": {
                "base_resp": {"status_code": 0, "status_msg": "success"},
                "data": {"audio": audio.hex(), "status": 2},
            }
        },
        str(output_path),
    )

    assert output_path.read_bytes() == audio


@patch("src.slide_to_video.aliyun.requests.post")
def test_minimax_resource_exhausted_error_mentions_url_output(mock_post):
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = (
        '{"code":"InternalError","message":"Unexpected error: RESOURCE_EXHAUSTED: '
        'gRPC message exceeds maximum size 4194304: 4734457"}'
    )
    mock_post.return_value = mock_response

    client = AliyunDashScopeClient({"ALIYUN_API_KEY": "sk-test"})

    with pytest.raises(RuntimeError, match="aliyun_minimax_output_format=url"):
        client.post("/services/aigc/multimodal-generation/generation", {"model": "x"})


@patch("src.slide_to_video.tts_engine.aliyun.AliyunDashScopeClient")
def test_qwen_tts_engine_defaults(mock_client_class):
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    engine = AliyunQwenTTSEngine({"ALIYUN_API_KEY": "sk-test", "language": "zh-cn"})

    engine.synthesize("你好", "out.wav")

    call = mock_client.synthesize_qwen_tts.call_args.kwargs
    assert call["model"] == "qwen3-tts-flash"
    assert call["voice"] == "Cherry"
    assert call["language_type"] == "Chinese"
    assert engine.parallizable() is False


@patch("src.slide_to_video.tts_engine.aliyun.AliyunDashScopeClient")
def test_cosyvoice_engine_defaults(mock_client_class):
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    engine = AliyunCosyVoiceEngine({"ALIYUN_API_KEY": "sk-test"})

    engine.synthesize("你好", "out.wav")

    call = mock_client.synthesize_cosyvoice.call_args.kwargs
    assert call["model"] == "cosyvoice-v3-flash"
    assert call["voice"] == "longanyang"
    assert call["audio_format"] == "wav"
    assert call["sample_rate"] == 24000
    assert engine.parallizable() is False


@patch("src.slide_to_video.tts_engine.aliyun.AliyunDashScopeClient")
def test_minimax_tts_engine_defaults(mock_client_class):
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    engine = AliyunMiniMaxTTSEngine({"ALIYUN_API_KEY": "sk-test", "language": "zh-cn"})

    engine.synthesize("你好", "out.wav")

    call = mock_client.synthesize_minimax_tts.call_args.kwargs
    assert call["model"] == "MiniMax/speech-2.8-hd"
    assert call["voice"] == "male-qn-qingse"
    assert call["audio_format"] == "wav"
    assert call["sample_rate"] == 32000
    assert call["speed"] == 1.0
    assert call["language_boost"] == "Chinese"
    assert call["output_format"] == "url"
    assert engine.parallizable() is False
