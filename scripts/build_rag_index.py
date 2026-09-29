"""Build data/guidelines/index.json from the bundled guideline PDFs."""

from src.rag.index_builder import build_index


if __name__ == "__main__":
    count = build_index()
    print(f"Built guideline index with {count} chunks.")
