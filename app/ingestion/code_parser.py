"""Source code parser — splits by functions/classes."""

import re


def parse_code(filepath: str) -> list[dict]:
    """
    Parse source code files, splitting by function/class definitions.
    Preserves structural context for better retrieval.
    """
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    ext = filepath.rsplit(".", 1)[-1]
    sections = []

    if ext == "py":
        sections = _split_python(content)
    elif ext in ("js", "ts", "jsx", "tsx"):
        sections = _split_javascript(content)

    if not sections:
        sections = [{"content": content, "metadata": {"section": "full_file"}}]

    return sections


def _split_python(content: str) -> list[dict]:
    """Split Python code by class and function definitions."""
    pattern = r"^(class\s+\w+|def\s+\w+|async\s+def\s+\w+)"
    blocks = re.split(f"(?=^(?:{pattern[1:]}))", content, flags=re.MULTILINE)

    sections = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Extract function/class name
        match = re.match(r"(class|def|async\s+def)\s+(\w+)", block)
        name = match.group(2) if match else "module_level"
        sections.append({
            "content": block,
            "metadata": {"section": name, "language": "python"},
        })

    return sections


def _split_javascript(content: str) -> list[dict]:
    """Split JS/TS code by function and class definitions."""
    pattern = r"^(export\s+)?(default\s+)?(function|class|const\s+\w+\s*=)"
    blocks = re.split(f"(?=^(?:{pattern[1:]}))", content, flags=re.MULTILINE)

    sections = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        match = re.match(r"(?:export\s+)?(?:default\s+)?(?:function|class|const)\s+(\w+)", block)
        name = match.group(1) if match else "module_level"
        sections.append({
            "content": block,
            "metadata": {"section": name, "language": "javascript"},
        })

    return sections
