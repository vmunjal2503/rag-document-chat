"""DOCX document parser using python-docx."""

from docx import Document


def parse_docx(filepath: str) -> list[dict]:
    """
    Extract text from DOCX files, grouping by headings.
    Returns list of {"content": str, "metadata": {"section": str}}
    """
    doc = Document(filepath)
    sections = []
    current_section = ""
    current_heading = "Document"

    for para in doc.paragraphs:
        if para.style.name.startswith("Heading"):
            # Save previous section
            if current_section.strip():
                sections.append({
                    "content": current_section.strip(),
                    "metadata": {"section": current_heading},
                })
            current_heading = para.text
            current_section = ""
        else:
            current_section += para.text + "\n"

    # Save last section
    if current_section.strip():
        sections.append({
            "content": current_section.strip(),
            "metadata": {"section": current_heading},
        })

    return sections if sections else [{"content": "", "metadata": {}}]
