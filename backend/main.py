from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
import traceback

from auth import router as auth_router
from database import Base, engine
import models
from translate  import detect_language, translate_to_english, translate_from_english
from emergency  import detect_emergency, build_emergency_response
from orchestrator import run as orchestrate

app = FastAPI(
    title="SakhiBot API",
    description="AI-powered women's legal rights assistant for India",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://sakhibot.vercel.app",   # update with your Vercel URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── request / response models ─────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message:    str
    language:   str  = ""     # optional — auto-detected if empty
    history:    list = []
    district:   str  = ""
    state_name: str  = ""

class ChatResponse(BaseModel):
    answer:           str
    sources:          list = []
    resources:        list = []
    helplines:        list = []
    safety_plan:      list = []
    document_ready:   bool = False
    document_type:    str  = ""
    next_question:    str  = ""
    is_emergency:     bool = False
    severity:         str  = "none"
    activated_agents: list = []
    asking_location:  bool = False
    detected_lang:    str  = "en"
    language_name:    str  = "English"

class DocumentRequest(BaseModel):
    document_type: str
    history:       list = []


# ── health check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {
        "status":  "ok",
        "project": "SakhiBot",
        "version": "1.0.0",
        "backend": "complete",
        "agents":  [
            "legal_retriever",
            "doc_drafter",
            "resource_locator",
            "safety_planner",
            "langgraph_orchestrator"
        ],
        "languages": [
            "English", "Hindi", "Bengali",
            "Tamil", "Telugu", "Marathi",
            "Gujarati", "Kannada", "Malayalam"
        ]
    }


# ── main chat endpoint ────────────────────────────────────────────────────────
@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        message = req.message.strip()
        if not message:
            return ChatResponse(
                answer="Please type or speak your question.",
                detected_lang="en",
                language_name="English"
            )

        # ── step 1: detect language ───────────────────────────────────────────
        detected_lang = req.language if req.language else detect_language(message)
        from translate import get_language_name
        language_name = get_language_name(detected_lang)

        print(f"\n{'='*50}")
        print(f"[REQUEST] lang={detected_lang} | msg={message[:60]}...")

        # ── step 2: emergency check ───────────────────────────────────────────
        em = detect_emergency(message, detected_lang)

        if em.is_emergency and em.severity in ["critical", "high"]:
            print(f"[EMERGENCY] severity={em.severity} | trigger='{em.trigger_word}'")
            response = build_emergency_response(detected_lang, em.severity)
            return ChatResponse(
                answer=response["answer"],
                helplines=response["helplines"],
                is_emergency=True,
                severity=em.severity,
                activated_agents=["emergency"],
                detected_lang=detected_lang,
                language_name=language_name
            )

        # ── step 3: translate input to English ───────────────────────────────
        english_message = translate_to_english(message, detected_lang)
        print(f"[TRANSLATE IN]  {detected_lang}→en: {english_message[:60]}...")

        # also translate history user messages for context
        translated_history = []
        for msg in req.history:
            if isinstance(msg, dict):
                if msg.get("role") == "user" and detected_lang != "en":
                    translated_content = translate_to_english(
                        msg.get("content", ""), detected_lang
                    )
                    translated_history.append({
                        "role":    "user",
                        "content": translated_content
                    })
                else:
                    translated_history.append(msg)

        # ── step 4: run LangGraph orchestrator ───────────────────────────────
        result = orchestrate(
            message=english_message,
            language=detected_lang,
            history=translated_history,
            district=req.district,
            state_name=req.state_name
        )

        print(f"[ORCHESTRATOR] agents={result['activated_agents']}")

        # ── step 5: translate answer back to user language ───────────────────
        answer_translated = translate_from_english(
            result["answer"], detected_lang
        )
        print(f"[TRANSLATE OUT] en→{detected_lang}: {answer_translated[:60]}...")

        # translate next_question if asking user something
        next_q = result.get("next_question", "")
        if next_q and detected_lang != "en":
            next_q = translate_from_english(next_q, detected_lang)

        # ── step 6: medium emergency — add helpline note ──────────────────────
        helplines = result.get("helplines", [])
        if em.is_emergency and em.severity == "medium":
            if not helplines:
                helplines = [
                    {"name": "Women's Helpline", "phone": "181", "type": "helpline"},
                    {"name": "Police",           "phone": "100", "type": "helpline"},
                ]

        return ChatResponse(
            answer=answer_translated,
            sources=result.get("sources", []),
            resources=result.get("resources", []),
            helplines=helplines,
            safety_plan=result.get("safety_plan", []),
            document_ready=result.get("document_ready", False),
            document_type=result.get("document_type", ""),
            next_question=next_q,
            is_emergency=em.is_emergency,
            severity=em.severity,
            activated_agents=result.get("activated_agents", []),
            asking_location=result.get("asking_location", False),
            detected_lang=detected_lang,
            language_name=language_name
        )

    except Exception as e:
        print(f"[ERROR] {traceback.format_exc()}")
        return ChatResponse(
            answer=(
                "I'm sorry, I encountered an error. "
                "Please try again or call 181 (Women's Helpline) for immediate help."
            ),
            is_emergency=False,
            detected_lang="en",
            language_name="English"
        )


# ── document download endpoint ────────────────────────────────────────────────
@app.post("/api/document")
async def generate_document(req: DocumentRequest):
    try:
        from agents.doc_drafter import (
            docx_to_pdf_bytes,
            extract_collected_fields
        )
        fields    = extract_collected_fields(req.history)
        pdf_bytes = docx_to_pdf_bytes(req.document_type, fields)
        filename  = f"sakhibot_{req.document_type}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "message": "Document generation failed"}
        )


# ── languages list endpoint ───────────────────────────────────────────────────
@app.get("/api/languages")
def get_languages():
    return {
        "languages": [
            {"code": "en", "name": "English",    "native": "English"},
            {"code": "hi", "name": "Hindi",      "native": "हिंदी"},
            {"code": "bn", "name": "Bengali",    "native": "বাংলা"},
            {"code": "ta", "name": "Tamil",      "native": "தமிழ்"},
            {"code": "te", "name": "Telugu",     "native": "తెలుగు"},
            {"code": "mr", "name": "Marathi",    "native": "मराठी"},
            {"code": "gu", "name": "Gujarati",   "native": "ગુજરાતી"},
            {"code": "kn", "name": "Kannada",    "native": "ಕನ್ನಡ"},
            {"code": "ml", "name": "Malayalam",  "native": "മലയാളം"},
        ]
    }
