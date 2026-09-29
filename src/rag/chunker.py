def chunk_pages(pages: list[dict], max_chars: int = 1500, overlap: int = 200) -> list[dict]:
    chunks = []
    for page in pages:
        text = page["text"]
        page_number = page["page"]
        start = 0
        while start < len(text):
            end = min(start + max_chars, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({"page": page_number, "text": chunk_text})
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)
    return chunks
