"""Build the small JSON retrieval index used by the demo."""

import json
from pathlib import Path

from src.rag.retriever import GUIDELINES_DIR, INDEX_FILE
from src.rag.chunker import chunk_pages
from src.rag.pdf_loader import load_pdf_pages


def build_index() -> int:
    if INDEX_FILE.exists():
        return len(json.loads(INDEX_FILE.read_text(encoding="utf-8")))

    chunks = []
    for pdf_file in sorted(GUIDELINES_DIR.glob("*.pdf")):
        for chunk in chunk_pages(load_pdf_pages(pdf_file)):
            chunks.append({**chunk, "source": pdf_file.stem})

    INDEX_FILE.write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    return len(chunks)
