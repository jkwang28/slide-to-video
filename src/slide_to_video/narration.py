from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import textwrap
import xml.etree.ElementTree as ET
import zipfile
from typing import Iterable, List, Optional

from .mimo import MimoClient


SCRIPT_MARKER = "NEWSLIDE"


@dataclass
class SlideContent:
    index: int
    title: str
    lines: List[str]

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


class SlideTextExtractor:
    def extract(self, slide_path: str) -> List[SlideContent]:
        path = Path(slide_path)
        suffix = path.suffix.lower()
        if suffix in {".ppt", ".pptx"}:
            return self.extract_from_pptx(path)
        if suffix == ".pdf":
            return self.extract_from_pdf(path)
        raise ValueError(f"Unsupported slide format for narration: {path.suffix}")

    def extract_from_pptx(self, pptx_path: Path) -> List[SlideContent]:
        slide_pattern = re.compile(r"ppt/slides/slide(\d+)\.xml$")
        contents = []
        with zipfile.ZipFile(pptx_path) as archive:
            slide_names = [
                name for name in archive.namelist() if slide_pattern.match(name)
            ]
            slide_names.sort(key=lambda name: int(slide_pattern.match(name).group(1)))
            for slide_name in slide_names:
                match = slide_pattern.match(slide_name)
                index = int(match.group(1))
                lines = self._extract_pptx_paragraphs(archive.read(slide_name))
                contents.append(self._build_slide_content(index, lines))
        return contents

    def extract_from_pdf(self, pdf_path: Path) -> List[SlideContent]:
        try:
            import fitz
        except ImportError as exc:  # pragma: no cover - depends on local env
            raise RuntimeError(
                "PyMuPDF is required to extract narration text from PDF slides."
            ) from exc

        contents = []
        document = fitz.open(pdf_path)
        try:
            for page_index in range(len(document)):
                page = document.load_page(page_index)
                lines = self._split_pdf_text(page.get_text())
                contents.append(self._build_slide_content(page_index + 1, lines))
        finally:
            document.close()
        return contents

    def _extract_pptx_paragraphs(self, xml_bytes: bytes) -> List[str]:
        root = ET.fromstring(xml_bytes)
        paragraphs = []
        for paragraph in root.iter():
            if not paragraph.tag.endswith("}p"):
                continue
            text = "".join(
                node.text or "" for node in paragraph.iter() if node.tag.endswith("}t")
            )
            text = self._clean_line(text)
            if text:
                paragraphs.append(text)
        return self._dedupe_preserve_order(paragraphs)

    def _split_pdf_text(self, text: str) -> List[str]:
        return [
            cleaned
            for cleaned in (self._clean_line(line) for line in text.splitlines())
            if cleaned
        ]

    def _build_slide_content(self, index: int, raw_lines: Iterable[str]) -> SlideContent:
        lines = [line for line in raw_lines if not self._is_low_value_line(line)]
        title = lines[0] if lines else f"Slide {index}"
        return SlideContent(index=index, title=title, lines=lines)

    def _clean_line(self, line: str) -> str:
        return re.sub(r"\s+", " ", line).strip()

    def _dedupe_preserve_order(self, lines: Iterable[str]) -> List[str]:
        seen = set()
        result = []
        for line in lines:
            key = line.casefold()
            if key not in seen:
                seen.add(key)
                result.append(line)
        return result

    def _is_low_value_line(self, line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return True
        if stripped.isdigit() and len(stripped) <= 2:
            return True
        return False


class NarrationGenerator:
    def __init__(
        self,
        *,
        language: str = "zh-cn",
        provider: str = "template",
        config: Optional[dict] = None,
    ):
        self.language = language
        self.provider = provider
        self.config = config or {}

    def generate(self, slides: List[SlideContent]) -> str:
        if self.provider == "mimo":
            return self._generate_with_mimo(slides)
        if self.provider != "template":
            raise ValueError(f"Unknown narration provider: {self.provider}")
        sections = [self._generate_template_section(slide) for slide in slides]
        return self.join_sections(sections)

    def join_sections(self, sections: List[str]) -> str:
        cleaned_sections = [section.strip() for section in sections if section.strip()]
        return f"\n\n{SCRIPT_MARKER}\n\n".join(cleaned_sections) + "\n"

    def _generate_template_section(self, slide: SlideContent) -> str:
        highlights = self._select_highlights(slide)
        if self.language.lower().startswith("zh"):
            if highlights:
                body = "；".join(highlights)
                return (
                    f"第 {slide.index} 页，{slide.title}。"
                    f"这一页的核心信息包括：{body}。"
                    "这里我会把这些要点串起来，说明它们在整份报告中的作用。"
                )
            return f"第 {slide.index} 页，{slide.title}。这一页用于承接前后的内容。"

        if highlights:
            body = "; ".join(highlights)
            return (
                f"On slide {slide.index}, {slide.title}. "
                f"The main points are: {body}. "
                "I will connect these points to the larger story of the presentation."
            )
        return f"On slide {slide.index}, {slide.title}. This slide connects the surrounding sections."

    def _select_highlights(self, slide: SlideContent, max_items: int = 4) -> List[str]:
        title_key = slide.title.casefold()
        candidates = []
        for line in slide.lines[1:]:
            line = line.strip(" .")
            if not line or line.casefold() == title_key:
                continue
            if len(line) <= 2:
                continue
            candidates.append(line)
        return candidates[:max_items]

    def _generate_with_mimo(self, slides: List[SlideContent]) -> str:
        client = MimoClient(self.config)
        model = self.config.get("mimo_text_model", "mimo-v2.5")
        max_tokens = int(self.config.get("mimo_text_max_tokens", 8192))
        prompt = self._build_mimo_prompt(slides)
        content = client.generate_text(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior presentation script writer. "
                        "Return only the requested editable narration script."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=max_tokens,
        )
        return self._normalize_model_script(content, expected_sections=len(slides))

    def _build_mimo_prompt(self, slides: List[SlideContent]) -> str:
        language_instruction = (
            "中文"
            if self.language.lower().startswith("zh")
            else "English"
        )
        slide_blocks = []
        for slide in slides:
            slide_blocks.append(
                f"Slide {slide.index}: {slide.title}\n{slide.text}"
            )
        return textwrap.dedent(
            f"""
            请根据下面的 PPT 内容生成一版可编辑的逐页旁白稿。

            要求：
            - 使用{language_instruction}。
            - 必须生成 {len(slides)} 段，每段对应一页 slide。
            - 段与段之间只使用一行 {SCRIPT_MARKER} 分隔。
            - 不要输出标题、编号、Markdown、舞台提示或解释。
            - 每段适合 20 到 45 秒口播，语气专业、自然，适合技术报告。
            - 保留关键英文术语、人名、团队名和指标名，不要臆造论文中没有的信息。

            PPT 内容：
            {chr(10).join(slide_blocks)}
            """
        ).strip()

    def _normalize_model_script(self, script: str, expected_sections: int) -> str:
        script = script.strip()
        sections = [section.strip() for section in script.split(SCRIPT_MARKER)]
        sections = [section for section in sections if section]
        if len(sections) != expected_sections:
            raise RuntimeError(
                "MiMo narration response did not match slide count: "
                f"expected {expected_sections}, got {len(sections)}"
            )
        return self.join_sections(sections)


def create_narration_script(
    *,
    slide_path: str,
    output_path: str,
    language: str = "zh-cn",
    provider: str = "template",
    overwrite: bool = False,
    config: Optional[dict] = None,
) -> str:
    output = Path(output_path)
    if output.exists() and not overwrite:
        return str(output)

    output.parent.mkdir(parents=True, exist_ok=True)
    slides = SlideTextExtractor().extract(slide_path)
    script = NarrationGenerator(
        language=language,
        provider=provider,
        config=config,
    ).generate(slides)
    output.write_text(script, encoding="utf-8")
    return str(output)
