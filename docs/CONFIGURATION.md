# Configuration

The CLI accepts options directly or from a YAML file with `--config`.

## Required Build Fields

```yaml
model: qwen-tts
slide: input/deck.pptx
script: output/deck/script.txt
output_dir: output/deck_qwen
language: zh-cn
speech_speed: 1.0
delay: 1.0
```

`slide` may be a PDF, PPT, or PPTX. For PPT/PPTX, keep a same-named PDF next to the deck when possible for deterministic rendering.

## Draft Script Fields

```yaml
slide: input/deck.pptx
output_dir: output/deck
draft_only: true
draft_script: output/deck/script.txt
language: zh-cn
script_provider: template
```

Set `script_provider: mimo` to use Xiaomi MiMo for draft generation.

## Alibaba Cloud DashScope

Default Beijing HTTP API base URL:

```yaml
aliyun_base_url: https://dashscope.aliyuncs.com/api/v1
aliyun_api_key_file: aliyun.key
```

### Qwen-TTS

```yaml
model: qwen-tts
aliyun_qwen_tts_model: qwen3-tts-flash
aliyun_qwen_voice: Cherry
aliyun_language_type: Chinese
```

Optional instruction fields:

```yaml
aliyun_tts_instruction: 请用自然、清晰、适合技术演示的语气朗读。
aliyun_optimize_instructions: true
```

Instruction support depends on the selected Qwen-TTS model.

### CosyVoice

```yaml
model: cosyvoice
aliyun_cosyvoice_model: cosyvoice-v3-flash
aliyun_cosyvoice_voice: longanyang
aliyun_sample_rate: 24000
```

### MiniMax

```yaml
model: minimax
aliyun_minimax_model: MiniMax/speech-2.8-hd
aliyun_minimax_voice: male-qn-qingse
aliyun_minimax_sample_rate: 32000
aliyun_minimax_language_boost: Chinese
aliyun_minimax_output_format: url
```

Optional MiniMax fields:

```yaml
aliyun_minimax_emotion: calm
aliyun_minimax_volume: 1.0
aliyun_minimax_pitch: 0
aliyun_minimax_bitrate: 128000
aliyun_minimax_channel: 1
aliyun_minimax_text_normalization: true
aliyun_minimax_aigc_watermark: false
```

MiniMax supports `wav`, `mp3`, and `flac` synthesis formats in non-streaming mode. The batch video pipeline writes `.wav` files by default.

Use `aliyun_minimax_output_format: url` for long narration. `hex` is supported for short clips, but large inline audio responses can exceed DashScope response-size limits.

For these engines, `--voice` is accepted as a shorthand when no engine-specific voice option is set.

## Xiaomi MiMo

```yaml
model: mimo
mimo_api_key_file: mimo.key
mimo_tts_model: mimo-v2.5-tts
mimo_voice: mimo_default
mimo_tts_instruction: 请用自然、清晰、适合技术演示的语气朗读。
```

Default base URLs:

- `sk-...`: `https://api.xiaomimimo.com/v1`
- `tp-...`: `https://token-plan-cn.xiaomimimo.com/v1`

Override with:

```yaml
mimo_base_url: https://your-endpoint.example/v1
```

## Local Coqui

Install optional dependencies first:

```bash
pip install ".[local]"
```

Then configure:

```yaml
model: local
voice: path/to/voice-sample.wav
language: zh-cn
```

## Timing

`delay` controls silence around each slide transition. Per-slide override is supported in the script:

```text
Narration for one slide.
===
#delay: 3.0
NEWSLIDE
Next slide narration.
```
