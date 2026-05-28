import typer
from typing import Optional
import yaml
import click
from slide_to_video.lib import slide_to_video
from slide_to_video.project import ProjectConfig
from slide_to_video.tts_engine.registery import get_all_engine_names


app = typer.Typer()


@app.command()
def generate(
    model: Optional[str] = typer.Option(
        None,
        help="TTS engine to use, such as qwen-tts, cosyvoice, minimax, mimo, playht, local, or mock.",
        case_sensitive=False,
        click_type=click.Choice(get_all_engine_names()),
    ),
    slide: str = typer.Option(..., help="Slide to use"),
    script: Optional[str] = typer.Option(
        None,
        help="Editable narration script to use. If omitted, use --draft-script or --draft-only first.",
    ),
    output_dir: str = typer.Option(..., help="Output directory"),
    voice: Optional[str] = typer.Option(
        None, help="Voice sample path or ID. Depends on the model."
    ),
    speech_speed: Optional[float] = typer.Option(
        None, help="Speed of the speech. Default value: 1.0."
    ),
    delay: Optional[float] = typer.Option(
        None, help="Delay between each slide in seconds. Default value: 2.0."
    ),
    script_dict: Optional[str] = typer.Option(
        None,
        help='Dictionary to replace the script. Each line should follow the format "original_text: new_text"',
    ),
    language: Optional[str] = typer.Option(
        None,
        case_sensitive=False,
        click_type=click.Choice(
            [
                "en",
                "es",
                "fr",
                "de",
                "it",
                "pt",
                "pl",
                "tr",
                "ru",
                "nl",
                "cs",
                "ar",
                "zh-cn",
                "hu",
                "ko",
                "ja",
                "hi",
            ]
        ),
        help="Language of the text. Default value: en.",
    ),
    config: Optional[str] = typer.Option(None, help="Path to yaml config file"),
    draft_script: Optional[str] = typer.Option(
        None,
        help="Path for generated editable narration script.",
    ),
    draft_only: bool = typer.Option(
        False,
        help="Generate the editable narration script and stop before TTS/video.",
    ),
    regenerate_draft: bool = typer.Option(
        False,
        help="Overwrite an existing generated narration script.",
    ),
    script_provider: Optional[str] = typer.Option(
        None,
        case_sensitive=False,
        click_type=click.Choice(["template", "mimo"]),
        help="Narration generator to use when creating a draft script.",
    ),
    mimo_api_key_file: Optional[str] = typer.Option(
        None,
        help="Path to MiMo API key file. Defaults to mimo.key when present.",
    ),
    mimo_base_url: Optional[str] = typer.Option(
        None,
        help="MiMo OpenAI-compatible base URL.",
    ),
    mimo_text_model: Optional[str] = typer.Option(
        None,
        help="MiMo model for draft script generation.",
    ),
    mimo_tts_model: Optional[str] = typer.Option(
        None,
        help="MiMo TTS model for speech synthesis.",
    ),
    mimo_voice: Optional[str] = typer.Option(
        None,
        help="MiMo built-in voice ID, such as mimo_default, default_zh, Mia, Chloe.",
    ),
    mimo_tts_instruction: Optional[str] = typer.Option(
        None,
        help="Natural language style instruction for MiMo TTS.",
    ),
    aliyun_api_key_file: Optional[str] = typer.Option(
        None,
        help="Path to Aliyun DashScope API key file. Defaults to aliyun.key when present.",
    ),
    aliyun_base_url: Optional[str] = typer.Option(
        None,
        help="Aliyun DashScope HTTP API base URL. Defaults to Beijing region.",
    ),
    aliyun_qwen_tts_model: Optional[str] = typer.Option(
        None,
        help="Aliyun Qwen-TTS model. Default: qwen3-tts-flash.",
    ),
    aliyun_cosyvoice_model: Optional[str] = typer.Option(
        None,
        help="Aliyun CosyVoice model. Default: cosyvoice-v3-flash.",
    ),
    aliyun_minimax_model: Optional[str] = typer.Option(
        None,
        help="Aliyun MiniMax model. Default: MiniMax/speech-2.8-hd.",
    ),
    aliyun_voice: Optional[str] = typer.Option(
        None,
        help="Aliyun voice name shared by qwen-tts/cosyvoice/minimax unless engine-specific voice is set.",
    ),
    aliyun_qwen_voice: Optional[str] = typer.Option(
        None,
        help="Aliyun Qwen-TTS voice. Default: Cherry.",
    ),
    aliyun_cosyvoice_voice: Optional[str] = typer.Option(
        None,
        help="Aliyun CosyVoice voice. Default: longanyang.",
    ),
    aliyun_minimax_voice: Optional[str] = typer.Option(
        None,
        help="Aliyun MiniMax voice ID. Default: male-qn-qingse.",
    ),
    aliyun_minimax_emotion: Optional[str] = typer.Option(
        None,
        help="Aliyun MiniMax emotion, such as happy, sad, angry, surprised, calm.",
    ),
    aliyun_language_type: Optional[str] = typer.Option(
        None,
        help="Aliyun Qwen-TTS language_type, such as Chinese or English.",
    ),
    aliyun_minimax_language_boost: Optional[str] = typer.Option(
        None,
        help="Aliyun MiniMax language_boost, such as Chinese, English, or auto.",
    ),
    aliyun_tts_instruction: Optional[str] = typer.Option(
        None,
        help="Natural language style instruction for Aliyun TTS models that support it.",
    ),
    aliyun_optimize_instructions: Optional[bool] = typer.Option(
        None,
        help="Whether Qwen-TTS should optimize instructions when supported.",
    ),
    aliyun_sample_rate: Optional[int] = typer.Option(
        None,
        help="Aliyun CosyVoice sample rate. Default: 24000.",
    ),
    aliyun_minimax_sample_rate: Optional[int] = typer.Option(
        None,
        help="Aliyun MiniMax sample rate. Default: 32000.",
    ),
    aliyun_minimax_output_format: Optional[str] = typer.Option(
        None,
        case_sensitive=False,
        click_type=click.Choice(["url", "hex"]),
        help="Aliyun MiniMax response format. Default: url.",
    ),
    ctx: typer.Context = typer.Option(None),
):
    # Load the project config
    if config:
        with open(config, "r") as f:
            raw_config = yaml.safe_load(f)
    else:
        raw_config = {}
    for key, value in ctx.params.items():
        if value is not None:
            if not (isinstance(value, bool) and value is False and key in raw_config):
                raw_config[key] = value
        elif key not in raw_config:
            if key == "speech_speed":
                raw_config[key] = 1.0
            elif key == "delay":
                raw_config[key] = 2.0
            elif key == "language":
                raw_config[key] = "en"
            elif key == "script_provider":
                raw_config[key] = "template"

    project_config = ProjectConfig(raw_config)
    slide_to_video(project_config=project_config)


def main():
    app()
