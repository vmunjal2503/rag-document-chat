# RAG Document Chat

**Upload a PDF, Word doc, or code file — then ask questions about it in plain English. The AI answers using only your document's content (no hallucinations) and tells you exactly which page the answer came from.**

---

## What is this?

You upload a document. The system reads it, breaks it into small pieces, and stores them. When you ask a question, it finds the most relevant pieces and uses AI to write an answer — citing exactly where the information came from.

```
Step 1: Upload               Step 2: Ask a question
┌──────────┐                 ┌──────────────────────────────────────┐
│ 📄 Upload │                 │ You: "What database does the         │
│ your PDF  │                 │       architecture use?"              │
└─────┬─────┘                 │                                      │
      │                       │ AI:  "The architecture uses           │
      ▼                       │      PostgreSQL 16 as the primary     │
┌──────────┐                 │      database, deployed in a private  │
│ System    │                 │      subnet with encryption enabled." │
│ breaks it │                 │                                      │
│ into small│                 │ 📎 Source: architecture.pdf, page 3   │
│ pieces &  │                 │ 📎 Source: architecture.pdf, page 7   │
│ stores    │                 └──────────────────────────────────────┘
│ them      │
└──────────┘
```

---

## What problem does this solve?

**Without this:** You paste a long document into ChatGPT. It loses context after a few pages. It sometimes makes up information that isn't in your document. You can't tell which part of the document the answer came from. For internal company docs, ChatGPT has no access at all.

**With this:** Your documents are stored locally. Every answer is grounded in your actual content — if the information isn't in the document, the AI says "I don't have that information" instead of guessing. Every answer shows exactly which document and page it came from.

---

## What can you do with it?

| Action | How it works |
|--------|-------------|
| **Upload documents** | Drag and drop PDFs, Word docs, text files, code files, CSVs |
| **Ask questions** | Type a question in plain English → get an answer from your docs |
| **See sources** | Every answer shows which document and page the info came from |
| **Have a conversation** | Follow-up questions work — the system remembers what you discussed |
| **Organize documents** | Group related docs into collections (e.g., "Project A docs", "HR policies") |
| **Use local AI** | Works with OpenAI (cloud) or Ollama (runs on your computer, no data leaves your machine) |

---

## Supported file types

| Type | Examples |
|------|---------|
| Documents | PDF, DOCX, TXT, Markdown |
| Code | Python, JavaScript, TypeScript |
| Data | CSV, JSON, YAML |

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

## How does it work inside?

```
1. UPLOAD         2. CHUNK              3. EMBED              4. STORE
   Your PDF  ──▶  Break into small  ──▶  Convert each piece  ──▶  Save in
                   overlapping pieces     into a number array      ChromaDB
                   (1000 chars each)      (embedding)              (vector DB)

5. QUESTION       6. SEARCH             7. GENERATE           8. RESPOND
   "What is   ──▶  Find the 5 most  ──▶  Send those pieces  ──▶  Return answer
   the main        similar pieces        + your question         + source
   conclusion?"    from the database     to the AI (GPT-4)      citations
```

---

## How is the code organized?

```
rag-document-chat/
├── app/
│   ├── api/
│   │   ├── documents.py       # Upload, list, delete documents
│   │   ├── chat.py            # Ask questions, get answers with sources
│   │   └── collections.py    # Group documents into collections
│   │
│   ├── services/
│   │   ├── ingestion.py       # Reads your document and breaks it into pieces
│   │   ├── embeddings.py      # Converts text into numbers (for similarity search)
│   │   ├── retriever.py       # Finds the most relevant pieces for your question
│   │   ├── llm.py             # Talks to GPT-4/Ollama to generate the answer
│   │   └── chat_memory.py     # Remembers your conversation for follow-up questions
│   │
│   ├── ingestion/             # One parser per file type
│   │   ├── pdf_parser.py      # Reads PDFs page by page
│   │   ├── docx_parser.py     # Reads Word docs section by section
│   │   ├── code_parser.py     # Reads code files function by function
│   │   └── csv_parser.py      # Reads CSVs in row batches
│   │
│   └── main.py                # Starts the API server
│
├── docker-compose.yml
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
