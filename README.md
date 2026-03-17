# RAG Document Chat

**Upload a PDF, Word doc, or code file — then ask questions about it in plain English. The AI answers using only your document's content (no hallucinations) and tells you exactly which page the answer came from.**

---

## What is this?

You upload a document. The system reads it, breaks it into small pieces, and stores them as vector embeddings. When you ask a question, it finds the most relevant pieces via semantic search and uses an LLM to write an answer — citing exactly where the information came from.

```
Step 1: Upload               Step 2: Ask a question
┌──────────┐                 ┌──────────────────────────────────────┐
│ Upload   │                 │ You: "What database does the         │
│ your PDF │                 │       architecture use?"              │
└─────┬────┘                 │                                      │
      │                      │ AI:  "The architecture uses           │
      ▼                      │      PostgreSQL 16 as the primary     │
┌──────────┐                 │      database, deployed in a private  │
│ Parse →  │                 │      subnet with encryption enabled." │
│ Chunk →  │                 │                                      │
│ Embed →  │                 │ Source: architecture.pdf, page 3      │
│ Store in │                 │ Source: architecture.pdf, page 7      │
│ ChromaDB │                 └──────────────────────────────────────┘
└──────────┘
```

---

## What problem does this solve?

**Without this:** You paste a long document into ChatGPT. It loses context after a few pages. It sometimes makes up information that isn't in your document. You can't tell which part of the document the answer came from. For internal company docs, ChatGPT has no access at all.

**With this:** Your documents are stored locally. Every answer is grounded in your actual content — if the information isn't in the document, the AI says "I don't have that information" instead of guessing. Every answer shows exactly which document and page it came from.

---

## What can you do with it?

| Action | How it works | Technical Details |
|--------|-------------|-------------------|
| **Upload documents** | Drag and drop PDFs, Word docs, text files, code files, CSVs | File type detected → routed to format-specific parser. Max 50MB per file. |
| **Ask questions** | Type in plain English → get an answer from your docs | Question embedded → top-5 similar chunks retrieved → sent as context to LLM. |
| **See sources** | Every answer shows document name, page number, and relevance score | Relevance is cosine similarity between question embedding and chunk embedding. Threshold: 0.7 minimum. |
| **Have a conversation** | Follow-up questions work — system remembers what you discussed | Session-based memory: last 10 messages stored in memory, injected into LLM context for continuity. |
| **Organize documents** | Group docs into collections (e.g., "Project A docs", "HR policies") | Each collection is a separate ChromaDB namespace. Search is scoped to the active collection. |
| **Use local AI** | Works with OpenAI (cloud) or Ollama (local, no data leaves your machine) | LLM service abstracts provider — swap by changing `LLM_PROVIDER` in `.env`. Ollama runs on localhost:11434. |

---

## How does it work inside?

```
1. UPLOAD              2. PARSE                3. CHUNK                 4. EMBED
   Your PDF  ────────▶  Format-specific   ────▶  Recursive text    ────▶  OpenAI
                         parser extracts          splitting:               text-embedding-ada-002
                         raw text + metadata      1000 chars/chunk         (or Ollama nomic-embed)
                         (page numbers,            200 char overlap         │
                         headings, etc.)           preserves sentence       │ 1536-dim vector
                                                   boundaries               │ per chunk
                                                                            ▼
5. STORE               6. SEARCH               7. GENERATE             8. RESPOND
   ChromaDB  ◀────────   Cosine similarity ◀──   System prompt     ────▶  JSON response:
   (vector DB)            between question        enforces grounded        {answer, sources[]}
   each chunk stored      embedding and all       answers:                 │
   with metadata:         stored chunks           "Answer ONLY from        │ Streaming via SSE
   {page, doc_name,       │                        the provided context.   │ (Server-Sent Events)
    chunk_index}          Top 5 results            If not found, say       ▼
                          above 0.7 threshold      'I don't have that      Real-time token-by-token
                                                   information.'"          response in the UI
```

---

## Technical deep dive

### Chunking strategy
```
Document text (5000 chars)
     │
     ▼
RecursiveTextSplitter:
  - Primary split: paragraphs (\n\n)
  - Fallback: sentences (. ! ?)
  - Last resort: character boundary
  - Chunk size: 1000 characters
  - Overlap: 200 characters (ensures no information is lost at boundaries)
     │
     ▼
Result: 6 chunks, each with metadata {doc_id, chunk_index, page_number}
```

**Why recursive splitting?** Naive splitting (every 1000 chars) cuts sentences in half. Recursive splitting tries paragraph breaks first, then sentence breaks, preserving semantic units. The 200-char overlap means if an answer spans two chunks, both chunks contain enough context.

### Embedding and retrieval
```python
# Embedding: text → 1536-dimensional vector
# Semantically similar text produces similar vectors

embed("What database is used?")      → [0.12, -0.34, 0.56, ...]
embed("PostgreSQL runs on port 5432") → [0.11, -0.32, 0.58, ...]
# Cosine similarity: 0.94 — high match!

embed("The weather is sunny today")   → [0.87, 0.23, -0.45, ...]
# Cosine similarity: 0.12 — low match, correctly excluded
```

### Grounding (how hallucinations are prevented)
```
System prompt sent to LLM:
┌────────────────────────────────────────────────────────┐
│ You are a document Q&A assistant.                       │
│                                                        │
│ RULES:                                                 │
│ 1. Answer ONLY using the provided context below.       │
│ 2. If the answer is not in the context, say:           │
│    "I don't have that information in the documents."   │
│ 3. Always cite which document and page your answer     │
│    comes from.                                         │
│ 4. Never use outside knowledge.                        │
│                                                        │
│ CONTEXT (retrieved from vector search):                │
│ [chunk 1: architecture.pdf, page 3] "The system uses..."│
│ [chunk 2: architecture.pdf, page 7] "PostgreSQL 16..."  │
│ [chunk 3: setup.md, page 1] "Database connection..."    │
│                                                        │
│ USER QUESTION: "What database does the architecture    │
│ use?"                                                  │
└────────────────────────────────────────────────────────┘
```

### Streaming responses (SSE)
```
Client opens: GET /api/chat/stream?question=...

Server sends tokens as they're generated:
  data: {"token": "The"}
  data: {"token": " architecture"}
  data: {"token": " uses"}
  data: {"token": " PostgreSQL"}
  data: {"token": " 16"}
  ...
  data: {"token": "[DONE]", "sources": [...]}

User sees the answer typing out in real-time, like ChatGPT.
```

---

## Supported file types

| Type | Parser | How it works |
|------|--------|-------------|
| **PDF** | `pdf_parser.py` | Extracts text page-by-page via `PyMuPDF`. Preserves page numbers for citation. Handles multi-column layouts. |
| **DOCX** | `docx_parser.py` | Reads paragraphs and tables via `python-docx`. Maps heading hierarchy for section-aware chunking. |
| **Code** | `code_parser.py` | Splits by function/class definitions (AST-aware for Python, regex for JS/TS). Each function becomes a chunk with file path + line number. |
| **CSV** | `csv_parser.py` | Reads in row batches (50 rows per chunk). Column headers prepended to each chunk for context. |
| **TXT/MD** | Built-in | Direct text input to the recursive splitter. Markdown headings used as split boundaries. |

---

## How to use it

```bash
# 1. Clone
git clone https://github.com/vmunjal2503/rag-document-chat.git
cd rag-document-chat

# 2. Add your OpenAI key (or set up Ollama for local AI)
cp .env.example .env
# Edit .env → add OPENAI_API_KEY=sk-xxxxx

# 3. Start
docker compose up -d

# 4. Open
# Chat UI:   http://localhost:3000
# API docs:  http://localhost:8000/docs
```

### Try it with curl

```bash
# Upload a document
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@my-document.pdf"

# Ask a question
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main conclusion?"}'

# Response:
# {
#   "answer": "The main conclusion is...",
#   "sources": [
#     {"document": "my-document.pdf", "page": 12, "relevance": 0.94}
#   ]
# }
```

---

## How is the code organized?

```
rag-document-chat/
├── app/
│   ├── api/
│   │   ├── documents.py       # Upload endpoint: validate → parse → chunk → embed → store
│   │   ├── chat.py            # Question endpoint: embed query → retrieve → generate → stream
│   │   └── collections.py    # Group documents into isolated collections (ChromaDB namespaces)
│   │
│   ├── services/
│   │   ├── ingestion.py       # Full pipeline: file → parser → RecursiveTextSplitter → embeddings → ChromaDB
│   │   ├── embeddings.py      # OpenAI ada-002 / Ollama nomic-embed. Batch embedding (100 chunks/call)
│   │   ├── retriever.py       # Cosine similarity search, top-5 results, 0.7 threshold filtering
│   │   ├── llm.py             # LLM abstraction: OpenAI GPT-4 or Ollama. Grounding prompt. Streaming.
│   │   └── chat_memory.py     # Session-based conversation history (last 10 messages per session)
│   │
│   ├── ingestion/             # One parser per file type
│   │   ├── pdf_parser.py      # PyMuPDF: page-by-page extraction with page number metadata
│   │   ├── docx_parser.py     # python-docx: paragraph + table extraction, heading hierarchy
│   │   ├── code_parser.py     # AST-aware splitting: functions/classes become individual chunks
│   │   └── csv_parser.py      # Batch rows (50/chunk) with column headers prepended
│   │
│   └── main.py                # FastAPI app: CORS, routes, startup (ChromaDB connection)
│
├── docker-compose.yml         # App + ChromaDB
├── requirements.txt
└── .env.example
```

---

## Who is this for?

- Teams with lots of internal documentation that nobody can find answers in
- Developers who want to chat with a codebase or technical spec
- Anyone who's tired of ChatGPT making up information about their documents
- Companies that need AI answers but can't send sensitive docs to the cloud (use Ollama for local AI)

---

Built by **Vikas Munjal** | Open source under MIT License
