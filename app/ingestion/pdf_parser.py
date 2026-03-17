"""PDF document parser using PyPDF."""

from pypdf import PdfReader


def parse_pdf(filepath: str) -> list[dict]:
    """
    Extract text from PDF, preserving page numbers.
    Returns list of {"content": str, "metadata": {"page": int}}
    """
    reader = PdfReader(filepath)
    pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({
                "content": text,
                "metadata": {"page": i + 1},
            })

    return pages
