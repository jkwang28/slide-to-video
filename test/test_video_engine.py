import pytest
import os
import tempfile
from unittest.mock import Mock, patch, mock_open
from src.slide_to_video.video_engine import VideoEngine, run_ffmpeg_command


@pytest.fixture
def video_engine():
    return VideoEngine()


@patch('src.slide_to_video.video_engine.ffmpeg')
def test_run_ffmpeg_command(mock_ffmpeg):
    mock_command = Mock()
    mock_command.global_args.return_value = mock_command
    
    run_ffmpeg_command(mock_command)
    
    mock_command.global_args.assert_called_once_with("-loglevel", "error")
    mock_ffmpeg.run.assert_called_once_with(mock_command, overwrite_output=True)


@patch('src.slide_to_video.video_engine.ffmpeg')
@patch('src.slide_to_video.video_engine.run_ffmpeg_command')
def test_generate_video_from_image(mock_run_ffmpeg, mock_ffmpeg, video_engine):
    # Mock ffmpeg chain
    mock_input = Mock()
    mock_output = Mock()
    mock_ffmpeg.input.return_value = mock_input
    mock_ffmpeg.output.return_value = mock_output
    
    video_engine.generate_video_from_image("image.png", "video.mp4", 5.0)
    
    # Verify ffmpeg.input call
    mock_ffmpeg.input.assert_called_once_with("image.png", loop=1, t=5.0, framerate=30)
    
    # Verify ffmpeg.output call
    mock_ffmpeg.output.assert_called_once_with(
        mock_input, "video.mp4", vcodec="libx264", pix_fmt="yuv420p"
    )
    
    # Verify run_ffmpeg_command call
    mock_run_ffmpeg.assert_called_once_with(mock_output)


@patch.object(VideoEngine, 'generate_video_from_image')
@patch('src.slide_to_video.video_engine.par_execute')
def test_par_generate_video_from_image(mock_par_execute, mock_generate, video_engine):
    image_paths = ["img1.png", "img2.png"]
    video_paths = ["vid1.mp4", "vid2.mp4"]
    durations = [3.0, 5.0]
    
    video_engine.par_generate_video_from_image(image_paths, video_paths, durations)
    
    mock_par_execute.assert_called_once_with(
        video_engine.generate_video_from_image, 
        image_paths, 
        video_paths, 
        durations
    )


@patch('src.slide_to_video.video_engine.ffmpeg')
@patch('src.slide_to_video.video_engine.run_ffmpeg_command')
@patch('src.slide_to_video.video_engine.tempfile.NamedTemporaryFile')
@patch('src.slide_to_video.video_engine.os.remove')
@patch('src.slide_to_video.video_engine.os.path.abspath')
def test_concatenate_videos(mock_abspath, mock_remove, mock_temp_file, mock_run_ffmpeg, mock_ffmpeg, video_engine):
    # Mock temporary file
    mock_temp_file_obj = Mock()
    mock_temp_file_obj.name = "/tmp/temp_file.txt"
    mock_temp_file_obj.__enter__ = Mock(return_value=mock_temp_file_obj)
    mock_temp_file_obj.__exit__ = Mock(return_value=None)
    mock_temp_file.return_value = mock_temp_file_obj
    
    # Mock absolute paths
    mock_abspath.side_effect = lambda x: f"/absolute/{x}"
    
    # Mock ffmpeg chain
    mock_input = Mock()
    mock_output = Mock()
    mock_ffmpeg.input.return_value = mock_input
    mock_input.output.return_value = mock_output
    
    video_paths = ["video1.mp4", "video2.mp4"]
    output_path = "final.mp4"
    
    video_engine.concatenate_videos(video_paths, output_path)
    
    # Verify temporary file creation
    mock_temp_file.assert_called_once_with(delete=False, mode="w", suffix=".txt")
    
    # Verify file writes
    expected_writes = [
        "file '/absolute/video1.mp4'\n",
        "file '/absolute/video2.mp4'\n"
    ]
    write_calls = mock_temp_file_obj.write.call_args_list
    assert len(write_calls) == 2
    assert write_calls[0][0][0] == expected_writes[0]
    assert write_calls[1][0][0] == expected_writes[1]
    
    # Verify ffmpeg calls
    mock_ffmpeg.input.assert_called_once_with("/tmp/temp_file.txt", format="concat", safe=0)
    mock_input.output.assert_called_once_with(output_path, c="copy")
    mock_run_ffmpeg.assert_called_once_with(mock_output)
    
    # Verify cleanup
    mock_remove.assert_called_once_with("/tmp/temp_file.txt")


@patch('src.slide_to_video.video_engine.ffmpeg')
@patch('src.slide_to_video.video_engine.run_ffmpeg_command')
@patch('src.slide_to_video.video_engine.tempfile.NamedTemporaryFile')
@patch('src.slide_to_video.video_engine.os.remove')
@patch('src.slide_to_video.video_engine.os.path.abspath')
def test_concatenate_videos_single_video(mock_abspath, mock_remove, mock_temp_file, mock_run_ffmpeg, mock_ffmpeg, video_engine):
    # Test with single video
    mock_temp_file_obj = Mock()
    mock_temp_file_obj.name = "/tmp/temp_file.txt"
    mock_temp_file_obj.__enter__ = Mock(return_value=mock_temp_file_obj)
    mock_temp_file_obj.__exit__ = Mock(return_value=None)
    mock_temp_file.return_value = mock_temp_file_obj
    
    mock_abspath.return_value = "/absolute/video1.mp4"
    
    mock_input = Mock()
    mock_output = Mock()
    mock_ffmpeg.input.return_value = mock_input
    mock_input.output.return_value = mock_output
    
    video_paths = ["video1.mp4"]
    output_path = "final.mp4"
    
    video_engine.concatenate_videos(video_paths, output_path)
    
    # Should still work with single video
    assert mock_temp_file_obj.write.call_count == 1
    mock_temp_file_obj.write.assert_called_with("file '/absolute/video1.mp4'\n")


@patch('src.slide_to_video.video_engine.ffmpeg')
@patch('src.slide_to_video.video_engine.run_ffmpeg_command')
@patch('src.slide_to_video.video_engine.tempfile.NamedTemporaryFile')
@patch('src.slide_to_video.video_engine.os.remove')
@patch('src.slide_to_video.video_engine.os.path.abspath')
def test_concatenate_videos_empty_list(mock_abspath, mock_remove, mock_temp_file, mock_run_ffmpeg, mock_ffmpeg, video_engine):
    # Test with empty video list
    mock_temp_file_obj = Mock()
    mock_temp_file_obj.name = "/tmp/temp_file.txt"
    mock_temp_file_obj.__enter__ = Mock(return_value=mock_temp_file_obj)
    mock_temp_file_obj.__exit__ = Mock(return_value=None)
    mock_temp_file.return_value = mock_temp_file_obj
    
    mock_input = Mock()
    mock_output = Mock()
    mock_ffmpeg.input.return_value = mock_input
    mock_input.output.return_value = mock_output
    
    video_paths = []
    output_path = "final.mp4"
    
    video_engine.concatenate_videos(video_paths, output_path)
    
    # Should create temp file but write nothing
    assert mock_temp_file_obj.write.call_count == 0
    mock_run_ffmpeg.assert_called_once()
    mock_remove.assert_called_once_with("/tmp/temp_file.txt")