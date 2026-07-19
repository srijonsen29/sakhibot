from dotenv import load_dotenv
import os

from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

# When running as `uvicorn app.main:app` from backend/, this file is at
# backend/app/config.py — parent is backend/app, grandparent is backend/
BASE_DIR = Path(__file__).resolve().parent.parent  # → backend/

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'sakhibot.db'}")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
EMBED_MODEL = "law-ai/InLegalBERT"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 5

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-dev-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")
)
BYPASS_AUTH = os.getenv("BYPASS_AUTH", "false").lower() in ("true", "1", "yes")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,https://sakhibot.vercel.app"
    ).split(",")
    if origin.strip()
]



BYPASS_AUTH = os.getenv("BYPASS_AUTH", "false").lower() == "true"

# ── model fallback chain ─────────────────────────────────────────────────────
# if first model hits rate limit, automatically tries next one
LLM_MODELS = [
    "llama-3.1-8b-instant",       # fast, low token cost — primary
    "gemma2-9b-it",                # Google Gemma — fallback 1
    "mixtral-8x7b-32768",          # Mixtral — fallback 2
    "llama-3.3-70b-versatile",     # large model — last resort
]

LLM_MODEL = LLM_MODELS[0]  # default, overridden by fallback logic