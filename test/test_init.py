from src.slide_to_video import hello


def test_hello_function():
    result = hello()
    assert result == "Hello from slide-to-video!"
    assert isinstance(result, str)


def test_hello_function_return_type():
    result = hello()
    assert isinstance(result, str)
    assert len(result) > 0
