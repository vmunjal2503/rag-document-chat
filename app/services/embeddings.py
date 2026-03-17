"""
Embedding service — generate embeddings and manage ChromaDB storage.
"""

import os
import chromadb
from openai import OpenAI


class EmbeddingService:
    """Handles embedding generation and vector store operations."""

    def __init__(self):
        self.model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./vectorstore")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.chroma = chromadb.PersistentClient(path=self.persist_dir)

    def _get_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        return self.chroma.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    def _generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts using OpenAI."""
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    async def embed_and_store(self, chunks: list[dict], collection: str):
        """
        Generate embeddings for chunks and store in ChromaDB.

        Args:
            chunks: List of {"id": str, "content": str, "metadata": dict}
            collection: Name of the ChromaDB collection
        """
        if not chunks:
            return

        coll = self._get_collection(collection)

        # Batch embedding generation (OpenAI supports up to 2048 inputs)
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [c["content"] for c in batch]
            ids = [c["id"] for c in batch]
            metadatas = [c["metadata"] for c in batch]

            embeddings = self._generate_embeddings(texts)

            coll.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

    async def search(
        self,
        query: str,
        collection: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Semantic similarity search against stored vectors.

        Returns list of {"content": str, "metadata": dict, "score": float}
        """
        coll = self._get_collection(collection)

        # Generate query embedding
        query_embedding = self._generate_embeddings([query])[0]

        # Search
        results = coll.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        items = []
        for i in range(len(results["ids"][0])):
            items.append({
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i],  # Convert distance to similarity
            })

        return items

    async def delete_by_doc_id(self, doc_id: str):
        """Delete all chunks belonging to a document across all collections."""
        for coll_name in [c.name for c in self.chroma.list_collections()]:
            coll = self.chroma.get_collection(coll_name)
            # ChromaDB supports filtering by metadata
            coll.delete(where={"doc_id": doc_id})
