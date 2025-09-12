# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python tool that converts slide decks (PDF) into videos with voice narration. It supports multiple TTS engines (local Coqui TTS and remote Play.ht) and multiple languages.

## Key Commands

### Installation and Setup
```bash
pip install .              # Install the package
slide-to-video --help      # View all available options
```

### Testing
```bash
pytest test               # Run tests (configured in .vscode/settings.json)
pytest --cov=src --cov-report=term-missing test/  # Run tests with coverage report
pytest --cov=src --cov-report=html test/          # Generate HTML coverage report
```

### Code Quality
```bash
ruff check                # Run linting (ruff is included in dependencies)
pyright                   # Run type checking (dev dependency)
```

### Running the Tool
```bash
# Basic usage with local TTS
slide-to-video --model local --slide example/slide.pdf --script example/script.txt --voice example/sample.mp3 --output-dir output

# With additional configuration
slide-to-video --model MODEL_NAME --slide slide.pdf --script script.txt --output-dir OUTPUT_PATH --config config.yaml
```

## Architecture

The codebase follows a modular engine-based architecture:

### Core Components
- **`src/slide_to_video/lib.py`**: Main entry point with `slide_to_video()` function
- **`src/slide_to_video/project.py`**: Project management, caching, and coordination
- **`src/script/__init__.py`**: CLI interface using Typer

### Engine System
All processing is handled by specialized engines in `src/slide_to_video/`:

- **`slide_engine.py`**: Converts PDF slides to images using PyMuPDF
- **`script_engine.py`**: Processes text scripts (splits by `NEWSLIDE` marker)  
- **`video_engine.py`**: Combines slides and audio into final video using FFmpeg
- **`tts_engine/`**: Text-to-speech processing with pluggable backends
  - **`base_engine.py`**: Abstract TTS interface
  - **`registery.py`**: Engine registration system
  - **`local.py`**: Coqui TTS implementation
  - **`playht.py`**: Play.ht API integration

### Project System
- Uses `project.yaml` for caching and incremental builds
- Tracks MD5 hashes to skip unchanged content
- Supports force regeneration via `force_reset` flags

### Dependencies
- **Core**: PyMuPDF (PDF), FFmpeg (video), Coqui TTS, Pydub (audio)
- **CLI**: Typer, Click  
- **Config**: PyYAML
- **Dev**: pytest, pyright, ruff, pyinstrument, coverage, pytest-cov, pytest-mock

### Testing & Coverage
- **Test Coverage**: Comprehensive unit tests covering 70% of codebase  
- **Test Performance**: All 124 tests run in <3 seconds with proper mocking
- **Test Structure**: 11 optimized test files organized by module in `test/` directory
- **Test Status**: ✅ ALL TESTS PASSING
- **Key Test Files**:
  - `test_utils.py`: Utility functions (MD5, file operations, parallel execution)
  - `test_script_engine_comprehensive.py`: Script parsing and processing  
  - `test_slide_engine.py`: PDF to image conversion
  - `test_tts_engine_fast.py`: Optimized TTS engine system tests with mocking
  - `test_tts_engine_integration.py`: TTS engine integration and configuration
  - `test_video_engine.py`: Video generation and concatenation
  - `test_lib_simple.py`: Main library functions
  - `test_cli_comprehensive.py`: Command-line interface
  - `test_project.py`: Project management and data structures

## Adding New TTS Engines

To add a new TTS engine:
1. Create a new class in `src/slide_to_video/tts_engine/` inheriting from `base_engine.TTSEngine`
2. Register it using `register_engine()` (see `local.py` example)
3. The engine will automatically appear in CLI choices

## Language Support
Supports 18 languages: en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, hu, ko, ja, hi

## Key Files to Understand
- `src/slide_to_video/project.py:30-50`: Item caching system
- `src/script/__init__.py:14-85`: CLI parameter handling  
- `src/slide_to_video/tts_engine/registery.py`: Engine discovery
- `pyproject.toml`: Build configuration and dependencies