"""
Document ingestion pipeline — parse, chunk, embed, store.
"""

import os
from typing import Optional
from app.services.embeddings import EmbeddingService
from app.ingestion.pdf_parser import parse_pdf
from app.ingestion.docx_parser import parse_docx
from app.ingestion.code_parser import parse_code
from app.ingestion.csv_parser import parse_csv


class IngestionService:
    """Orchestrates the document ingestion pipeline."""

    def __init__(self):
        self.embeddings = EmbeddingService()
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))

    async def ingest_document(
        self,
        doc_id: str,
        filepath: str,
        filename: str,
        file_type: str,
        collection: str,
    ) -> int:
        """
        Full ingestion pipeline:
        1. Parse document into raw text (with page/section metadata)
        2. Split into overlapping chunks
        3. Generate embeddings
        4. Store in vector database
        """
        # Step 1: Parse
        parsed = self._parse(filepath, file_type)

        # Step 2: Chunk with overlap
        chunks = self._chunk(parsed, doc_id, filename)

        # Step 3 & 4: Embed and store
        await self.embeddings.embed_and_store(
            chunks=chunks,
            collection=collection,
        )

        return len(chunks)

    def _parse(self, filepath: str, file_type: str) -> list[dict]:
        """Route to the correct parser based on file type."""
        parsers = {
            ".pdf": parse_pdf,
            ".docx": parse_docx,
            ".csv": parse_csv,
            ".py": parse_code,
            ".js": parse_code,
            ".ts": parse_code,
            ".jsx": parse_code,
            ".tsx": parse_code,
        }

        parser = parsers.get(file_type)
        if parser:
            return parser(filepath)

        # Default: plain text
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        return [{"content": text, "metadata": {"page": 1}}]

    def _chunk(self, parsed: list[dict], doc_id: str, filename: str) -> list[dict]:
        """
        Split parsed content into overlapping chunks.
        Uses recursive character splitting for natural boundaries.
        """
        chunks = []
        chunk_id = 0

        for section in parsed:
            text = section["content"]
            metadata = section.get("metadata", {})

            # Split by paragraphs first, then by sentences if too large
            separators = ["\n\n", "\n", ". ", " "]
            sub_chunks = self._recursive_split(text, separators)

            for sub in sub_chunks:
                if len(sub.strip()) < 50:  # Skip tiny chunks
                    continue

                chunks.append({
                    "id": f"{doc_id}_chunk_{chunk_id}",
                    "content": sub.strip(),
                    "metadata": {
                        "doc_id": doc_id,
                        "filename": filename,
                        "chunk_index": chunk_id,
                        **metadata,
                    },
                })
                chunk_id += 1

        return chunks

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using a hierarchy of separators."""
        if len(text) <= self.chunk_size:
            return [text]

        # Try each separator
        for sep in separators:
            parts = text.split(sep)
            if len(parts) > 1:
                chunks = []
                current = ""
                for part in parts:
                    candidate = current + sep + part if current else part
                    if len(candidate) > self.chunk_size and current:
                        chunks.append(current)
                        # Keep overlap from previous chunk
                        overlap = current[-self.chunk_overlap:] if len(current) > self.chunk_overlap else current
                        current = overlap + sep + part
                    else:
                        current = candidate
                if current:
                    chunks.append(current)
                return chunks

        # Last resort: hard split by character count
        return [
            text[i:i + self.chunk_size]
            for i in range(0, len(text), self.chunk_size - self.chunk_overlap)
        ]

    async def delete_document(self, doc_id: str):
        """Remove all vectors for a document from the store."""
        await self.embeddings.delete_by_doc_id(doc_id)
