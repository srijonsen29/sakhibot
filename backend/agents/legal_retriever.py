import chromadb
from sentence_transformers import SentenceTransformer
from config import CHROMA_PATH, EMBED_MODEL, TOP_K
from cache import get as cache_get, set as cache_set
from groq_client import chat as groq_chat
from quality_gates import run_legal_accuracy_gate

# ── initialise clients ───────────────────────────────────────────────────────
print("Initialising Legal Retriever...")
_embed_model = SentenceTransformer(EMBED_MODEL)
_chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _chroma_client.get_collection("sakhibot_legal")
print(f"Legal Retriever ready. DB has {_collection.count()} chunks.")

# Max regeneration attempts for the quality gate. Each attempt costs one
# generation call + one judge call, so keep this modest — 2 attempts
# (1 generation + up to 1 retry) balances accuracy against latency/cost.
GATE_MAX_ATTEMPTS = 2

QUERY_ROUTING = {
    "Domestic Violence Act 2005": [
        "domestic violence", "dv act", "protection order", "residence order",
        "shared household", "aggrieved", "protection officer", "monetary relief",
        "custody order", "section 12", "section 18", "section 19", "section 3",
        "husband beat", "husband violence", "pati maar", "ghar mein maar",
        "file dv", "dv complaint", "magistrate complaint"
    ],
    "POSH Act 2013": [
        "sexual harassment", "workplace harassment", "posh", "icc",
        "internal complaints", "internal committee", "office harassment",
        "employer harassment", "section 2", "section 4", "section 9",
        "unwelcome", "sexual favour", "hostile work", "file complaint office",
        "complaint against boss", "harassment at work"
    ],
    "Indian Penal Code": [
        "498a", "section 498", "cruelty husband", "ipc", "penal code",
        "criminal", "punishment husband", "husband relative cruelty",
        "section 354", "section 376", "assault woman", "criminal force",
        "hurt wife", "bodily harm"
    ],
    "Dowry Prohibition Act": [
        "dowry", "dowry demand", "dowry prohibition", "dahej",
        "bride burning", "section 3 dowry", "section 4 dowry",
        "property demand marriage", "valuables marriage"
    ],
    "Maternity Benefit Act": [
        "maternity", "maternity leave", "pregnancy leave", "nursing",
        "maternity benefit", "weeks leave", "delivery leave",
        "pregnant employee", "childbirth leave"
    ],
    "Equal Remuneration Act": [
        "equal pay", "equal remuneration", "same work pay",
        "gender pay gap", "pay discrimination", "section 4 remuneration",
        "less salary woman", "woman paid less"
    ],
    "Code of Criminal Procedure": [
        "fir", "police complaint", "arrest", "bail", "first information",
        "section 154", "refuse fir", "police refuse", "cognizable",
        "magistrate court", "register complaint police"
    ],
    "Constitution of India": [
        "fundamental rights", "article 14", "article 15", "article 21",
        "constitutional rights", "right to equality", "right to life",
        "article 19", "basic rights"
    ],
}


# ── system prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are SakhiBot, a legal rights assistant for women in India.

Your rules:
1. Answer ONLY using the provided context documents. Do not use outside knowledge.
2. Always cite which Act or section your answer comes from.
3. If the answer is truly not found in the context, respond with EXACTLY this phrase and nothing else: "NOT_FOUND_IN_KB"
4. Keep answers clear and simple — the user may have limited education.
5. Be empathetic and supportive. The user may be in a difficult situation.
6. Always end with one practical next step the user can take right now.
7. Never discourage the user from seeking help.
"""


def retrieve(query: str) -> dict:
    query_lower = query.lower()

    # routing check
    target_act = None
    for act, keywords in QUERY_ROUTING.items():
        if any(kw in query_lower for kw in keywords):
            target_act = act
            break

    query_embedding = _embed_model.encode([query]).tolist()

    if target_act:
        # restrict retrieval to that Act
        results = _collection.query(
            query_embeddings=query_embedding,
            n_results=TOP_K,
            where={"source": target_act}
        )
    else:
        # normal retrieval
        results = _collection.query(
            query_embeddings=query_embedding,
            n_results=TOP_K
        )

    chunks    = results["documents"][0] if results["documents"] else []
    metadatas = results["metadatas"][0]  if results["metadatas"]  else []

    sources = []
    seen = set()
    for meta in metadatas:
        key = f"{meta['source']}_{meta['chunk_index']}"
        if key not in seen:
            seen.add(key)
            sources.append({
                "source":      meta["source"],
                "filename":    meta["filename"],
                "chunk_index": meta["chunk_index"]
            })

    return {"chunks": chunks, "sources": sources, "query": query}


def generate_answer(query: str, chunks: list, unsupported_claims: list[str] | None = None) -> str:
    """
    Generates an answer grounded in `chunks`. If `unsupported_claims` is
    provided (i.e. this is a retry from the quality gate), the prompt
    explicitly instructs the model to drop or correct those claims —
    this is what makes run_legal_accuracy_gate's retry loop actually
    improve the answer on each attempt instead of just re-asking blindly.
    """
    if not chunks:
        return (
            "I could not find relevant information in my knowledge base. "
            "Please consult a lawyer or call 181 (Women's Helpline) for immediate help."
        )

    context = "\n\n---\n\n".join([
        f"Context {i+1}:\n{chunk}"
        for i, chunk in enumerate(chunks)
    ])

    retry_instruction = ""
    if unsupported_claims:
        retry_instruction = (
            "\n\nIMPORTANT: Your previous answer included the following claims "
            "that were NOT supported by the context above and must be removed "
            "or corrected in this revised answer:\n"
            + "\n".join(f"- {c}" for c in unsupported_claims)
            + "\nRewrite the answer using ONLY what is directly stated in the context."
        )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": (
            f"Context documents:\n{context}\n\n"
            f"Question: {query}\n\n"
            f"Answer based only on the context above.{retry_instruction}"
        )}
    ]

    return groq_chat(messages, temperature=0.1, max_tokens=1024)


def score_confidence(answer: str, chunks: list) -> str:
    """
    Legacy confidence heuristic — kept for backwards compatibility with any
    code that may still call it directly. The main run() pipeline now
    derives confidence from the quality gate's verdict instead (see below),
    which reflects actual LLM-judged groundedness rather than chunk count.
    """
    if "NOT_FOUND_IN_KB" in answer:
        return "low"
    if len(chunks) >= 3:
        return "high"
    if len(chunks) >= 1:
        return "medium"
    return "low"


def run(query: str) -> dict:
    """Full pipeline with caching + hybrid retrieval + quality-gated generation."""

    # ── hardcoded factual answers not in any PDF ──────────────────────────────
    HARDCODED = {
        "helpline": {
            "keywords": ["helpline", "helpline number", "women helpline",
                         "distress number", "emergency number women",
                         "181", "1091", "call for help"],
            "answer": (
                "Women's helplines in India:\n\n"
                "• 181 — Women's Helpline (24x7, free, all states)\n"
                "• 1091 — Women in Distress (Police)\n"
                "• 7827-170-170 — NCW Helpline\n"
                "• 100 — Police Emergency\n"
                "• 112 — National Emergency Number\n\n"
                "Practical next step: Save 181 in your phone right now. "
                "It is free, confidential, and available 24 hours."
            ),
            "sources": [{"source": "National Commission for Women",
                         "filename": "ncw_helplines", "chunk_index": 0}]
        }
    }

    # check hardcoded answers first — no LLM call, no gate needed
    query_lower = query.lower()
    for key, data in HARDCODED.items():
        if any(kw in query_lower for kw in data["keywords"]):
            return {
                "answer":         data["answer"],
                "sources":        data["sources"],
                "chunks":         [],
                "confidence":     "high",
                "quality_verdict": {"grounded": True, "score": 100, "reason": "hardcoded_answer"},
                "query":          query
            }

    # check cache
    cached = cache_get(query)
    if cached:
        return cached

    # normal pipeline
    retrieval = retrieve(query)
    chunks    = retrieval["chunks"]
    sources   = retrieval["sources"]

    if not chunks:
        # nothing to ground an answer in — skip the gate entirely, no point
        # judging a response that was never grounded in the first place
        answer = (
            "I could not find relevant information in my knowledge base. "
            "Please consult a lawyer or call 181 (Women's Helpline) for immediate help."
        )
        result = {
            "answer":          answer,
            "sources":         [],
            "chunks":          [],
            "confidence":      "low",
            "quality_verdict": {"grounded": False, "score": 0, "reason": "no_chunks_retrieved"},
            "query":           query
        }
        cache_set(query, result)
        return result

    def _generate(unsupported_claims):
        return generate_answer(query, chunks, unsupported_claims)

    answer, verdict = run_legal_accuracy_gate(
        question=query,
        chunks=chunks,
        generate=_generate,
        max_attempts=GATE_MAX_ATTEMPTS,
    )

    # replace the NOT_FOUND sentinel with a friendly message *after* the gate,
    # so the gate always judges the model's raw output
    if "NOT_FOUND_IN_KB" in answer:
        answer = (
            "I could not find this specific information in my knowledge base. "
            "Please consult a lawyer or call 181 (Women's Helpline) for help."
        )

    if verdict.get("grounded") and verdict.get("score", 0) >= 85:
        confidence = "high"
    elif verdict.get("grounded"):
        confidence = "medium"
    else:
        confidence = "low"

    result = {
        "answer":          answer,
        "sources":         sources,
        "chunks":          chunks,
        "confidence":      confidence,
        "quality_verdict": verdict,
        "query":           query
    }

    cache_set(query, result)
    return result