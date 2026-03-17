# RAG Document Chat — Chat with Your PDFs, Docs & Code

Upload any document and have an AI conversation with it. Uses Retrieval-Augmented Generation (RAG) to ground answers in your actual content — no hallucinations.

## Why I Built This

**The Problem:** ChatGPT and other LLMs are powerful but they hallucinate — they confidently make up information that isn't in your documents. If you paste a 50-page PDF into ChatGPT, it loses context. If you ask about your company's internal docs, it has no idea. Teams waste hours manually searching through documentation, SOPs, and codebases to find answers that should be instant.

**The Solution:** Upload your documents (PDFs, Word docs, code, CSVs — any format), and this system chunks them, embeds them into a vector database, and lets you have a grounded conversation where every answer comes from YOUR actual content with source citations. The AI can say "Based on page 7 of architecture.pdf..." instead of hallucinating. Supports streaming responses, conversation memory, and works with OpenAI or local models via Ollama.

**Built to solve a real pain point** I've seen across multiple clients — knowledge is trapped in documents that nobody reads. This turns static docs into an interactive knowledge base that anyone on the team can query in natural language.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Architecture                                │
│                                                                     │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────────────────┐   │
│  │  Upload   │    │  Ingestion   │    │   Vector Database       │   │
│  │  PDF/DOCX │───▶│  Pipeline    │───▶│   (ChromaDB)            │   │
│  │  MD/TXT   │    │              │    │                         │   │
│  │  Code     │    │  • Chunking  │    │  • Embeddings stored    │   │
│  └──────────┘    │  • Embedding │    │  • Metadata indexed     │   │
│                  │  • Metadata  │    │  • Similarity search    │   │
│                  └──────────────┘    └────────────┬────────────┘   │
│                                                   │                 │
│  ┌──────────┐    ┌──────────────┐                │                 │
│  │  User     │    │   FastAPI    │    ┌───────────▼─────────────┐   │
│  │  Question │───▶│   Backend    │───▶│   LLM (OpenAI/Ollama)  │   │
│  │           │    │              │    │                         │   │
│  │           │◀───│  • Retrieve  │◀───│  • Context + Question   │   │
│  │  Answer   │    │  • Augment   │    │  • Grounded Answer     │   │
│  │  + Sources│    │  • Generate  │    │  • Source Citations     │   │
│  └──────────┘    └──────────────┘    └─────────────────────────┘   │
│                                                                     │
│  Supported: PDF, DOCX, Markdown, TXT, Python, JS, JSON, CSV       │
└─────────────────────────────────────────────────────────────────────┘
```

## Features

- **Multi-format ingestion** — PDF, DOCX, Markdown, TXT, source code (.py, .js, .ts), CSV, JSON
- **Smart chunking** — Recursive text splitting with overlap for context preservation
- **Semantic search** — ChromaDB vector store with OpenAI or HuggingFace embeddings
- **Source citations** — Every answer includes the exact document chunks used
- **Conversation memory** — Multi-turn chat with context from previous messages
- **Multiple LLM support** — OpenAI GPT-4, GPT-3.5, or local models via Ollama
- **Streaming responses** — Real-time token streaming via Server-Sent Events
- **REST API** — Upload, query, and manage documents via API
- **Web UI** — Clean chat interface built with Next.js

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python 3.12, LangChain |
| Vector DB | ChromaDB (local) or Pinecone (cloud) |
| Embeddings | OpenAI `text-embedding-3-small` or HuggingFace |
| LLM | OpenAI GPT-4o / GPT-3.5 / Ollama (local) |
| Frontend | Next.js 14, React 18, Tailwind CSS |
| Ingestion | PyPDF, python-docx, Unstructured |
| Infra | Docker Compose |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/vmunjal2503/rag-document-chat.git
cd rag-document-chat

# 2. Configure
cp .env.example .env
# Add your OpenAI API key (or configure Ollama for local)

# 3. Start
docker compose up -d

# 4. Open
# Web UI: http://localhost:3000
# API Docs: http://localhost:8000/docs

# 5. Upload a document and start chatting!
```

### Without Docker

```bash
pip install -r requirements.txt
python -m app.main
# API runs at http://localhost:8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/upload` | Upload and ingest a document |
| GET | `/api/documents` | List all ingested documents |
| DELETE | `/api/documents/{id}` | Remove a document and its vectors |
| POST | `/api/chat` | Ask a question (returns answer + sources) |
| POST | `/api/chat/stream` | Ask a question (streaming response) |
| GET | `/api/chat/history/{session_id}` | Get conversation history |
| POST | `/api/collections` | Create a document collection |
| GET | `/api/health` | Health check |

## Example

```bash
# Upload a document
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@architecture.pdf" \
  -F "collection=project-docs"

# Ask a question
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What database is used in the architecture?",
    "collection": "project-docs"
  }'

# Response
{
  "answer": "The architecture uses PostgreSQL 16 as the primary database...",
  "sources": [
    {"document": "architecture.pdf", "page": 3, "chunk": "...PostgreSQL 16..."},
    {"document": "architecture.pdf", "page": 7, "chunk": "...database layer..."}
  ],
  "confidence": 0.94
}
```

## Project Structure

```
rag-document-chat/
├── app/
│   ├── api/                  # FastAPI route handlers
│   │   ├── documents.py      # Upload, list, delete documents
│   │   ├── chat.py           # Question answering + streaming
│   │   └── collections.py    # Document collection management
│   ├── services/             # Core business logic
│   │   ├── ingestion.py      # Document parsing + chunking
│   │   ├── embeddings.py     # Embedding generation
│   │   ├── retriever.py      # Vector similarity search
│   │   ├── llm.py            # LLM client (OpenAI/Ollama)
│   │   └── chat_memory.py    # Conversation history
│   ├── ingestion/            # File-type specific parsers
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   ├── code_parser.py
│   │   └── csv_parser.py
│   └── main.py               # FastAPI app entry point
├── vectorstore/              # ChromaDB persistent storage
├── frontend/                 # Next.js chat UI
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | OpenAI API key (required if not using Ollama) |
| `LLM_PROVIDER` | `openai` | `openai` or `ollama` |
| `LLM_MODEL` | `gpt-4o` | Model name |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K` | `5` | Number of chunks to retrieve |
| `CHROMA_PERSIST_DIR` | `./vectorstore` | ChromaDB storage path |

---

Built by **Vikas Munjal** | Open source under MIT License
