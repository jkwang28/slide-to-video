from unittest.mock import Mock, patch
from typer.testing import CliRunner
from src.script import app, main


runner = CliRunner()


@patch("src.script.slide_to_video")
@patch("src.script.ProjectConfig")
@patch("builtins.open")
@patch("src.script.yaml.safe_load")
def test_generate_basic_local(
    mock_yaml, mock_open, mock_project_config, mock_slide_to_video
):
    # Mock ProjectConfig
    mock_config_instance = Mock()
    mock_project_config.return_value = mock_config_instance

    result = runner.invoke(
        app,
        [
            "--model",
            "local",
            "--slide",
            "test.pdf",
            "--script",
            "test.txt",
            "--output-dir",
            "/output",
            "--voice",
            "voice.wav",
        ],
    )

    assert result.exit_code == 0

    # Verify ProjectConfig was called with expected parameters
    mock_project_config.assert_called_once()
    config_args = mock_project_config.call_args[0][0]

    assert config_args["model"] == "local"
    assert config_args["slide"] == "test.pdf"
    assert config_args["script"] == "test.txt"
    assert config_args["output_dir"] == "/output"
    assert config_args["voice"] == "voice.wav"
    assert config_args["speech_speed"] == 1.0  # default
    assert config_args["delay"] == 2.0  # default
    assert config_args["language"] == "en"  # default

    # Verify slide_to_video was called
    mock_slide_to_video.assert_called_once_with(project_config=mock_config_instance)


@patch("src.script.slide_to_video")
@patch("src.script.ProjectConfig")
def test_generate_with_all_parameters(mock_project_config, mock_slide_to_video):
    mock_config_instance = Mock()
    mock_project_config.return_value = mock_config_instance

    result = runner.invoke(
        app,
        [
            "--model",
            "playht",
            "--slide",
            "presentation.pdf",
            "--script",
            "script.txt",
            "--output-dir",
            "/custom/output",
            "--voice",
            "custom_voice_id",
            "--speech-speed",
            "1.5",
            "--delay",
            "3.0",
            "--language",
            "es",
            "--script-dict",
            "replacements.txt",
        ],
    )

    assert result.exit_code == 0

    config_args = mock_project_config.call_args[0][0]

    assert config_args["model"] == "playht"
    assert config_args["slide"] == "presentation.pdf"
    assert config_args["script"] == "script.txt"
    assert config_args["output_dir"] == "/custom/output"
    assert config_args["voice"] == "custom_voice_id"
    assert config_args["speech_speed"] == 1.5
    assert config_args["delay"] == 3.0
    assert config_args["language"] == "es"
    assert config_args["script_dict"] == "replacements.txt"


@patch("src.script.slide_to_video")
@patch("src.script.ProjectConfig")
@patch("builtins.open")
@patch("src.script.yaml.safe_load")
def test_generate_with_config_file(
    mock_yaml, mock_open, mock_project_config, mock_slide_to_video
):
    # Mock config file content
    mock_yaml.return_value = {
        "model": "local",
        "slide": "config_slide.pdf",
        "voice": "config_voice.wav",
        "speech_speed": 0.8,
        "custom_key": "custom_value",
    }

    mock_config_instance = Mock()
    mock_project_config.return_value = mock_config_instance

    result = runner.invoke(
        app,
        [
            "--model",
            "local",  # Use valid model name
            "--slide",
            "test.pdf",  # Required parameter
            "--script",
            "test.txt",
            "--output-dir",
            "/output",
            "--config",
            "config.yaml",
        ],
    )

    assert result.exit_code == 0

    # Verify config file was opened and loaded
    mock_open.assert_called_once_with("config.yaml", "r")
    mock_yaml.assert_called_once()

    config_args = mock_project_config.call_args[0][0]

    # CLI args should override config file
    assert config_args["model"] == "local"  # overridden by CLI
    assert config_args["script"] == "test.txt"  # from CLI
    assert config_args["output_dir"] == "/output"  # from CLI
    assert config_args["slide"] == "test.pdf"  # overridden by CLI

    # Config file values should be used for non-overridden keys
    assert config_args["voice"] == "config_voice.wav"  # from config
    assert config_args["speech_speed"] == 0.8  # from config
    assert config_args["custom_key"] == "custom_value"  # from config

    # Defaults should be filled in
    assert config_args["delay"] == 2.0
    assert config_args["language"] == "en"


@patch("src.script.slide_to_video")
@patch("src.script.ProjectConfig")
def test_generate_without_config_file(mock_project_config, mock_slide_to_video):
    mock_config_instance = Mock()
    mock_project_config.return_value = mock_config_instance

    result = runner.invoke(
        app,
        [
            "--model",
            "local",
            "--slide",
            "test.pdf",
            "--script",
            "test.txt",
            "--output-dir",
            "/output",
        ],
    )

    assert result.exit_code == 0

    config_args = mock_project_config.call_args[0][0]

    # Should have default values for optional parameters
    assert config_args["speech_speed"] == 1.0
    assert config_args["delay"] == 2.0
    assert config_args["language"] == "en"
    assert config_args.get("voice") is None


def test_generate_missing_required_args():
    # Test missing model
    result = runner.invoke(
        app, ["--slide", "test.pdf", "--script", "test.txt", "--output-dir", "/output"]
    )
    assert result.exit_code != 0

    # Test missing slide
    result = runner.invoke(
        app, ["--model", "local", "--script", "test.txt", "--output-dir", "/output"]
    )
    assert result.exit_code != 0

    # Test missing script
    result = runner.invoke(
        app, ["--model", "local", "--slide", "test.pdf", "--output-dir", "/output"]
    )
    assert result.exit_code != 0

    # Test missing output-dir
    result = runner.invoke(
        app, ["--model", "local", "--slide", "test.pdf", "--script", "test.txt"]
    )
    assert result.exit_code != 0


@patch("src.script.get_all_engine_names")
def test_generate_invalid_model(mock_get_engines):
    mock_get_engines.return_value = ["local", "playht"]

    result = runner.invoke(
        app,
        [
            "--model",
            "invalid_model",
            "--slide",
            "test.pdf",
            "--script",
            "test.txt",
            "--output-dir",
            "/output",
        ],
    )

    assert result.exit_code != 0


@patch("src.script.get_all_engine_names")
def test_generate_invalid_language(mock_get_engines):
    mock_get_engines.return_value = ["local", "playht"]

    result = runner.invoke(
        app,
        [
            "--model",
            "local",
            "--slide",
            "test.pdf",
            "--script",
            "test.txt",
            "--output-dir",
            "/output",
            "--language",
            "invalid_lang",
        ],
    )

    assert result.exit_code != 0


@patch("src.script.slide_to_video")
@patch("src.script.ProjectConfig")
def test_generate_valid_languages(mock_project_config, mock_slide_to_video):
    mock_config_instance = Mock()
    mock_project_config.return_value = mock_config_instance

    valid_languages = [
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
    ]

    for lang in valid_languages:
        result = runner.invoke(
            app,
            [
                "--model",
                "local",
                "--slide",
                "test.pdf",
                "--script",
                "test.txt",
                "--output-dir",
                "/output",
                "--language",
                lang,
            ],
        )
        assert result.exit_code == 0


@patch("src.script.slide_to_video")
@patch("src.script.ProjectConfig")
@patch("builtins.open")
@patch("src.script.yaml.safe_load")
def test_generate_config_file_overrides_defaults(
    mock_yaml, mock_open, mock_project_config, mock_slide_to_video
):
    # Config file provides values different from defaults
    mock_yaml.return_value = {
        "speech_speed": 2.0,  # default is 1.0
        "delay": 5.0,  # default is 2.0
        "language": "fr",  # default is 'en'
    }

    mock_config_instance = Mock()
    mock_project_config.return_value = mock_config_instance

    result = runner.invoke(
        app,
        [
            "--model",
            "local",
            "--slide",
            "test.pdf",
            "--script",
            "test.txt",
            "--output-dir",
            "/output",
            "--config",
            "config.yaml",
        ],
    )

    assert result.exit_code == 0

    config_args = mock_project_config.call_args[0][0]

    # Config file values should override defaults
    assert config_args["speech_speed"] == 2.0
    assert config_args["delay"] == 5.0
    assert config_args["language"] == "fr"


@patch("src.script.app")
def test_main_function(mock_app):
    main()
    mock_app.assert_called_once()


@patch("src.script.slide_to_video")
@patch("src.script.ProjectConfig")
@patch("builtins.open")
@patch("src.script.yaml.safe_load")
def test_generate_empty_config_file(
    mock_yaml, mock_open, mock_project_config, mock_slide_to_video
):
    # Empty config file should work fine
    mock_yaml.return_value = {}

    mock_config_instance = Mock()
    mock_project_config.return_value = mock_config_instance

    result = runner.invoke(
        app,
        [
            "--model",
            "local",
            "--slide",
            "test.pdf",
            "--script",
            "test.txt",
            "--output-dir",
            "/output",
            "--config",
            "empty_config.yaml",
        ],
    )

    assert result.exit_code == 0

    config_args = mock_project_config.call_args[0][0]

    # Should use defaults since config is empty
    assert config_args["speech_speed"] == 1.0
    assert config_args["delay"] == 2.0
    assert config_args["language"] == "en"
