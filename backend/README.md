# SakhiBot Backend

FastAPI backend with multi-agent orchestration for Indian women's legal rights assistance.

## 📁 Project Structure

```
backend/
├── agents/              # 4 specialized AI agents
│   ├── legal_retriever.py    # Agent 1: Retrieves legal info from ChromaDB
│   ├── doc_drafter.py         # Agent 2: Generates FIR/DV/POSH complaints
│   ├── resource_locator.py    # Agent 3: Finds shelters, OSCs, legal aid
│   └── safety_planner.py      # Agent 4: Creates personalized safety plans
│
├── core/                # Core utilities
│   ├── config.py              # Configuration & environment variables
│   ├── cache.py               # Query caching (7-day TTL)
│   ├── translate.py           # Multilingual translation layer
│   ├── emergency.py           # Emergency detection & SOS responses
│   └── groq_client.py         # Groq API client with fallback models
│
├── data/                # Static data
│   └── resources.json         # 100+ helplines, OSCs, shelters, legal aid
│
├── docs/                # Legal documents (PDFs)
│   ├── dv_act_2005.pdf
│   ├── posh_act_2013.pdf
│   ├── ipc_498a.pdf
│   └── ... (9 documents total)
│
├── templates/           # Document templates
│   ├── fir_template.docx
│   ├── dv_complaint.docx
│   └── posh_complaint.docx
│
├── scripts/             # Setup & maintenance scripts
│   ├── ingest.py              # Ingest PDFs into ChromaDB
│   └── create_templates.py    # Generate document templates
│
├── tests/               # Test files
│   ├── test_agent1.py
│   ├── test_agent2.py
│   ├── test_agent3.py
│   └── test_agent4.py
│
├── main.py              # FastAPI application entry point
├── orchestrator.py      # LangGraph multi-agent orchestrator
└── requirements.txt     # Python dependencies
```

## 🚀 Setup

### 1. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file:
```env
GROQ_API_KEY=your_groq_api_key_here
```

Get your Groq API key from: https://console.groq.com

### 4. Ingest Legal Documents
```bash
python scripts/ingest.py
```

This will:
- Extract text from all PDFs in `docs/`
- Chunk and embed the text
- Store in ChromaDB vector database

Expected output:
```
Total chunks: 500+
DV Act has 50+ chunks — good!
```

### 5. Generate Document Templates
```bash
python scripts/create_templates.py
```

Creates DOCX templates in `templates/` folder.

### 6. Run Server
```bash
uvicorn main:app --reload
```

Server runs at: http://localhost:8000

API docs at: http://localhost:8000/docs

## 📡 API Endpoints

### POST `/api/chat`
Main chat endpoint.

**Request:**
```json
{
  "message": "What is domestic violence?",
  "language": "en",
  "history": [],
  "district": "",
  "state_name": ""
}
```

**Response:**
```json
{
  "answer": "Domestic violence under DV Act 2005...",
  "sources": [{"source": "Domestic Violence Act 2005", ...}],
  "resources": [],
  "helplines": [{"name": "Women's Helpline", "phone": "181", ...}],
  "safety_plan": [],
  "document_ready": false,
  "document_type": "",
  "next_question": "",
  "is_emergency": false,
  "severity": "none",
  "activated_agents": ["legal"],
  "asking_location": false,
  "detected_lang": "en",
  "language_name": "English"
}
```

### POST `/api/document`
Generate and download legal documents.

**Request:**
```json
{
  "document_type": "fir",
  "history": [...]
}
```

**Response:** PDF file download

### GET `/api/health`
Health check endpoint.

### GET `/api/languages`
Returns list of supported languages.

## 🤖 Agent System

### Agent 1: Legal Retriever
- **Purpose:** Answer legal questions using actual Indian law
- **Tech:** ChromaDB vector search + Groq LLM
- **Features:** Query routing, confidence scoring, caching

### Agent 2: Document Drafter
- **Purpose:** Generate FIR, DV complaints, POSH complaints
- **Tech:** Conversational detail collection + DOCX templates
- **Features:** Context retention, field extraction, PDF generation

### Agent 3: Resource Locator
- **Purpose:** Find nearest help centers by location
- **Tech:** Fuzzy string matching + geographic database
- **Features:** 32 cities, 100+ resources, state normalization

### Agent 4: Safety Planner
- **Purpose:** Create personalized safety action plans
- **Tech:** Situational analysis + Groq LLM
- **Features:** Urgency detection, 6-step plans, law references

## 🔄 Orchestration Flow

```
User Message
    ↓
Translation (9 languages → English)
    ↓
Emergency Detection (critical/high/medium)
    ↓
Router Node (classifies intent)
    ↓
┌─────────────────────────────────┐
│  Agent Activation (parallel)     │
├─────────────────────────────────┤
│ • legal_node                     │
│ • document_node                  │
│ • resource_node                  │
│ • safety_node                    │
└─────────────────────────────────┘
    ↓
Synthesizer Node (combines outputs)
    ↓
Translation (English → user language)
    ↓
Frontend Response
```

## 🗄️ Database

**ChromaDB** - Vector database for legal documents
- Location: `chroma_db/` (auto-created)
- Collection: `sakhibot_legal`
- Embeddings: `all-MiniLM-L6-v2` (384 dimensions)
- Distance: Cosine similarity

**Query Cache** - JSON file cache
- Location: `query_cache/`
- TTL: 7 days
- Format: MD5 hash filenames

## 🛠️ Development

### Run Tests
```bash
python tests/test_agent1.py  # Legal Retriever
python tests/test_agent2.py  # Document Drafter
python tests/test_agent3.py  # Resource Locator
python tests/test_agent4.py  # Safety Planner
```

### Clear Cache
```python
from core.cache import clear
clear()
```

### Check ChromaDB
```python
import chromadb
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_collection("sakhibot_legal")
print(f"Total chunks: {collection.count()}")
```

## 🌐 Supported Languages

- English (en)
- Hindi (hi)
- Bengali (bn)
- Tamil (ta)
- Telugu (te)
- Marathi (mr)
- Gujarati (gu)
- Kannada (kn)
- Malayalam (ml)

## 📦 Key Dependencies

- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **langchain + langgraph** - Agent orchestration
- **chromadb** - Vector database
- **sentence-transformers** - Embeddings
- **groq** - LLM API
- **deep-translator** - Translation
- **pymupdf** - PDF processing
- **python-docx** - Document generation
- **reportlab** - PDF creation

## 🔐 Security

- API keys in `.env` (never commit)
- Input validation on all endpoints
- CORS configured for frontend origin
- No PII stored in cache (document_bytes stripped)

## 📝 License

Educational project for Final Year B.Tech CSE (Data Science)
