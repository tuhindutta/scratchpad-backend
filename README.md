# Scratchpad Backend

> Persistent AI agent backend with long-term markdown memory, Retrieval-Augmented Generation (RAG), streaming responses, and LangGraph-based reasoning.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Overview

[Repository Link](https://github.com/tuhindutta/scratchpad-backend/tree/main)

Scratchpad Backend is a FastAPI-powered backend for building persistent AI assistants that continuously accumulate and organize knowledge over time.

Unlike traditional chatbots that rely solely on conversation history, this system maintains two complementary knowledge stores:

- **Scratchpad Repository** – A structured markdown repository that acts as the agent's permanent knowledge base.
- **RAG Knowledge Base** – A vector database built from user-uploaded documents for semantic retrieval.

The backend uses **LangGraph**, **OpenAI**, **LlamaIndex**, and **Docling** to provide a persistent AI assistant capable of reasoning, remembering, retrieving, and streaming responses in real time.

The project is designed to integrate with a frontend responsible for authentication and session management using `user_id` and `thread_id`.

---

# Features

- Persistent markdown-based long-term memory
- LangGraph ReAct agent
- Streaming responses (NDJSON)
- Retrieval-Augmented Generation (RAG)
- Automatic document ingestion
- Semantic search over uploaded documents
- Web search support
- Website scraping
- SQLite checkpoint-based conversation memory
- Per-user and per-thread isolation
- Modular tool architecture
- Easily extensible

---

# Architecture

```
                        User
                          │
                          ▼
                  FastAPI REST API
                          │
                          ▼
                  LangGraph Agent
                          │
           ┌──────────────┬───────────────┬
           ▼              ▼               ▼
      Scratchpad      RAG Engine      Web Tools
      Repository      (LlamaIndex)    (Search/Scrape)
           │              │               │
           └──────────────┴───────────────┘
                          │
                          ▼
                Streaming NDJSON Response
```

---

# Project Structure

```
scratchpad-backend/
│
├── create_app.py
├── main.py
├── llms/
├── prompts/
├── rag/
├── stream/
│   ├── agent_stream.py
│   └── toolset/
│
└── work/
    ├── scratchpad/
    ├── ingestion/
    │   ├── raw_data/
    │   ├── parsed_data/
    │   └── vectorstore/
    └── checkpointer/
```

---

# Working Directory Layout

By default, all runtime data is stored inside the configured `WORK_DIR` (default: `work/`).

```
work/
├── scratchpad/
│   ├── index.md
│   └── *.md
│
├── ingestion/
│   ├── raw_data/
│   ├── parsed_data/
│   └── vectorstore/
│
└── checkpointer/
    └── agent_memory.sqlite
```

### scratchpad/

Permanent markdown knowledge repository maintained by the AI agent.

### ingestion/raw_data/

Temporary location where uploaded files are placed before ingestion.

Files are removed after successful processing.

### ingestion/parsed_data/

Markdown versions of uploaded documents generated using Docling.

### ingestion/vectorstore/

LlamaIndex vector databases isolated by user and thread.

### checkpointer/

SQLite database storing LangGraph checkpoints and conversation state.

---

# Technology Stack

| Component | Technology |
|------------|------------|
| Backend | FastAPI |
| Agent Framework | LangGraph |
| LLM | OpenAI |
| Embeddings | Google Generative AI |
| Vector Database | LlamaIndex |
| Document Parsing | Docling |
| Memory | SQLite |
| Web Search | DuckDuckGo |
| Website Scraping | Firecrawl |

---

# Installation

## Requirements

- Python 3.12+
- OpenAI API Key
- Google API Key
- Firecrawl API Key

Clone the repository:

```bash
git clone https://github.com/tuhindutta/scratchpad-backend.git

cd scratchpad-backend
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file.

```env
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
FIRECRAWL_API_KEY=...

AGENT_MODEL=gpt-4o-mini
RAG_MODEL=gpt-4o-mini

WORK_DIR=work
```

---

# Running

```bash
python main.py --port 8080
```

The backend will start at

```
http://localhost:8080
```

---

# API

## Base URL

```
http://localhost:8080
```

---

## Streaming Chat

### GET `/assistant/chat`

Streams agent reasoning and responses in NDJSON format.

### Request

```json
{
    "message": "Summarize my meeting notes",
    "credential": {
        "user_id": "user123",
        "thread_id": "threadABC"
    }
}
```

### Response Stream

```json
{"node":"reasoning","type":"tool","tool_name":"query_RAG_agent","content":"Searching..."}
{"node":"response","content":"Here is the summary..."}
```

---

## Ingest Documents

### POST `/rag/ingest`

Ingests all files present in:

```
work/ingestion/raw_data/
```

Pipeline:

```
Raw Files
      │
      ▼
Docling Parsing
      │
      ▼
Markdown Conversion
      │
      ▼
Vector Embedding
      │
      ▼
LlamaIndex Storage
      │
      ▼
Agent Notification
```

---

## List Conversations

### GET

```
/assistant/chats/list
```

Returns all active conversation threads.

Example:

```json
{
    "active_threads":[
        "thread1",
        "thread2"
    ]
}
```

---

## Delete Thread

### POST

```
/assistant/chats/delete/thread
```

```json
{
    "thread_id":"thread1"
}
```

Deletes the specified conversation.

---

## Delete Entire History

### POST

```
/assistant/chats/delete/full
```

Removes all stored conversation history.

---

# Streaming Format

All streaming endpoints return newline-delimited JSON (NDJSON).

Example:

```json
{"node":"reasoning","content":"Thinking..."}
{"node":"reasoning","tool_name":"print_tree"}
{"node":"response","content":"Final answer"}
```

This allows frontends to progressively render:

- Agent reasoning
- Tool execution
- Intermediate updates
- Final response

---

# Core Components

## FastAPI Layer

Responsible for:

- REST endpoints
- Streaming endpoints
- Request validation
- Application initialization

Files:

```
create_app.py
main.py
```

---

## Agent Layer

Implemented using LangGraph.

Responsibilities:

- Reasoning
- Tool execution
- Long-term memory
- Streaming events
- Conversation checkpoints

File:

```
stream/agent_stream.py
```

---

## LLM Layer

Two independent models are used.

### Agent Model

Used for:

- Conversation
- Planning
- Tool calling

Default:

```
ChatOpenAI
```

Temperature:

```
0.3
```

---

### RAG Model

Used for:

- Retrieval
- Query answering

Temperature:

```
0.1
```

---

## RAG Layer

Responsible for:

- Parsing uploaded files
- Building vector stores
- Semantic retrieval

Workflow:

```
Documents
    │
    ▼
Docling
    │
    ▼
Markdown
    │
    ▼
Embeddings
    │
    ▼
LlamaIndex
```

---

# Scratchpad Repository

The Scratchpad is the agent's permanent knowledge repository.

Knowledge is stored as markdown documents.

A mandatory `index.md` maintains the repository catalog.

The agent is responsible for:

- creating files
- updating files
- avoiding duplicates
- maintaining the catalog

---

# Available Tools

The agent has access to a comprehensive set of tools.

## Repository Management

- Print repository tree
- Read index
- Update index
- Read files
- Create files
- Append files
- Delete files
- Delete folders

---

## Knowledge

- Query RAG
- Summarize text
- Web search
- Website scraping

---

# Agent Workflow

```
User Message
      │
      ▼
Reasoning
      │
      ▼
Tool Selection
      │
      ▼
Repository / RAG / Web
      │
      ▼
Streaming Updates
      │
      ▼
Final Response
```

---

# Document Ingestion Workflow

```
Upload Files
      │
      ▼
raw_data/
      │
      ▼
Docling Parser
      │
      ▼
Markdown
      │
      ▼
Embeddings
      │
      ▼
Vector Store
      │
      ▼
Agent Notification
```

---

# Conversation Memory

Conversation state is managed using LangGraph checkpoints.

Memory is isolated using:

```
user_id
+
thread_id
```

Each conversation maintains independent context and history.

---

# Error Handling

The backend automatically handles:

- Missing directories
- Directory creation
- Read-only file deletion
- Missing environment variables
- Per-thread RAG isolation

---

# Extending the Project

## Add New Tools

Create additional LangChain tools inside:

```
stream/toolset/tools.py
```

---

## Change LLMs

Alternative implementations for Groq and Gemini are already scaffolded and can be enabled with minimal changes.

---

## Customize Prompts

System prompts are stored in:

```
prompts/
```

---

## Frontend Integration

A frontend should:

- Authenticate users
- Generate `user_id`
- Generate `thread_id`
- Upload files to `raw_data`
- Consume NDJSON streams
- Display reasoning and final responses

---

# Production Recommendations

- Add authentication middleware
- Use HTTPS
- Monitor vector store growth
- Schedule cleanup of temporary files
- Deploy behind Nginx or a reverse proxy
- Run using Docker, Supervisor, or PM2
- Separate ingestion workers from chat workers for higher throughput

---

# License

This project is licensed under the MIT License.
