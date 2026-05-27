import zipfile

from src.slide_to_video.narration import (
    SCRIPT_MARKER,
    NarrationGenerator,
    SlideContent,
    SlideTextExtractor,
    create_narration_script,
)


def write_pptx(path, slides):
    with zipfile.ZipFile(path, "w") as archive:
        for index, paragraphs in enumerate(slides, start=1):
            xml_paragraphs = []
            for paragraph in paragraphs:
                runs = "".join(
                    f"<a:r><a:t>{part}</a:t></a:r>" for part in paragraph
                )
                xml_paragraphs.append(f"<a:p>{runs}</a:p>")
            archive.writestr(
                f"ppt/slides/slide{index}.xml",
                (
                    '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
                    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
                    "<p:cSld><p:spTree>"
                    + "".join(xml_paragraphs)
                    + "</p:spTree></p:cSld></p:sld>"
                ),
            )


def test_extract_from_pptx_merges_text_runs(tmp_path):
    pptx_path = tmp_path / "slides.pptx"
    write_pptx(
        pptx_path,
        [
            [["The ", "2nd", " Challenge"], ["1"], ["Real-world restoration"]],
            [["Results"], ["MiPlusCV wins"]],
        ],
    )

    slides = SlideTextExtractor().extract(str(pptx_path))

    assert len(slides) == 2
    assert slides[0].title == "The 2nd Challenge"
    assert slides[0].lines == ["The 2nd Challenge", "Real-world restoration"]
    assert slides[1].title == "Results"


def test_template_narration_matches_slide_count():
    slides = [
        SlideContent(index=1, title="Intro", lines=["Intro", "Challenge", "Task"]),
        SlideContent(index=2, title="Results", lines=["Results", "Team A wins"]),
    ]

    script = NarrationGenerator(language="zh-cn").generate(slides)

    assert script.count(SCRIPT_MARKER) == 1
    sections = [section.strip() for section in script.split(SCRIPT_MARKER)]
    assert len(sections) == 2
    assert "第 1 页" in sections[0]
    assert "第 2 页" in sections[1]


def test_create_narration_script_does_not_overwrite_by_default(tmp_path):
    pptx_path = tmp_path / "slides.pptx"
    script_path = tmp_path / "script.txt"
    write_pptx(pptx_path, [[["Intro"], ["Challenge"]]])
    script_path.write_text("manual edit", encoding="utf-8")

    result = create_narration_script(
        slide_path=str(pptx_path),
        output_path=str(script_path),
        overwrite=False,
    )

    assert result == str(script_path)
    assert script_path.read_text(encoding="utf-8") == "manual edit"
