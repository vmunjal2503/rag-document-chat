"""
Document upload and management endpoints.
"""

import uuid
import os
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.ingestion import IngestionService

router = APIRouter()
ingestion = IngestionService()

# In-memory document registry (use DB in production)
documents_db: dict[str, dict] = {}

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    collection: str
    chunk_count: int
    status: str
    uploaded_at: str


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form(default="default"),
):
    """
    Upload a document for ingestion into the vector store.

    Supported formats: PDF, DOCX, TXT, MD, PY, JS, TS, CSV, JSON
    """
    # Validate file type
    allowed_extensions = {
        ".pdf", ".docx", ".txt", ".md",
        ".py", ".js", ".ts", ".jsx", ".tsx",
        ".csv", ".json", ".yaml", ".yml",
    }
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {allowed_extensions}",
        )

    # Read file content
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)

    if size_mb > MAX_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {size_mb:.1f}MB (max {MAX_SIZE_MB}MB)",
        )

    # Save file
    doc_id = str(uuid.uuid4())
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filepath = os.path.join(UPLOAD_DIR, f"{doc_id}{ext}")
    with open(filepath, "wb") as f:
        f.write(content)

    # Ingest: parse → chunk → embed → store in vector DB
    chunk_count = await ingestion.ingest_document(
        doc_id=doc_id,
        filepath=filepath,
        filename=file.filename or "unknown",
        file_type=ext,
        collection=collection,
    )

    # Register document
    doc_record = {
        "id": doc_id,
        "filename": file.filename,
        "file_type": ext,
        "collection": collection,
        "chunk_count": chunk_count,
        "status": "indexed",
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    documents_db[doc_id] = doc_record

    return doc_record


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(collection: Optional[str] = None):
    """List all ingested documents, optionally filtered by collection."""
    docs = list(documents_db.values())
    if collection:
        docs = [d for d in docs if d["collection"] == collection]
    return docs


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    """Get details of a specific document."""
    if doc_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    return documents_db[doc_id]


@router.delete("/{doc_id}", status_code=204)
async def delete_document(doc_id: str):
    """Delete a document and its vectors from the store."""
    if doc_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove vectors from ChromaDB
    await ingestion.delete_document(doc_id)

    # Remove file
    doc = documents_db.pop(doc_id)
    filepath = os.path.join(UPLOAD_DIR, f"{doc_id}{doc['file_type']}")
    if os.path.exists(filepath):
        os.remove(filepath)

    return None
