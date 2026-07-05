from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHROMA_PATH = "chroma_db"
EMBED_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 5

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-dev-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")
)

# ── model fallback chain ─────────────────────────────────────────────────────
# UPDATED (Jul 2026): llama-3.1-8b-instant, llama-3.3-70b-versatile, and
# mixtral-8x7b-32768 have all been deprecated by Groq. gemma2-9b-it is also
# past its recommended-migration date. Swapped in Groq's current
# recommended replacements below.
# Groq's lineup changes often — if any of these start failing, check
# https://console.groq.com/docs/deprecations for the latest recommended IDs.
LLM_MODELS = [
    "openai/gpt-oss-20b",          # fast, low cost — primary
    "openai/gpt-oss-120b",         # stronger reasoning — fallback 1
    "qwen/qwen3.6-27b",            # fallback 2 (also used for vision below)
]

LLM_MODEL = LLM_MODELS[0]  # default, overridden by fallback logic

# ── vision model (for image analysis) ─────────────────────────────────────────
# As of Jul 2026, Llama 4 Scout/Maverick (previously Groq's vision models)
# have been deprecated. qwen/qwen3.6-27b is currently the only Groq
# vision-capable chat model, and it's a *preview* model (Groq's words: meant
# for evaluation, not guaranteed stable production availability). Re-check
# https://console.groq.com/docs/vision before relying on this long-term.
VISION_MODEL = "qwen/qwen3.6-27b"

