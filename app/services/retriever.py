"""
Retriever service — semantic search with re-ranking.
"""

import os
from app.services.embeddings import EmbeddingService


class RetrieverService:
    """Retrieves relevant document chunks for a given query."""

    def __init__(self):
        self.embeddings = EmbeddingService()
        self.default_top_k = int(os.getenv("TOP_K", "5"))

    async def search(
        self,
        query: str,
        collection: str = "default",
        top_k: int = None,
    ) -> list[dict]:
        """
        Search for relevant document chunks.

        Steps:
        1. Semantic search via embeddings
        2. Filter low-confidence results (score < 0.3)
        3. Return ranked results with metadata
        """
        k = top_k or self.default_top_k

        results = await self.embeddings.search(
            query=query,
            collection=collection,
            top_k=k,
        )

        # Filter low-confidence matches
        filtered = [r for r in results if r["score"] >= 0.3]

        return filtered
