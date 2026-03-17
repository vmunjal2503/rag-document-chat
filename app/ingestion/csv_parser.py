"""CSV/structured data parser."""

import csv


def parse_csv(filepath: str) -> list[dict]:
    """
    Parse CSV into row-based text for embedding.
    Each row becomes a text block with column headers as context.
    """
    rows = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        batch = []
        batch_size = 20  # Group 20 rows per chunk

        for i, row in enumerate(reader):
            row_text = " | ".join([f"{k}: {v}" for k, v in row.items() if v])
            batch.append(row_text)

            if len(batch) >= batch_size:
                rows.append({
                    "content": f"Columns: {', '.join(headers)}\n\n" + "\n".join(batch),
                    "metadata": {"rows": f"{i - batch_size + 2}-{i + 1}"},
                })
                batch = []

        # Remaining rows
        if batch:
            rows.append({
                "content": f"Columns: {', '.join(headers)}\n\n" + "\n".join(batch),
                "metadata": {"rows": f"remaining"},
            })

    return rows if rows else [{"content": "", "metadata": {}}]
