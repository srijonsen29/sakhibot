# SakhiBot - Quick Start Guide

## Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API key (free at https://console.groq.com)

## 5-Minute Setup

### Step 1: Clone & Navigate
```bash
cd sakhibot
```

### Step 2: Backend Setup
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

### Step 3: Frontend Setup (New Terminal)
```bash
cd frontend

# Install dependencies
npm install

# Start frontend dev server
npm run dev
```
Frontend runs at: http://localhost:5173

### Step 4: Open Browser
Go to http://localhost:5173 and start chatting!

## Test Individual Agents

```bash
cd backend

# Test Legal Retriever
python tests/test_agent1.py

# Test Document Drafter  
python tests/test_agent2.py

# Test Resource Locator
python tests/test_agent3.py

# Test Safety Planner
python tests/test_agent4.py
```

## Common Issues

### ChromaDB Not Found
```bash
python scripts/ingest.py
```

### Import Errors
Make sure you're in the correct directory and virtual environment is activated.

### Port Already in Use
Change ports in:
- Backend: `uvicorn main:app --port 8001`
- Frontend: Edit `vite.config.js` to change port 5173

### Missing API Key
Create `.env` in `backend/` folder with:
```
GROQ_API_KEY=your_actual_key_here
```

## API Endpoints

### Chat
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is domestic violence?", "language": "en"}'
```

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Languages
```bash
curl http://localhost:8000/api/languages
```

## File Organization

```
sakhibot/
├── backend/
│   ├── agents/       → 4 AI agents
│   ├── core/         → Utilities (config, cache, translate, etc.)
│   ├── scripts/      → Setup scripts (ingest.py)
│   ├── tests/        → Test files
│   ├── data/         → resources.json
│   ├── docs/         → PDFs
│   ├── templates/    → DOCX templates
│   └── main.py       → FastAPI app
│
└── frontend/
    ├── src/
    │   ├── components/  → React components
    │   ├── App.jsx      → Main app
    │   └── api.js       → API client
    └── package.json
```

## Next Steps

1. Add more legal documents to `backend/docs/`
2. Update resource database in `backend/data/resources.json`
3. Customize document templates in `backend/templates/`
4. Modify styling in `frontend/src/index.css`

## Support

For detailed documentation, see:
- Main README: `README.md`
- Structure Guide: `STRUCTURE.md`
- Backend Docs: `backend/README.md`

## Production Deployment

### Backend
```bash
cd backend
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend
```bash
cd frontend
npm run build
# Deploy dist/ folder to Vercel, Netlify, or any static host
```

---

**Built with:** React + FastAPI + LangGraph + ChromaDB + Groq
