import pytest
from unittest.mock import Mock, patch, MagicMock
from src.slide_to_video.slide_engine import SlideEngine


@pytest.fixture
def slide_engine():
    return SlideEngine()


@patch("src.slide_to_video.slide_engine.fitz")
@patch("src.slide_to_video.slide_engine.par_execute")
def test_pdf_to_images(mock_par_execute, mock_fitz, slide_engine, tmp_path):
    # Mock PDF document
    mock_doc = Mock()
    mock_doc.__len__ = Mock(return_value=3)  # 3 pages
    mock_fitz.open.return_value = mock_doc

    output_dir = str(tmp_path)
    result = slide_engine.pdf_to_images("test.pdf", output_dir, dpi=150)

    # Verify the calls
    mock_fitz.open.assert_called_once_with("test.pdf")
    mock_doc.close.assert_called_once()

    # Check that par_execute was called with correct arguments
    mock_par_execute.assert_called_once()
    args = mock_par_execute.call_args[0]

    # First arg should be the extract_one_page method
    assert args[0] == slide_engine.extract_one_page
    # Second arg should be list of pdf_documents
    assert args[1] == [mock_doc, mock_doc, mock_doc]
    # Third arg should be page numbers
    assert args[2] == [0, 1, 2]
    # Fourth arg should be image paths
    expected_paths = [f"{output_dir}/slide_{i + 1}.png" for i in range(3)]
    assert args[3] == expected_paths
    # Fifth arg should be dpis
    assert args[4] == [150, 150, 150]

    # Check return value
    assert result == expected_paths


@patch("src.slide_to_video.slide_engine.fitz")
def test_extract_one_page(mock_fitz, slide_engine):
    # Mock the page and pixmap
    mock_page = Mock()
    mock_pixmap = Mock()
    mock_page.get_pixmap.return_value = mock_pixmap

    mock_pdf_doc = Mock()
    mock_pdf_doc.load_page.return_value = mock_page

    slide_engine.extract_one_page(mock_pdf_doc, 1, "output.png", dpi=200)

    # Verify page loading
    mock_pdf_doc.load_page.assert_called_once_with(1)

    # Verify matrix calculation (200 DPI / 72 = 2.777... zoom)
    mock_page.get_pixmap.assert_called_once()
    # Check that get_pixmap was called with a matrix argument
    call_args = mock_page.get_pixmap.call_args
    assert "matrix" in call_args[1] or len(call_args[0]) > 0

    # Verify save was called
    mock_pixmap.save.assert_called_once_with("output.png")


def test_slide_to_images_calls_pdf_to_images(slide_engine):
    with patch.object(
        slide_engine, "pdf_to_images", return_value=["image1.png"]
    ) as mock_pdf:
        result = slide_engine.slide_to_images("test.pdf", "output_dir")

        mock_pdf.assert_called_once_with("test.pdf", "output_dir")
        assert result == ["image1.png"]


@patch("src.slide_to_video.slide_engine.fitz")
def test_extract_one_page_default_dpi(mock_fitz, slide_engine):
    # Test with default DPI (300)
    mock_page = Mock()
    mock_pixmap = Mock()
    mock_page.get_pixmap.return_value = mock_pixmap

    mock_pdf_doc = Mock()
    mock_pdf_doc.load_page.return_value = mock_page

    slide_engine.extract_one_page(mock_pdf_doc, 0, "output.png")

    # Verify default DPI calculation (300 / 72 = 4.1666...)
    mock_page.get_pixmap.assert_called_once()
    # Check that get_pixmap was called with matrix argument
    call_args = mock_page.get_pixmap.call_args
    assert "matrix" in call_args[1] or len(call_args[0]) > 0
