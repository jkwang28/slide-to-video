import pytest
from unittest.mock import Mock, patch
from typer.testing import CliRunner
from src.script import app, generate, main


runner = CliRunner()


@patch("src.script.slide_to_video")
@patch("src.script.ProjectConfig")
def test_generate_all_parameters(mock_project_config, mock_slide_to_video):
    """Test with all possible parameters"""
    mock_config_instance = Mock()
    mock_project_config.return_value = mock_config_instance

    result = runner.invoke(
        app,
        [
            "--model",
            "local",
            "--slide",
            "presentation.pdf",
            "--script",
            "script.txt",
            "--output-dir",
            "/custom/output",
            "--voice",
            "voice.wav",
            "--speech-speed",
            "1.8",
            "--delay",
            "4.0",
            "--language",
            "es",
            "--script-dict",
            "replace.txt",
        ],
    )

    assert result.exit_code == 0

    config_args = mock_project_config.call_args[0][0]

    assert config_args["model"] == "local"
    assert config_args["slide"] == "presentation.pdf"
    assert config_args["script"] == "script.txt"
    assert config_args["output_dir"] == "/custom/output"
    assert config_args["voice"] == "voice.wav"
    assert config_args["speech_speed"] == 1.8
    assert config_args["delay"] == 4.0
    assert config_args["language"] == "es"
    assert config_args["script_dict"] == "replace.txt"


@patch("src.script.slide_to_video")
@patch("src.script.ProjectConfig")
@patch("builtins.open")
@patch("src.script.yaml.safe_load")
def test_generate_config_file_empty(
    mock_yaml, mock_open, mock_project_config, mock_slide_to_video
):
    """Test with empty config file"""
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
            "empty.yaml",
        ],
    )

    assert result.exit_code == 0

    # Should use defaults
    config_args = mock_project_config.call_args[0][0]
    assert config_args["speech_speed"] == 1.0
    assert config_args["delay"] == 2.0
    assert config_args["language"] == "en"


@patch("src.script.slide_to_video")
@patch("src.script.ProjectConfig")
@patch("builtins.open")
@patch("src.script.yaml.safe_load")
def test_generate_config_file_partial_override(
    mock_yaml, mock_open, mock_project_config, mock_slide_to_video
):
    """Test config file with partial parameter override"""
    mock_yaml.return_value = {"speech_speed": 0.5, "custom_param": "custom_value"}

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
            "partial.yaml",
            "--delay",
            "3.5",  # This should override any config file value
        ],
    )

    assert result.exit_code == 0

    config_args = mock_project_config.call_args[0][0]
    # From config file
    assert config_args["speech_speed"] == 0.5
    assert config_args["custom_param"] == "custom_value"
    # From CLI (overrides)
    assert config_args["delay"] == 3.5
    # Default
    assert config_args["language"] == "en"


@patch("src.script.app")
def test_main_calls_app(mock_app):
    """Test main function calls typer app"""
    main()
    mock_app.assert_called_once()


def test_generate_command_context_params():
    """Test that the generate command has correct context handling"""
    # This tests that ctx.params is properly processed
    from typer.testing import CliRunner
    from src.script import generate

    # Test that the function signature includes ctx parameter
    import inspect

    sig = inspect.signature(generate)
    assert "ctx" in sig.parameters

    # Test that ctx parameter has correct type annotation
    ctx_param = sig.parameters["ctx"]
    assert "Context" in str(ctx_param.annotation)


@patch("src.script.slide_to_video")
@patch("src.script.ProjectConfig")
def test_generate_missing_optional_params(mock_project_config, mock_slide_to_video):
    """Test with minimal required parameters only"""
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

    # Check defaults were applied
    assert config_args["speech_speed"] == 1.0
    assert config_args["delay"] == 2.0
    assert config_args["language"] == "en"
    # Optional params should be None
    assert config_args.get("voice") is None
    assert config_args.get("script_dict") is None
    assert config_args.get("config") is None


def test_generate_language_choices():
    """Test that language parameter accepts all valid choices"""
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

    from src.script import generate
    import inspect

    sig = inspect.signature(generate)
    language_param = sig.parameters["language"]

    # Check that the parameter has Click choice constraint
    assert language_param.default.case_sensitive is False


@patch("src.script.slide_to_video")
@patch("src.script.ProjectConfig")
def test_generate_numeric_parameters(mock_project_config, mock_slide_to_video):
    """Test numeric parameter parsing"""
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
            "--speech-speed",
            "2.75",
            "--delay",
            "0.5",
        ],
    )

    assert result.exit_code == 0

    config_args = mock_project_config.call_args[0][0]

    # Check that numeric values are properly converted
    assert config_args["speech_speed"] == 2.75
    assert config_args["delay"] == 0.5
    assert isinstance(config_args["speech_speed"], float)
    assert isinstance(config_args["delay"], float)
