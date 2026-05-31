# slide-to-video

Convert a PDF/PPTX slide deck into a narrated video. The workflow is designed around an editable per-slide narration script, so you can generate a draft, edit the text, and rebuild the video without changing code.

## Features

- PDF slides to images via PyMuPDF.
- PPT/PPTX support through a same-named PDF, or LibreOffice conversion when no PDF exists.
- Editable narration scripts split by `NEWSLIDE`, with optional per-slide delay overrides.
- Incremental rebuilds with `project.yaml` caching.
- TTS-only review mode for generating per-slide audio before video assembly.
- TTS engines:
  - `qwen-tts`: Alibaba Cloud DashScope Qwen-TTS.
  - `cosyvoice`: Alibaba Cloud DashScope CosyVoice.
  - `minimax`: Alibaba Cloud DashScope MiniMax speech synthesis.
  - `mimo`: Xiaomi MiMo TTS.
  - `playht`: Play.ht.
  - `openai-tts`: example OpenAI TTS integration configured through YAML.
  - `local`: optional Coqui XTTS voice cloning.
  - `mock`: silent audio for CI and pipeline testing.

## Requirements

- Python 3.8 or newer. Python 3.9 to 3.11 is recommended.
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

### 1. Generate Or Write An Editable Script

Create an offline template draft:

```bash
slide-to-video \
  --slide input/deck.pptx \
  --output-dir output/deck \
  --draft-only \
  --draft-script output/deck/script.txt \
  --language zh-cn \
  --script-provider template
```

Or generate a draft with MiMo:

```bash
slide-to-video \
  --slide input/deck.pptx \
  --output-dir output/deck \
  --draft-only \
  --draft-script output/deck/script.txt \
  --language zh-cn \
  --script-provider mimo \
  --mimo-api-key-file mimo.key
```

Edit `output/deck/script.txt` until the narration text is right.

### 2. Generate TTS Audio For Review

Use `--tts-only` to generate one WAV file per slide and stop before ffmpeg video assembly:

```bash
slide-to-video \
  --model qwen-tts \
  --slide input/deck.pptx \
  --script output/deck/script.txt \
  --output-dir output/deck_qwen \
  --language zh-cn \
  --aliyun-api-key-file aliyun.key \
  --aliyun-qwen-tts-model qwen3-tts-flash \
  --voice Cherry \
  --delay 1.0 \
  --tts-only
```

The per-slide audio files are written to:

```text
<output-dir>/sub_paragraph_1.wav
<output-dir>/sub_paragraph_2.wav
...
```

Listen to the WAV files. If a slide sounds wrong, edit only that slide section in the script and run the same `--tts-only` command again. The cache will re-synthesize only changed slide sections.

### 3. Assemble The Final Video

After all WAV files sound right, run the same command without `--tts-only`:

```bash
slide-to-video \
  --model qwen-tts \
  --slide input/deck.pptx \
  --script output/deck/script.txt \
  --output-dir output/deck_qwen \
  --language zh-cn \
  --aliyun-api-key-file aliyun.key \
  --aliyun-qwen-tts-model qwen3-tts-flash \
  --voice Cherry \
  --delay 1.0
```

Cached audio is reused, so this step should generate `sub_paragraph_*.mp4` and concatenate them into:

```text
<output-dir>/output.mp4
```

### One-Step Video Generation

You can skip the review stage and build the final video in one command by omitting `--tts-only` from the first run. This is faster to type but less convenient when you need to correct pronunciation or narration text.

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

## Script Format

Narration scripts are plain text. Each non-empty section corresponds to one slide and sections are separated by `NEWSLIDE`:

```text
This is the narration for slide 1.

NEWSLIDE

This is the narration for slide 2.
```

You can add a per-slide end delay by appending a config block after `===`:

```text
This slide needs a slightly longer pause before moving on.
===
#delay: 2.5

NEWSLIDE

This is the next slide.
```

The global `--delay` value is split around each slide's audio. The first slide has no leading silence. Per-slide `#delay` overrides the ending delay for that slide.

Keep cloud TTS sections reasonably short. If a provider rejects a long section, split or rewrite that slide narration and run `--tts-only` again.

## Cache And Rebuild Behavior

The output directory contains a `project.yaml` cache file. The cache tracks rendered slide images, split script sections, and whether each item has already been built.

- Reusing the same `--output-dir` enables incremental rebuilds.
- Editing one script section and rerunning `--tts-only` re-synthesizes only that section.
- Running without `--tts-only` after the audio is cached builds videos from the existing WAV files.
- Changing model, voice, speed, language, delay, slide count, or other config resets the cache for the affected project.
- Using a new `--output-dir` creates an independent experiment and will not overwrite earlier outputs.

If an output directory already exists but does not contain `project.yaml`, the tool treats it as stale generated output and recreates it.

Advanced retry: if you want to re-synthesize a slide without changing its text, set that script item's `force_reset` to `true` in `project.yaml`, run with `--tts-only`, then set it back to `false`.

## Config Files

Every CLI option can also be stored in a YAML config file:

```yaml
model: qwen-tts
slide: input/deck.pptx
script: output/deck/script.txt
output_dir: output/deck_qwen
language: zh-cn
delay: 1.0
aliyun_api_key_file: aliyun.key
aliyun_qwen_tts_model: qwen3-tts-flash
voice: Cherry
aliyun_language_type: Chinese
aliyun_tts_instruction: 请用自然、清晰、适合技术演示的语气朗读。
```

Run it with:

```bash
slide-to-video --config config.yaml
```

CLI arguments override values loaded from `--config`.

## Script Dictionary

Use `--script-dict` for simple terminology replacements before TTS. The file format is one replacement per line:

```text
original term: replacement term
CVPR: C V P R
Face26: Face twenty six
```

Then run:

```bash
slide-to-video \
  --model qwen-tts \
  --slide input/deck.pptx \
  --script output/deck/script.txt \
  --output-dir output/deck_qwen \
  --language zh-cn \
  --aliyun-api-key-file aliyun.key \
  --aliyun-qwen-tts-model qwen3-tts-flash \
  --voice Cherry \
  --script-dict replacements.txt \
  --tts-only
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

Qwen-TTS model and voice compatibility is model-specific. If DashScope returns an `InvalidParameter` error for `input.voice`, choose a voice supported by that model or switch to a compatible model. For example, `qwen3-tts-flash-2025-11-27` supports voices that are not accepted by `qwen-tts-latest` in some accounts.

Useful Qwen-TTS options:

```bash
--aliyun-qwen-tts-model qwen3-tts-flash
--voice Cherry
--aliyun-language-type Chinese
--aliyun-tts-instruction "Read clearly and professionally."
```

MiniMax long narrations should use URL output to avoid response-size limits:

```bash
--aliyun-minimax-output-format url
```

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

## Acknowledgement

Thanks to the original [slide-to-video](https://github.com/llm-believer/slide-to-video) project. This repository reconstructs the workflow and adds new TTS and narration features.
