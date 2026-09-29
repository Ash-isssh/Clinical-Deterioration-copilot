from pathlib import Path
from pypdf import PdfReader


def load_pdf_pages(pdf_path: str | Path) -> list[dict]:
    """Extract text from a PDF one page at a time."""
    reader = PdfReader(str(pdf_path))
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append({"page": page_number, "text": text})
    return pages
