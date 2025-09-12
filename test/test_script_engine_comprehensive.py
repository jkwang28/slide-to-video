import pytest
from unittest.mock import Mock, patch
from src.slide_to_video.script_engine import (
    ScriptEngine,
    Script,
    ScriptConfig,
    extract_text_from_docx,
)


@pytest.fixture
def script_engine():
    return ScriptEngine()


def test_script_config_is_dict():
    config = ScriptConfig({"key": "value"})
    assert config["key"] == "value"
    assert isinstance(config, dict)


def test_script_dataclass():
    script = Script(
        text="Hello World",
        original_text="Hello World Original",
        path="/path/to/script.txt",
    )
    assert script.text == "Hello World"
    assert script.original_text == "Hello World Original"
    assert script.path == "/path/to/script.txt"
    assert script.config is None


def test_script_dataclass_with_config():
    config = ScriptConfig({"delay": 2.5})
    script = Script(
        text="Hello World",
        original_text="Hello World Original",
        path="/path/to/script.txt",
        config=config,
    )
    assert script.config == config


@patch("src.slide_to_video.script_engine.Document")
def test_extract_text_from_docx(mock_document_class):
    # Mock the Document and its paragraphs
    mock_doc = Mock()
    mock_para1 = Mock()
    mock_para1.text = "First paragraph"
    mock_para2 = Mock()
    mock_para2.text = "Second paragraph"
    mock_doc.paragraphs = [mock_para1, mock_para2]

    mock_document_class.return_value = mock_doc

    result = extract_text_from_docx("test.docx")

    mock_document_class.assert_called_once_with("test.docx")
    assert result == "First paragraph\nSecond paragraph"


@patch("src.slide_to_video.script_engine.Document")
def test_extract_text_from_docx_empty(mock_document_class):
    mock_doc = Mock()
    mock_doc.paragraphs = []
    mock_document_class.return_value = mock_doc

    result = extract_text_from_docx("test.docx")
    assert result == ""


def test_load_script_txt(script_engine, tmp_path):
    script_path = tmp_path / "test.txt"
    script_path.write_text("Test content")

    result = script_engine.load_script(str(script_path))
    assert result == "Test content"


@patch("src.slide_to_video.script_engine.extract_text_from_docx")
def test_load_script_docx(mock_extract, script_engine):
    mock_extract.return_value = "Docx content"

    result = script_engine.load_script("test.docx")
    assert result == "Docx content"
    mock_extract.assert_called_once_with("test.docx")


@patch("src.slide_to_video.script_engine.extract_text_from_docx")
def test_load_script_doc(mock_extract, script_engine):
    mock_extract.return_value = "Doc content"

    result = script_engine.load_script("test.doc")
    assert result == "Doc content"
    mock_extract.assert_called_once_with("test.doc")


def test_parse_script_no_config(script_engine):
    script = "Simple script text"
    text, config = script_engine.parse_script(script)

    assert text == "Simple script text"
    assert config is None


def test_parse_script_with_delay_config(script_engine):
    script = "Script text===#delay: 3.5"
    text, config = script_engine.parse_script(script)

    assert text == "Script text"
    assert isinstance(config, ScriptConfig)
    assert config["delay"] == 3.5


def test_parse_script_with_whitespace(script_engine):
    script = "  Script text  === #delay: 2.0  "
    text, config = script_engine.parse_script(script)

    assert text == "Script text"
    assert config["delay"] == 2.0


def test_parse_script_invalid_format(script_engine):
    script = "Part1===Part2===Part3"

    with pytest.raises(ValueError, match="Invalid script format"):
        script_engine.parse_script(script)


def test_parse_script_config_with_multiple_lines(script_engine):
    script = "Script text===#delay: 2.5\n#other: ignored"
    text, config = script_engine.parse_script(script)

    assert text == "Script text"
    assert config["delay"] == 2.5
    # Only #delay is currently supported


def test_split_script_simple(script_engine, tmp_path):
    script_path = tmp_path / "script.txt"
    script_path.write_text("Part 1NEWSLIDEPart 2")

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = script_engine.split_script(str(script_path), str(output_dir))

    assert len(result) == 2
    assert result[0].text == "Part 1"
    assert result[0].original_text == "Part 1"
    assert result[1].text == "Part 2"
    assert result[1].original_text == "Part 2"

    # Check files were created
    assert (output_dir / "sub_paragraph_1.txt").exists()
    assert (output_dir / "sub_paragraph_2.txt").exists()


def test_split_script_with_custom_marker(script_engine, tmp_path):
    script_path = tmp_path / "script.txt"
    script_path.write_text("Part 1CUSTOMPart 2")

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = script_engine.split_script(
        str(script_path), str(output_dir), marker="CUSTOM"
    )

    assert len(result) == 2
    assert result[0].text == "Part 1"
    assert result[1].text == "Part 2"


def test_split_script_with_empty_parts(script_engine, tmp_path):
    script_path = tmp_path / "script.txt"
    script_path.write_text("Part 1NEWSLIDE  \n\n  NEWSLIDEPart 2")

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = script_engine.split_script(str(script_path), str(output_dir))

    # Empty parts should be filtered out
    assert len(result) == 2
    assert result[0].text == "Part 1"
    assert result[1].text == "Part 2"


def test_split_script_with_config(script_engine, tmp_path):
    script_path = tmp_path / "script.txt"
    script_path.write_text("Part 1===#delay: 1.5NEWSLIDEPart 2===#delay: 3.0")

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = script_engine.split_script(str(script_path), str(output_dir))

    assert len(result) == 2
    assert result[0].config["delay"] == 1.5
    assert result[1].config["delay"] == 3.0


def test_split_script_with_replace_dict(script_engine, tmp_path):
    script_path = tmp_path / "script.txt"
    script_path.write_text("Hello worldNEWSLIDEGoodbye world")

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    replace_dict = {"world": "universe"}
    result = script_engine.split_script(
        str(script_path), str(output_dir), script_dict=replace_dict
    )

    assert len(result) == 2
    assert result[0].text == "Hello universe"
    assert result[0].original_text == "Hello world"
    assert result[1].text == "Goodbye universe"
    assert result[1].original_text == "Goodbye world"


def test_replace_dict_simple(script_engine):
    text = "Hello world"
    replace_dict = {"world": "universe"}

    result = script_engine.replace_dict(text, replace_dict)
    assert result == "Hello universe"


def test_replace_dict_word_boundary(script_engine):
    text = "The wonderful world"
    replace_dict = {"world": "universe"}

    result = script_engine.replace_dict(text, replace_dict)
    # Should not replace "world" in "wonderful"
    assert result == "The wonderful universe"


def test_replace_dict_plural(script_engine):
    text = "I have many cats and dogs"
    replace_dict = {"cat": "feline", "dog": "canine"}

    result = script_engine.replace_dict(text, replace_dict)
    assert result == "I have many felines and canines"


def test_replace_dict_multiple_occurrences(script_engine):
    text = "The cat and the cat are cats"
    replace_dict = {"cat": "dog"}

    result = script_engine.replace_dict(text, replace_dict)
    assert result == "The dog and the dog are dogs"


def test_replace_dict_no_matches(script_engine):
    text = "Hello world"
    replace_dict = {"foo": "bar"}

    result = script_engine.replace_dict(text, replace_dict)
    assert result == "Hello world"  # No changes


def test_replace_dict_empty(script_engine):
    text = "Hello world"
    replace_dict = {}

    result = script_engine.replace_dict(text, replace_dict)
    assert result == "Hello world"
