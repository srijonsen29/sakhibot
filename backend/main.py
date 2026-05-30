from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from orchestrator import run as orchestrate

app = FastAPI(title="SakhiBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message:   str
    language:  str  = "en"
    history:   list = []
    district:  str  = ""
    state_name: str = ""

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
    activated_agents: list = []
    asking_location:  bool = False
    detected_lang:    str  = "en"

class DocumentRequest(BaseModel):
    document_type: str
    history:       list = []

@app.get("/api/health")
def health():
    return {
        "status":  "ok",
        "project": "SakhiBot",
        "version": "Day 6 — all 4 agents + LangGraph orchestrator"
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    result = orchestrate(
        message=req.message,
        language=req.language,
        history=req.history,
        district=req.district,
        state_name=req.state_name
    )
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        resources=result["resources"],
        helplines=result["helplines"],
        safety_plan=result["safety_plan"],
        document_ready=result["document_ready"],
        document_type=result["document_type"],
        next_question=result["next_question"],
        is_emergency=result["is_emergency"],
        activated_agents=result["activated_agents"],
        asking_location=result["asking_location"],
        detected_lang=req.language
    )

@app.post("/api/document")
async def generate_document(req: DocumentRequest):
    from agents.doc_drafter import docx_to_pdf_bytes, extract_collected_fields
    fields    = extract_collected_fields(req.history)
    pdf_bytes = docx_to_pdf_bytes(req.document_type, fields)
    filename  = f"sakhibot_{req.document_type}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )