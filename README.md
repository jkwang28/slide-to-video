# slide-to-video

Convert a PDF/PPTX slide deck into a narrated video. The workflow is designed around an editable per-slide narration script, so you can generate a draft, edit the text, and rebuild the video without changing code.

## Features

- PDF slides to images via PyMuPDF.
- PPT/PPTX support through a same-named PDF, or LibreOffice conversion when no PDF exists.
- Editable narration scripts split by `NEWSLIDE`.
- Incremental rebuilds with `project.yaml` caching.
- TTS engines:
  - `qwen-tts`: Alibaba Cloud DashScope Qwen-TTS.
  - `cosyvoice`: Alibaba Cloud DashScope CosyVoice.
  - `minimax`: Alibaba Cloud DashScope MiniMax speech synthesis.
  - `mimo`: Xiaomi MiMo TTS.
  - `playht`: Play.ht.
  - `local`: optional Coqui XTTS voice cloning.
  - `mock`: silent audio for CI and pipeline testing.

## Requirements

- Python 3.9 to 3.11 recommended.
- `ffmpeg` available on `PATH`.
- Optional: LibreOffice for direct PPT/PPTX conversion when a same-named PDF is not available.

Install system tools:

```bash
# macOS
brew install ffmpeg
brew install --cask libreoffice

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y ffmpeg libreoffice
```

Install Python package:

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

For local Coqui voice cloning:

```bash
pip install ".[local]"
```

For development:

```bash
pip install ".[dev]"
pytest test
```

## Secrets

Never commit API keys. The repository ignores `*.key`.

Supported key sources:

- Environment variables:
  - `DASHSCOPE_API_KEY`
  - `MIMO_API_KEY`
  - `PLAY_HT_USER_ID`
  - `PLAY_HT_API_KEY`
- Local ignored key files:
  - `aliyun.key`
  - `mimo.key`

## Basic Workflow

### 1. Generate An Editable Script

Offline template draft:

```bash
slide-to-video \
  --slide input/deck.pptx \
  --output-dir output/deck \
  --draft-only \
  --draft-script output/deck/script.txt \
  --language zh-cn \
  --script-provider template
```

The generated script is plain text. Each slide section is separated by:

```text
NEWSLIDE
```

Edit `output/deck/script.txt` until the narration is right.

### 2. Build A Narrated Video

Alibaba Cloud Qwen-TTS:

```bash
slide-to-video \
  --model qwen-tts \
  --slide input/deck.pptx \
  --script output/deck/script.txt \
  --output-dir output/deck_qwen \
  --language zh-cn \
  --aliyun-api-key-file aliyun.key \
  --voice Cherry
```

Alibaba Cloud CosyVoice:

```bash
slide-to-video \
  --model cosyvoice \
  --slide input/deck.pptx \
  --script output/deck/script.txt \
  --output-dir output/deck_cosyvoice \
  --language zh-cn \
  --aliyun-api-key-file aliyun.key \
  --voice longanyang
```

Alibaba Cloud MiniMax:

```bash
slide-to-video \
  --model minimax \
  --slide input/deck.pptx \
  --script output/deck/script.txt \
  --output-dir output/deck_minimax \
  --language zh-cn \
  --aliyun-api-key-file aliyun.key \
  --aliyun-minimax-model MiniMax/speech-2.8-hd \
  --voice male-qn-qingse \
  --aliyun-minimax-language-boost Chinese \
  --aliyun-minimax-output-format url
```

Xiaomi MiMo:

```bash
slide-to-video \
  --model mimo \
  --slide input/deck.pptx \
  --script output/deck/script.txt \
  --output-dir output/deck_mimo \
  --language zh-cn \
  --mimo-api-key-file mimo.key
```

The final video is written to:

```text
<output-dir>/output.mp4
```

## PPT/PPTX Handling

For stable rendering, place a PDF with the same basename next to the PPTX:

```text
input/deck.pptx
input/deck.pdf
```

When both exist, the tool uses `deck.pdf` for slide rendering and `deck.pptx` for text extraction. If no sibling PDF exists, it attempts conversion through LibreOffice.

## Alibaba Cloud Notes

For 华北 2（北京）:

- API key guide: <https://help.aliyun.com/zh/model-studio/get-api-key>
- MiniMax synchronous speech synthesis API: <https://help.aliyun.com/zh/model-studio/minimax-synchronous-speech-synthesis-api>
- DashScope HTTP API base URL: `https://dashscope.aliyuncs.com/api/v1`
- OpenAI-compatible text base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`

This project uses the non-realtime TTS HTTP APIs because they fit batch video generation:

- `qwen-tts`: `/services/aigc/multimodal-generation/generation`
- `cosyvoice`: `/services/audio/tts/SpeechSynthesizer`
- `minimax`: `/services/aigc/multimodal-generation/generation`

The Alibaba Cloud engines run TTS sequentially to avoid API rate-limit errors during multi-slide generation.

## Common Commands

List all options:

```bash
slide-to-video --help
```

Smoke-test the video pipeline without API keys:

```bash
slide-to-video \
  --model mock \
  --slide example/slide.pdf \
  --script example/script.txt \
  --output-dir output-smoke
```

Run tests:

```bash
pytest test
```

## Project Structure

```text
src/slide_to_video/
  aliyun.py                 # DashScope HTTP client
  mimo.py                   # MiMo OpenAI-compatible client
  narration.py              # PPT/PDF text extraction and script drafting
  project.py                # caching and orchestration
  script_engine.py          # NEWSLIDE script splitting
  slide_engine.py           # PDF/PPTX rendering
  video_engine.py           # ffmpeg video assembly
  tts_engine/               # pluggable TTS engines
```

## Acknodeglement

Thanks the codebase from [slide-to-video](https://github.com/llm-believer/slide-to-video). I use codex to reconstruct it and add new features. 
