# SakhiBot - Complete Project Structure

## Directory Organization

```
sakhibot/
│
├── .git/                    # Git version control
├── .gitignore               # Git ignore patterns
├── README.md                # Main project documentation
├── STRUCTURE.md             # This file - project structure guide
│
├── backend/                 # Python FastAPI backend
│   │
│   ├── agents/              # Multi-agent system (4 agents)
│   │   ├── __init__.py
│   │   ├── legal_retriever.py     # Agent 1: Legal knowledge retrieval
│   │   ├── doc_drafter.py         # Agent 2: Document generation
│   │   ├── resource_locator.py    # Agent 3: Find help centers
│   │   └── safety_planner.py      # Agent 4: Safety plan creation
│   │
│   ├── core/                # Core utilities & configuration
│   │   ├── __init__.py
│   │   ├── config.py              # Environment & settings
│   │   ├── cache.py               # Query caching layer
│   │   ├── translate.py           # Multilingual translation
│   │   ├── emergency.py           # Emergency detection
│   │   └── groq_client.py         # LLM API client
│   │
│   ├── data/                # Static data files
│   │   └── resources.json         # Helplines, shelters, OSCs
│   │
│   ├── docs/                # Legal documents (PDFs)
│   │   ├── dv_act_2005.pdf
│   │   ├── posh_act_2013.pdf
│   │   ├── ipc_498a.pdf
│   │   ├── dowry_act.pdf
│   │   ├── maternity_act.pdf
│   │   ├── equal_remuneration_act.pdf
│   │   ├── crpc.pdf
│   │   ├── constitution.pdf
│   │   └── hindu_marriage_act_1955.pdf
│   │
│   ├── templates/           # Document templates (DOCX)
│   │   ├── fir_template.docx
│   │   ├── dv_complaint.docx
│   │   └── posh_complaint.docx
│   │
│   ├── scripts/             # Setup & maintenance scripts
│   │   ├── __init__.py
│   │   ├── ingest.py              # Ingest PDFs into ChromaDB
│   │   └── create_templates.py    # Generate document templates
│   │
│   ├── tests/               # Test files
│   │   ├── __init__.py
│   │   ├── test_agent1.py
│   │   ├── test_agent2.py
│   │   ├── test_agent3.py
│   │   ├── test_agent4.py
│   │   ├── test_lang.py
│   │   ├── test_retrieval.py
│   │   ├── test_dv_output.pdf
│   │   ├── test_fir_output.pdf
│   │   └── test_posh_output.pdf
│   │
│   ├── chroma_db/           # ChromaDB vector database (auto-created)
│   ├── query_cache/         # Query cache files (auto-created)
│   ├── myenv/               # Python virtual environment (gitignored)
│   │
│   ├── main.py              # FastAPI application entry point
│   ├── orchestrator.py      # LangGraph orchestrator (routes to agents)
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Example environment file
│   └── README.md            # Backend-specific documentation
│
└── frontend/                # React + Vite frontend
    │
    ├── src/                 # Source code
    │   ├── components/      # React components
    │   │   ├── ChatWindow.jsx
    │   │   ├── MessageBubble.jsx
    │   │   ├── InputBar.jsx
    │   │   ├── VoiceButton.jsx
    │   │   ├── LanguageSelector.jsx
    │   │   ├── SourceCard.jsx
    │   │   ├── ResourceCard.jsx
    │   │   ├── SafetyPlanCard.jsx
    │   │   ├── DocumentCard.jsx
    │   │   ├── EmergencyBanner.jsx
    │   │   ├── TypingIndicator.jsx
    │   │   └── LandingPage.jsx
    │   │
    │   ├── assets/          # Static assets
    │   │   ├── hero.png
    │   │   ├── react.svg
    │   │   └── vite.svg
    │   │
    │   ├── App.jsx          # Main React component
    │   ├── App.css          # App styles
    │   ├── main.jsx         # React entry point
    │   ├── index.css        # Global styles
    │   └── api.js           # API client (axios)
    │
    ├── public/              # Public assets
    │   ├── favicon.svg
    │   └── icons.svg
    │
    ├── node_modules/        # npm dependencies (gitignored)
    ├── .vite/               # Vite cache (gitignored)
    │
    ├── index.html           # HTML entry point
    ├── package.json         # npm dependencies
    ├── package-lock.json    # npm lock file
    ├── vite.config.js       # Vite configuration
    ├── eslint.config.js     # ESLint configuration
    ├── .gitignore           # Frontend gitignore
    └── README.md            # Frontend documentation

```

## Key File Descriptions

### Backend Core Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, API endpoints, CORS, translation layer |
| `orchestrator.py` | LangGraph StateGraph, routes queries to agents |
| `core/config.py` | Environment variables, model settings, paths |
| `core/cache.py` | 7-day query cache with MD5 key generation |
| `core/translate.py` | 9-language translation using deep-translator |
| `core/emergency.py` | Detects emergency keywords, builds SOS responses |
| `core/groq_client.py` | Groq API client with automatic model fallback |

### Agent Files

| Agent | File | Purpose |
|-------|------|---------|
| Agent 1 | `agents/legal_retriever.py` | ChromaDB vector search + LLM answer generation |
| Agent 2 | `agents/doc_drafter.py` | Conversational detail collection + PDF generation |
| Agent 3 | `agents/resource_locator.py` | Fuzzy location matching + resource database |
| Agent 4 | `agents/safety_planner.py` | Situational analysis + personalized safety steps |

### Frontend Components

| Component | Purpose |
|-----------|---------|
| `App.jsx` | Main state manager, API integration, screen routing |
| `ChatWindow.jsx` | Message list, auto-scroll, emergency banner |
| `MessageBubble.jsx` | User/bot messages, TTS, WhatsApp share |
| `InputBar.jsx` | Text input + voice button + send |
| `VoiceButton.jsx` | Web Speech API integration |
| `LanguageSelector.jsx` | Dropdown for 9 languages |
| `DocumentCard.jsx` | Download generated legal documents |
| `ResourceCard.jsx` | Display OSCs, shelters, helplines |
| `SafetyPlanCard.jsx` | Numbered safety action steps |
| `SourceCard.jsx` | Legal citation chips |
| `EmergencyBanner.jsx` | Red SOS banner with 181/100/112 |

## Data Flow

```
1. User types or speaks message
   ↓
2. Frontend (App.jsx) → POST /api/chat
   ↓
3. Backend (main.py) receives request
   ↓
4. Translate to English (translate.py)
   ↓
5. Check for emergency (emergency.py)
   ↓
6. Orchestrator (orchestrator.py) classifies intent
   ↓
7. Activate relevant agents in parallel
   ├─ Agent 1: Retrieve legal info
   ├─ Agent 2: Draft documents
   ├─ Agent 3: Find resources
   └─ Agent 4: Create safety plan
   ↓
8. Synthesize all agent outputs
   ↓
9. Translate back to user's language
   ↓
10. Return JSON response to frontend
   ↓
11. Frontend displays message + cards + actions
```

## Important Paths

### Backend Paths (relative to `backend/`)
- Legal PDFs: `docs/*.pdf`
- Document templates: `templates/*.docx`
- Resource database: `data/resources.json`
- Vector DB: `chroma_db/` (auto-created by ingest.py)
- Cache: `query_cache/` (auto-created)
- Virtual env: `myenv/` (create with `python -m venv myenv`)

### Frontend Paths (relative to `frontend/`)
- React entry: `src/main.jsx`
- Main component: `src/App.jsx`
- Components: `src/components/*.jsx`
- API client: `src/api.js`
- Static assets: `public/`
- Build output: `dist/` (created by `npm run build`)

## Environment Variables

### Backend `.env`
```env
GROQ_API_KEY=your_groq_api_key_here
```

### Frontend `.env` (optional)
```env
VITE_API_URL=http://localhost:8000
```

## Git Ignored Files

- `backend/myenv/` - Python virtual environment
- `backend/chroma_db/` - Vector database
- `backend/query_cache/` - Query cache files
- `backend/.env` - Environment variables
- `backend/__pycache__/` - Python bytecode
- `frontend/node_modules/` - npm packages
- `frontend/.vite/` - Vite cache
- `frontend/dist/` - Build output
- `*.pdf` output files from tests
- `*.log` files

## Setup Order

1. Backend setup:
   ```bash
   cd backend
   python -m venv myenv
   myenv\Scripts\activate
   pip install -r requirements.txt
   python scripts/ingest.py
   uvicorn main:app --reload
   ```

2. Frontend setup (in new terminal):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Access:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Tech Stack Summary

### Backend
- **Framework:** FastAPI 
- **Agent Orchestration:** LangGraph (StateGraph)
- **Vector DB:** ChromaDB
- **Embeddings:** sentence-transformers (all-MiniLM-L6-v2)
- **LLM:** Groq API (Llama 3.1 8B → Gemma2 → Mixtral fallback)
- **Translation:** deep-translator + langdetect
- **PDF Processing:** PyMuPDF (fitz)
- **Document Gen:** python-docx + reportlab

### Frontend
- **Framework:** React 19
- **Build Tool:** Vite 8
- **Styling:** TailwindCSS 4
- **HTTP Client:** axios
- **Voice:** Web Speech API (native)

---

**Last Updated:** Structure reorganization on 2026-06-19