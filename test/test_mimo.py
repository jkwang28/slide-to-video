import base64
from unittest.mock import Mock, patch

from src.slide_to_video.mimo import MimoClient, resolve_mimo_api_key, resolve_mimo_base_url
from src.slide_to_video.tts_engine.mimo import MimoTTSEngine


def test_resolve_mimo_api_key_from_file(tmp_path):
    key_file = tmp_path / "mimo.key"
    key_file.write_text("sk-test\n", encoding="utf-8")

    assert resolve_mimo_api_key({"mimo_api_key_file": str(key_file)}) == "sk-test"


def test_resolve_mimo_base_url_uses_token_plan_for_tp_key():
    assert (
        resolve_mimo_base_url({}, "tp-test")
        == "https://token-plan-cn.xiaomimimo.com/v1"
    )


def test_resolve_mimo_base_url_uses_public_api_for_sk_key():
    assert resolve_mimo_base_url({}, "sk-test") == "https://api.xiaomimimo.com/v1"


def test_resolve_mimo_base_url_can_be_overridden():
    assert (
        resolve_mimo_base_url({"mimo_base_url": "https://example.com/v1/"}, "tp-test")
        == "https://example.com/v1"
    )


@patch("src.slide_to_video.mimo.requests.post")
def test_mimo_client_synthesize_speech_writes_audio(mock_post, tmp_path):
    audio = b"fake wav bytes"
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "audio": {"data": base64.b64encode(audio).decode("ascii")}
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    output_path = tmp_path / "audio.wav"
    client = MimoClient({"MIMO_API_KEY": "sk-test"})
    client.synthesize_speech(
        text="hello",
        output_path=str(output_path),
        instruction="read naturally",
    )

    assert output_path.read_bytes() == audio
    payload = mock_post.call_args.kwargs["json"]
    assert payload["model"] == "mimo-v2.5-tts"
    assert payload["messages"][0]["role"] == "user"
    assert payload["messages"][1]["content"] == "hello"
    assert payload["audio"]["format"] == "wav"


@patch("src.slide_to_video.tts_engine.mimo.MimoClient")
def test_mimo_tts_engine_uses_configured_voice(mock_client_class):
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    engine = MimoTTSEngine(
        {
            "MIMO_API_KEY": "sk-test",
            "mimo_tts_model": "mimo-v2.5-tts",
            "mimo_voice": "default_zh",
            "speech_speed": 1.1,
        }
    )

    engine.synthesize("你好", "out.wav")

    mock_client.synthesize_speech.assert_called_once()
    call = mock_client.synthesize_speech.call_args.kwargs
    assert call["voice"] == "default_zh"
    assert call["text"] == "你好"
    assert "1.1" in call["instruction"]
