"""
RAG Document Chat — FastAPI Backend
Upload documents, embed them, and chat with AI using RAG.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import documents, chat, collections

app = FastAPI(
    title="RAG Document Chat API",
    description="Chat with your documents using Retrieval-Augmented Generation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(collections.router, prefix="/api/collections", tags=["Collections"])


@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "rag-document-chat"}
