# SakhiBot — Women's Legal Rights & Emergency Response AI

> Aapka haq, aapki bhasha mein (Your rights, in your language)

An agentic, multilingual AI platform that helps Indian women know their legal rights AND stay safe with integrated emergency response features — in Hindi, Bengali, Tamil, and more.

---

## 🌟 What it does

### Legal Rights & Support:
- ✅ Answers legal questions grounded in actual Indian law (no hallucination)
- ✅ Generates filled FIR drafts and complaint documents ready to print
- ✅ Finds nearest shelters, One Stop Centres, and helplines by district
- ✅ Builds a personalised step-by-step safety plan
- ✅ Supports voice input and text-to-speech in multiple Indian languages

### 🚨 NEW: Emergency Response Features:
- 🆘 **SOS Button** - instant alerts to trusted guardians with GPS location
- 📍 **Live Location Sharing** - real-time tracking for safety
- 📱 **Multi-Channel Alerts** - SMS, WhatsApp, and voice calls
- 👥 **Guardian Network** - manage trusted emergency contacts
- 🚓 **Police Station Locator** - find nearest help with contact info
- 🔒 **Privacy Compliant** - DPDP Act 2023 & IT Act 2000 compliant consent management

[📖 See Emergency Features Documentation](EMERGENCY_FEATURES.md) | [🔌 Integration Guide](backend/INTEGRATION_GUIDE.md)

---

## 🎯 Quick Start

See **[QUICK_START.md](QUICK_START.md)** for 5-minute setup guide.

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python scripts/ingest.py
uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite 8 + TailwindCSS 4 |
| Backend | FastAPI (Python) |
| Agent Orchestration | LangGraph (StateGraph) |
| Vector Database | ChromaDB |
| Embeddings | sentence-transformers all-MiniLM-L6-v2 |
| LLM | Groq API — Llama 3.1 8B (+ fallback models) |
| Translation | deep-translator + langdetect |
| Document Generation | python-docx + reportlab |

---

## 📁 Project Structure

```
sakhibot/
├── backend/
│   ├── agents/              # 4 specialized AI agents
│   │   ├── legal_retriever.py    # Agent 1: Legal info retrieval
│   │   ├── doc_drafter.py        # Agent 2: Document generation
│   │   ├── resource_locator.py   # Agent 3: Find help centers
│   │   └── safety_planner.py     # Agent 4: Safety plans
│   │
│   ├── core/                # Core utilities
│   │   ├── config.py             # Configuration
│   │   ├── cache.py              # Query caching
│   │   ├── translate.py          # Multilingual support
│   │   ├── emergency.py          # Emergency detection
│   │   └── groq_client.py        # LLM client
│   │
│   ├── scripts/             # Setup scripts
│   │   ├── ingest.py             # Ingest PDFs to ChromaDB
│   │   └── create_templates.py   # Generate templates
│   │
│   ├── tests/               # Test files
│   ├── data/                # resources.json
│   ├── docs/                # Legal PDFs (9 documents)
│   ├── templates/           # DOCX templates
│   ├── main.py              # FastAPI app
│   └── orchestrator.py      # LangGraph orchestrator
│
└── frontend/
    └── src/
        ├── components/      # React components (12 components)
        ├── App.jsx          # Main app
        └── api.js           # API client
```

**Complete structure guide:** [STRUCTURE.md](STRUCTURE.md)

---

## 🤖 Multi-Agent System

### Agent 1: Legal Retriever
- **Purpose:** Answers legal questions using actual Indian law
- **Tech:** ChromaDB vector search + Groq LLM
- **Features:** Query routing, confidence scoring, 7-day caching

### Agent 2: Document Drafter
- **Purpose:** Generates FIR, DV complaints, POSH complaints
- **Tech:** Conversational detail collection + DOCX/PDF generation
- **Features:** Context retention, field extraction, downloadable PDFs

### Agent 3: Resource Locator
- **Purpose:** Finds nearest help centers by location
- **Tech:** Fuzzy string matching + geographic database
- **Features:** 32 cities, 100+ resources, state normalization

### Agent 4: Safety Planner
- **Purpose:** Creates personalized safety action plans
- **Tech:** Situational analysis + Groq LLM
- **Features:** Urgency detection, 6-step plans, law references

---

## 📊 System Flow

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
│  Agents Activated (parallel)     │
├─────────────────────────────────┤
│ • Legal Retriever                │
│ • Document Drafter               │
│ • Resource Locator               │
│ • Safety Planner                 │
└─────────────────────────────────┘
    ↓
Synthesizer (combines outputs)
    ↓
Translation (English → user language)
    ↓
Frontend Response (with cards)
```

---

## 📚 Legal Knowledge Base

| Document | Source | Chunks | Status |
|----------|--------|--------|--------|
| Domestic Violence Act 2005 | indiacode.nic.in | 50+ | ✅ |
| POSH Act 2013 | indiacode.nic.in | 40+ | ✅ |
| IPC Section 498A | indiacode.nic.in | 100+ | ✅ |
| Maternity Benefit Act | indiacode.nic.in | 30+ | ✅ |
| Dowry Prohibition Act | indiacode.nic.in | 20+ | ✅ |
| Equal Remuneration Act | indiacode.nic.in | 20+ | ✅ |
| CrPC Sections | indiacode.nic.in | 80+ | ✅ |
| Constitution Art 14-21 | legislative.gov.in | 60+ | ✅ |

**Total: 500+ chunks** in ChromaDB vector database

---

## 🌐 Supported Languages

1. English (en)
2. Hindi (hi)
3. Bengali (bn)
4. Tamil (ta)
5. Telugu (te)
6. Marathi (mr)
7. Gujarati (gu)
8. Kannada (kn)
9. Malayalam (ml)

---

## 🔥 Key Features

### 1. Multilingual Support
- Auto-detects user language
- Translates input/output seamlessly
- TTS in 9 Indian languages

### 2. Emergency Detection
- Keywords in all languages
- Instant SOS card with helplines
- Severity levels (critical/high/medium)

### 3. Document Generation
- FIR (First Information Report)
- DV Act Section 12 complaint
- POSH Act workplace harassment complaint
- Downloadable PDF format

### 4. Resource Finder
- 100+ resources across India
- One Stop Centres (24x7)
- Shelter homes
- Legal aid offices
- Fuzzy location matching

### 5. Safety Planning
- Personalized 6-step plans
- Based on user situation
- References specific laws
- Practical next steps

### 6. Grounded Answers
- No hallucination
- Only from actual legal documents
- Citations provided
- Confidence scoring

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | This file - project overview |
| [QUICK_START.md](QUICK_START.md) | 5-minute setup guide |
| [STRUCTURE.md](STRUCTURE.md) | Complete project structure |
| [CHANGES.md](CHANGES.md) | Folder reorganization log |
| [backend/README.md](backend/README.md) | Backend-specific docs |

---

## 🔧 Development Progress

| Phase | Task | Status |
|-------|------|--------|
| Phase 1 | Project setup + GitHub | ✅ Done |
| Phase 2 | PDF ingestion + ChromaDB | ✅ Done |
| Phase 3 | Agent 1: Legal Retriever | ✅ Done |
| Phase 4 | Agent 2: Document Drafter | ✅ Done |
| Phase 5 | Agent 3: Resource Locator | ✅ Done |
| Phase 6 | Agent 4 + Orchestrator | ✅ Done |
| Phase 7 | Translation + Emergency | ✅ Done |
| Phase 8 | React UI Components | ✅ Done |
| Phase 9 | Frontend-Backend Integration | ✅ Done |
| Phase 10 | **Folder Reorganization** | ✅ Done |
| Phase 11 | Testing + Polish | 🔄 In Progress |
| Phase 12 | TTS + Voice | 🔄 In Progress |
| Phase 13 | Deployment | ⏳ Planned |

---

## 🚀 Setup & Run

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API key (free at https://console.groq.com)

### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo GROQ_API_KEY=your_key_here > .env

# Ingest legal documents
python scripts/ingest.py

# Start backend server
uvicorn main:app --reload
```

Backend runs at: http://localhost:8000

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend runs at: http://localhost:5173

---

## 📡 API Endpoints

### POST `/api/chat`
Main chat endpoint - processes user messages.

### POST `/api/document`
Download generated legal documents (PDF).

### GET `/api/health`
Health check endpoint.

### GET `/api/languages`
Returns list of supported languages.

**API Documentation:** http://localhost:8000/docs (when server is running)

---

## 🧪 Testing

```bash
cd backend

# Test individual agents
python tests/test_agent1.py  # Legal Retriever
python tests/test_agent2.py  # Document Drafter
python tests/test_agent3.py  # Resource Locator
python tests/test_agent4.py  # Safety Planner

# Test language detection
python tests/test_lang.py

# Test retrieval pipeline
python tests/test_retrieval.py
```

---

## 🎓 Project Context

**Institution:** Final Year B.Tech Computer Science & Engineering (Data Science)  
**Duration:** 14-day sprint  
**Team Size:** Solo project  
**Advisor:** [Your Advisor Name]

### Learning Outcomes
- Multi-agent systems with LangGraph
- Vector databases (ChromaDB)
- RAG (Retrieval-Augmented Generation)
- Multilingual NLP
- FastAPI backend development
- React frontend integration
- Document generation (DOCX/PDF)
- Emergency detection systems

---

## 🔐 Security & Privacy

- No user data stored
- No PII logged
- API keys in `.env` (never committed)
- CORS configured for frontend only
- Input validation on all endpoints
- Secure document generation

---

## 🌍 Social Impact

SakhiBot addresses a critical gap in legal awareness for women in India:

- **Language Barrier:** 9 Indian languages supported
- **Information Access:** Legal rights explained simply
- **Document Assistance:** Ready-to-file complaint drafts
- **Resource Discovery:** Nearest help centers by location
- **Safety Planning:** Personalized actionable steps
- **24x7 Availability:** Unlike human counselors

---

## 📝 License

Educational project - Free to use for learning purposes.  
Not for commercial use without permission.

---

## 🙏 Acknowledgments

- **Legal Documents:** indiacode.nic.in, legislative.gov.in
- **LLM:** Groq (free tier)
- **Framework:** LangGraph by LangChain
- **Vector DB:** ChromaDB
- **Frontend:** React + Vite
- **UI Design:** TailwindCSS

---

## 📞 Emergency Contacts (India)

- **181** — Women's Helpline (24x7, free)
- **1091** — Women in Distress (Police)
- **7827-170-170** — NCW Helpline
- **100** — Police Emergency
- **112** — National Emergency Number

---

**Built with:** React + FastAPI + LangGraph + ChromaDB + Groq  
**Architecture:** Multi-agent RAG system with orchestration  
**Purpose:** Empowering Indian women with legal knowledge  

---

*"Technology can be a powerful tool for social change." — This project is a step in that direction.*
