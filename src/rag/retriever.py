"""Small local keyword retriever over the bundled guideline corpus."""

from functools import lru_cache
import json
from pathlib import Path
import re

from src.rag.chunker import chunk_pages
from src.rag.pdf_loader import load_pdf_pages
from src.rag.query_builder import build_clinical_query

BASE_DIR = Path(__file__).resolve().parents[2]
GUIDELINES_DIR = BASE_DIR / "data" / "guidelines" / "documents"
INDEX_FILE = BASE_DIR / "data" / "guidelines" / "index.json"


@lru_cache(maxsize=1)
def load_guideline_chunks() -> tuple[dict, ...]:
    """Load the prebuilt index. Fall back to PDF extraction when absent."""
    if INDEX_FILE.exists():
        return tuple(json.loads(INDEX_FILE.read_text(encoding="utf-8")))

    all_chunks = []
    for pdf_file in sorted(GUIDELINES_DIR.glob("*.pdf")):
        for chunk in chunk_pages(load_pdf_pages(pdf_file)):
            all_chunks.append({**chunk, "source": pdf_file.stem})
    return tuple(all_chunks)


def tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(token) > 2}


def retrieve(query: str, k: int = 3) -> list[dict]:
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    results = []
    for chunk in load_guideline_chunks():
        matches = query_tokens & tokenize(chunk["text"])
        if not matches:
            continue
        score = len(matches) / len(query_tokens)
        results.append({
            "source": chunk["source"],
            "page": chunk["page"],
            "score": round(score, 4),
            "text": chunk["text"],
        })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:k]


retrieve_guidelines = retrieve


def retrieve_for_patient(state, k: int = 3) -> dict:
    query = build_clinical_query(state)
    return {"query": query, "evidence": retrieve(query, k)}
