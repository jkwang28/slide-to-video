import os
from pathlib import Path
import shutil
import subprocess

from .utils import par_execute

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover - exercised in environments without deps
    fitz = None


class SlideEngine(object):
    def slide_to_images(self, slide_path: str, output_path: str):
        pdf_path = self.ensure_pdf(slide_path, output_path)
        return self.pdf_to_images(pdf_path, output_path)

    def ensure_pdf(self, slide_path: str, output_dir: str) -> str:
        path = Path(slide_path)
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return str(path)
        if suffix in {".ppt", ".pptx"}:
            sibling_pdf = path.with_suffix(".pdf")
            if sibling_pdf.exists():
                return str(sibling_pdf)
            return self.ppt_to_pdf(str(path), output_dir)
        raise ValueError(f"Unsupported slide format: {path.suffix}")

    def ppt_to_pdf(self, ppt_path: str, output_dir: str) -> str:
        converter = shutil.which("soffice") or shutil.which("libreoffice")
        if not converter:
            raise RuntimeError(
                "PPT/PPTX conversion requires LibreOffice. Install LibreOffice "
                "or place a same-named PDF next to the presentation."
            )

        os.makedirs(output_dir, exist_ok=True)
        source = Path(ppt_path)
        command = [
            converter,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            output_dir,
            str(source),
        ]
        result = subprocess.run(command, capture_output=True, check=False, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                "LibreOffice failed to convert the presentation to PDF: "
                f"{result.stderr or result.stdout}"
            )

        pdf_path = Path(output_dir) / f"{source.stem}.pdf"
        if not pdf_path.exists():
            raise RuntimeError(f"Expected converted PDF was not created: {pdf_path}")
        return str(pdf_path)

    def pdf_to_images(self, pdf_path, output_dir, dpi=300):
        if fitz is None:
            raise RuntimeError(
                "PyMuPDF is required to render PDF slides. Install project dependencies first."
            )
        # Open the PDF file
        pdf_document = fitz.open(pdf_path)

        pages = list(range(len(pdf_document)))
        image_paths = [f"{output_dir}/slide_{page_num + 1}.png" for page_num in pages]
        dpis = [dpi] * len(pages)
        pdf_documents = [pdf_document] * len(pages)
        par_execute(self.extract_one_page, pdf_documents, pages, image_paths, dpis)
        # Close the document
        pdf_document.close()
        return image_paths

    def extract_one_page(self, pdf_document, page_num, output_path, dpi=300):
        # Get the page
        page = pdf_document.load_page(page_num)

        zoom = dpi / 72

        mat = fitz.Matrix(zoom, zoom)

        # Render the page to an image with the specified resolution
        pix = page.get_pixmap(matrix=mat)

        # Save the image
        pix.save(output_path)
