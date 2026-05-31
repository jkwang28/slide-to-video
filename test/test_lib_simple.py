from unittest.mock import Mock, patch, mock_open


@patch("src.slide_to_video.lib.Project")
@patch("src.slide_to_video.lib.os.makedirs")
@patch("src.slide_to_video.lib.os.path.exists")
def test_slide_to_video_basic(mock_exists, mock_makedirs, mock_project_class):
    from src.slide_to_video.lib import slide_to_video

    # Mock project setup
    mock_project = Mock()
    mock_project_class.return_value = mock_project

    # Mock directory doesn't exist initially
    mock_exists.return_value = False

    project_config = {"output_dir": "/output"}

    slide_to_video(project_config=project_config)

    # Verify directory creation
    mock_makedirs.assert_called_once_with("/output", exist_ok=True)

    # Verify project creation and execution
    mock_project_class.assert_called_once_with(name="project", config=project_config)
    mock_project.build.assert_called_once_with(tts_only=False)
    mock_project.save.assert_called_once()


@patch("src.slide_to_video.lib.Project")
@patch("src.slide_to_video.lib.os.makedirs")
@patch("src.slide_to_video.lib.os.path.exists")
@patch("src.slide_to_video.lib.os.system")
def test_slide_to_video_existing_dir_no_project_file(
    mock_system, mock_exists, mock_makedirs, mock_project_class
):
    from src.slide_to_video.lib import slide_to_video

    # Mock project setup
    mock_project = Mock()
    mock_project_class.return_value = mock_project

    def exists_side_effect(path):
        if path == "/output":
            return True
        elif path == "/output/project.yaml":
            return False
        return False

    mock_exists.side_effect = exists_side_effect

    project_config = {"output_dir": "/output"}

    slide_to_video(project_config=project_config)

    # Should remove existing directory when project.yaml doesn't exist
    mock_system.assert_called_once_with("rm -rf /output")
    mock_makedirs.assert_called_once_with("/output", exist_ok=True)

    # Verify project execution
    mock_project.build.assert_called_once_with(tts_only=False)
    mock_project.save.assert_called_once()


@patch("src.slide_to_video.lib.Project")
@patch("src.slide_to_video.lib.os.makedirs")
@patch("src.slide_to_video.lib.os.path.exists")
@patch("src.slide_to_video.lib.os.system")
def test_slide_to_video_existing_dir_with_project_file(
    mock_system, mock_exists, mock_makedirs, mock_project_class
):
    from src.slide_to_video.lib import slide_to_video

    # Mock project setup
    mock_project = Mock()
    mock_project_class.return_value = mock_project

    def exists_side_effect(path):
        if path == "/output":
            return True
        elif path == "/output/project.yaml":
            return True
        return False

    mock_exists.side_effect = exists_side_effect

    project_config = {"output_dir": "/output"}

    slide_to_video(project_config=project_config)

    # Should NOT remove directory when project.yaml exists
    mock_system.assert_not_called()
    mock_makedirs.assert_called_once_with("/output", exist_ok=True)

    # Verify project execution
    mock_project.build.assert_called_once_with(tts_only=False)
    mock_project.save.assert_called_once()


@patch("src.slide_to_video.lib.Project")
@patch("src.slide_to_video.lib.os.makedirs")
@patch("src.slide_to_video.lib.os.path.exists")
def test_slide_to_video_tts_only(mock_exists, mock_makedirs, mock_project_class):
    from src.slide_to_video.lib import slide_to_video

    mock_project = Mock()
    mock_project_class.return_value = mock_project
    mock_exists.return_value = False

    project_config = {"output_dir": "/output", "tts_only": True}

    slide_to_video(project_config=project_config)

    mock_project_class.assert_called_once_with(name="project", config=project_config)
    mock_project.build.assert_called_once_with(tts_only=True)
    mock_project.save.assert_called_once()
    assert "tts_only" not in project_config


@patch("src.slide_to_video.lib.Project")
@patch("src.slide_to_video.lib.os.makedirs")
@patch("src.slide_to_video.lib.os.path.exists")
@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="original: replacement\nkey: value",
)
def test_slide_to_video_with_script_dict(
    mock_file, mock_exists, mock_makedirs, mock_project_class
):
    from src.slide_to_video.lib import slide_to_video

    # Mock project setup - capture the modified config
    captured_config = None

    def capture_project_init(name, config):
        nonlocal captured_config
        captured_config = config
        return Mock()

    mock_project_class.side_effect = capture_project_init
    mock_exists.return_value = False

    project_config = {
        "output_dir": "/output",
        "script_dict": "/path/to/replace_dict.txt",
    }

    slide_to_video(project_config=project_config)

    # Verify file was read
    mock_file.assert_called_once_with("/path/to/replace_dict.txt", "r")

    # Verify script_dict was replaced with parsed dictionary
    expected_dict = {"original": "replacement", "key": "value"}
    assert captured_config["script_dict"] == expected_dict


@patch("src.slide_to_video.lib.Project")
@patch("src.slide_to_video.lib.os.makedirs")
@patch("src.slide_to_video.lib.os.path.exists")
def test_slide_to_video_without_script_dict(
    mock_exists, mock_makedirs, mock_project_class
):
    from src.slide_to_video.lib import slide_to_video

    # Test that script_dict is not processed when not present
    captured_config = None

    def capture_project_init(name, config):
        nonlocal captured_config
        captured_config = config
        return Mock()

    mock_project_class.side_effect = capture_project_init
    mock_exists.return_value = False

    project_config = {"output_dir": "/output", "model": "local"}

    slide_to_video(project_config=project_config)

    # Verify script_dict key is not present
    assert "script_dict" not in captured_config
