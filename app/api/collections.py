"""
Document collection management.
Collections group related documents for scoped search.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# In-memory store (use DB in production)
collections_db: dict[str, dict] = {
    "default": {"name": "default", "description": "Default collection", "document_count": 0},
}


class CreateCollectionRequest(BaseModel):
    name: str
    description: Optional[str] = None


class CollectionResponse(BaseModel):
    name: str
    description: Optional[str]
    document_count: int


@router.get("/", response_model=list[CollectionResponse])
async def list_collections():
    """List all document collections."""
    return list(collections_db.values())


@router.post("/", response_model=CollectionResponse, status_code=201)
async def create_collection(data: CreateCollectionRequest):
    """Create a new document collection."""
    collections_db[data.name] = {
        "name": data.name,
        "description": data.description,
        "document_count": 0,
    }
    return collections_db[data.name]


@router.delete("/{name}", status_code=204)
async def delete_collection(name: str):
    """Delete a collection and all its documents."""
    collections_db.pop(name, None)
    return None
