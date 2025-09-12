import pytest
import os
import tempfile
from unittest.mock import Mock, patch
from src.slide_to_video.utils import (
    par_execute,
    md5sum_of_file,
    exists,
    get_audio_duration,
)


def test_md5sum_of_file(tmp_path):
    test_file = tmp_path / "test.txt"
    test_content = "Hello, World!"
    test_file.write_text(test_content)

    md5_hash = md5sum_of_file(str(test_file))
    assert isinstance(md5_hash, str)
    assert len(md5_hash) == 32  # MD5 hash is 32 characters long

    # Test with the same content should give the same hash
    test_file2 = tmp_path / "test2.txt"
    test_file2.write_text(test_content)
    md5_hash2 = md5sum_of_file(str(test_file2))
    assert md5_hash == md5_hash2


def test_md5sum_of_file_binary(tmp_path):
    test_file = tmp_path / "binary_test.bin"
    test_content = b"\x00\x01\x02\x03\x04\x05"
    test_file.write_bytes(test_content)

    md5_hash = md5sum_of_file(str(test_file))
    assert isinstance(md5_hash, str)
    assert len(md5_hash) == 32


def test_exists_true(tmp_path):
    test_file = tmp_path / "existing_file.txt"
    test_file.write_text("content")

    assert exists(str(test_file)) is True


def test_exists_false():
    assert exists("/nonexistent/path/file.txt") is False


def test_exists_directory(tmp_path):
    test_dir = tmp_path / "test_directory"
    test_dir.mkdir()

    assert exists(str(test_dir)) is True


@patch("src.slide_to_video.utils.AudioSegment.from_wav")
def test_get_audio_duration(mock_from_wav):
    mock_audio = Mock()
    mock_audio.__len__ = Mock(return_value=5000)  # 5 seconds in milliseconds
    mock_from_wav.return_value = mock_audio

    duration = get_audio_duration("fake_audio.wav")
    assert duration == 5.0
    mock_from_wav.assert_called_once_with("fake_audio.wav")


def test_par_execute():
    def test_func(x, y):
        return x + y

    # Test parallel execution with multiple arguments
    futures = par_execute(test_func, [1, 2, 3], [4, 5, 6])

    assert len(futures) == 3
    # Results should be computed (5, 7, 9)
    results = [future.result() for future in futures]
    assert results == [5, 7, 9]


def test_par_execute_single_arg():
    def test_func(x):
        return x * 2

    futures = par_execute(test_func, [1, 2, 3])

    assert len(futures) == 3
    results = [future.result() for future in futures]
    assert results == [2, 4, 6]


def test_par_execute_exception_handling():
    def failing_func(x):
        if x == 2:
            raise ValueError("Test error")
        return x * 2

    # par_execute will raise exception immediately when one fails
    with pytest.raises(ValueError, match="Test error"):
        par_execute(failing_func, [1, 2, 3])


def test_par_execute_empty_args():
    def test_func(x):
        return x

    futures = par_execute(test_func, [])
    assert len(futures) == 0
