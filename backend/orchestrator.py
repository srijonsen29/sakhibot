from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
from agents.legal_retriever  import run as legal_run
from agents.doc_drafter      import run as doc_run, detect_document_type
from agents.resource_locator import run as resource_run, needs_location
from agents.safety_planner   import run as safety_run, extract_situation_from_history
from groq_client             import chat as groq_chat

# ── state definition ──────────────────────────────────────────────────────────
class SakhiBotState(TypedDict):
    # input
    message:         str
    language:        str
    history:         list
    district:        str
    state_name:      str

    # routing
    activated_agents: list[str]
    is_emergency:     bool

    # agent outputs
    legal_answer:    str
    legal_sources:   list
    doc_result:      dict
    resource_result: dict
    safety_result:   dict

    # final output
    final_answer:    str
    final_sources:   list
    final_resources: list
    final_helplines: list
    final_plan:      list
    document_ready:  bool
    document_type:   str
    next_question:   str
    asking_location: bool


# ── emergency keywords ────────────────────────────────────────────────────────
EMERGENCY_KEYWORDS = {
    "en":  ["help me now", "in danger", "hitting me", "killing me",
            "he will kill", "very scared", "please help", "beating me",
            "going to hurt", "emergency"],
    "hi":  ["bachao", "maar raha", "khatra", "madad karo", "darr",
            "please help", "abhi help", "maar dalega"],
    "bn":  ["bachao", "sahajjo", "biponno", "marlo", "help"],
    "ta":  ["help", "udavi", "paayam", "aapatthu"],
    "te":  ["help", "sahayam", "provaadam", "chantham"],
    "mr":  ["bachao", "madad", "dhoka", "maar"],
}

def detect_emergency(message: str) -> bool:
    msg_lower = message.lower()
    for lang_keywords in EMERGENCY_KEYWORDS.values():
        if any(kw in msg_lower for kw in lang_keywords):
            return True
    return False


# ── intent classifier ─────────────────────────────────────────────────────────
def classify_intent(message: str, history: list) -> list[str]:
    """
    Classifies which agents should handle this message.
    Returns list of agent names to activate.
    """
    msg_lower = message.lower()
    agents    = ["legal"]   # legal retriever always runs

    # document drafter
    doc_type = detect_document_type(message)
    if doc_type != "none":
        agents.append("document")

    # resource locator
    if needs_location(message):
        agents.append("resource")

    # safety planner — activate when user describes their situation
    safety_triggers = [
        "what should i do", "what do i do", "help me", "how do i",
        "i am scared", "i am in danger", "he beats", "he hits",
        "my husband", "pati", "scared", "afraid", "planning to leave",
        "want to leave", "need to escape", "need help", "what are my options"
    ]
    situation = extract_situation_from_history(history)
    if any(t in msg_lower for t in safety_triggers) or situation.get("immediate_safety") == "danger":
        agents.append("safety")

    # always add resource if safety is activated (user needs help finding places)
    if "safety" in agents and "resource" not in agents:
        agents.append("resource")

    return agents


# ── node functions ────────────────────────────────────────────────────────────

def router_node(state: SakhiBotState) -> SakhiBotState:
    """Classifies the message and sets activated_agents."""
    message  = state["message"]
    history  = state.get("history", [])

    is_emergency     = detect_emergency(message)
    activated_agents = classify_intent(message, history)

    # emergency always gets resource + safety
    if is_emergency:
        for a in ["resource", "safety", "legal"]:
            if a not in activated_agents:
                activated_agents.append(a)

    return {
        **state,
        "is_emergency":     is_emergency,
        "activated_agents": activated_agents
    }


def legal_node(state: SakhiBotState) -> SakhiBotState:
    """Runs Agent 1 — Legal Retriever."""
    if "legal" not in state.get("activated_agents", []):
        return {**state, "legal_answer": "", "legal_sources": []}

    result = legal_run(state["message"])
    return {
        **state,
        "legal_answer":  result["answer"],
        "legal_sources": result["sources"]
    }


def document_node(state: SakhiBotState) -> SakhiBotState:
    """Runs Agent 2 — Document Drafter."""
    if "document" not in state.get("activated_agents", []):
        return {
            **state,
            "doc_result": {
                "needs_document": False,
                "document_ready": False,
                "document_type":  "",
                "next_question":  "",
                "message":        ""
            }
        }

    result = doc_run(state["message"], state.get("history", []))
    return {**state, "doc_result": result}


def resource_node(state: SakhiBotState) -> SakhiBotState:
    """Runs Agent 3 — Resource Locator."""
    if "resource" not in state.get("activated_agents", []):
        return {
            **state,
            "resource_result": {
                "resources":      [],
                "helplines":      [],
                "message":        "",
                "asking_for":     "",
                "location_found": False
            }
        }

    result = resource_run(
    state["message"],
    district=state.get("district", ""),
    state=state.get("state_name", "")
    )
    return {**state, "resource_result": result}

def safety_node(state: SakhiBotState) -> SakhiBotState:
    """Runs Agent 4 — Safety Planner."""
    if "safety" not in state.get("activated_agents", []):
        return {
            **state,
            "safety_result": {
                "plan_steps":    [],
                "plan_text":     "",
                "is_urgent":     False,
                "next_question": "",
                "ready":         False
            }
        }

    result = safety_run(state["message"], state.get("history", []))
    return {**state, "safety_result": result}


def synthesizer_node(state: SakhiBotState) -> SakhiBotState:
    """
    Combines all agent outputs into one clean response.
    """
    legal_answer    = state.get("legal_answer", "")
    doc_result      = state.get("doc_result", {})
    resource_result = state.get("resource_result", {})
    safety_result   = state.get("safety_result", {})
    is_emergency    = state.get("is_emergency", False)

    # build final answer
    answer_parts = []

    # emergency banner first
    if is_emergency:
        answer_parts.append(
            "🚨 I can see you may be in danger. "
            "Please call 181 (Women's Helpline) immediately — "
            "they can send help to your location.\n"
        )

    # document drafter message (overrides legal if collecting details)
    if doc_result.get("needs_document") and doc_result.get("message"):
        answer_parts.append(doc_result["message"])
    elif legal_answer:
        answer_parts.append(legal_answer)

    # resource message
    resource_msg = resource_result.get("message", "")
    if resource_msg and resource_msg not in answer_parts:
        answer_parts.append(resource_msg)

    # safety plan
    safety_plan  = safety_result.get("plan_steps", [])
    safety_ready = safety_result.get("ready", False)
    if safety_ready and safety_plan:
        answer_parts.append(
            "\n📋 Here is your step-by-step safety plan:"
        )

    final_answer = "\n\n".join(filter(None, answer_parts))

    if not final_answer:
        final_answer = (
            "I am here to help you. Could you tell me more about your situation "
            "so I can give you the right guidance?"
        )

    return {
        **state,
        "final_answer":    final_answer,
        "final_sources":   state.get("legal_sources", []),
        "final_resources": resource_result.get("resources", []),
        "final_helplines": resource_result.get("helplines", []),
        "final_plan":      safety_plan,
        "document_ready":  doc_result.get("document_ready", False),
        "document_type":   doc_result.get("document_type", ""),
        "next_question":   doc_result.get("next_question", ""),
        "asking_location": resource_result.get("asking_for") == "location"
    }


# ── build the LangGraph ───────────────────────────────────────────────────────
def build_graph():
    graph = StateGraph(SakhiBotState)

    # add nodes
    graph.add_node("router",       router_node)
    graph.add_node("legal",        legal_node)
    graph.add_node("document",     document_node)
    graph.add_node("resource",     resource_node)
    graph.add_node("safety",       safety_node)
    graph.add_node("synthesizer",  synthesizer_node)

    # entry point
    graph.set_entry_point("router")

    # router → all agents in parallel (LangGraph runs sequentially here)
    graph.add_edge("router",      "legal")
    graph.add_edge("legal",       "document")
    graph.add_edge("document",    "resource")
    graph.add_edge("resource",    "safety")
    graph.add_edge("safety",      "synthesizer")
    graph.add_edge("synthesizer", END)

    return graph.compile()


# compile once at import
_graph = build_graph()
print("LangGraph orchestrator compiled successfully.")


# ── public run function ───────────────────────────────────────────────────────
def run(
    message:   str,
    language:  str  = "en",
    history:   list = [],
    district:  str  = "",
    state_name: str = ""
) -> dict:
    """
    Main entry point for the full SakhiBot pipeline.

    Input:
        message:    user's message (in English — translation handled in main.py)
        language:   detected language code
        history:    full conversation history
        district:   user's district (optional)
        state_name: user's state (optional)

    Output: full response dict ready for FastAPI
    """
    initial_state: SakhiBotState = {
        "message":          message,
        "language":         language,
        "history":          history,
        "district":         district,
        "state_name":       state_name,
        "activated_agents": [],
        "is_emergency":     False,
        "legal_answer":     "",
        "legal_sources":    [],
        "doc_result":       {},
        "resource_result":  {},
        "safety_result":    {},
        "final_answer":     "",
        "final_sources":    [],
        "final_resources":  [],
        "final_helplines":  [],
        "final_plan":       [],
        "document_ready":   False,
        "document_type":    "",
        "next_question":    "",
        "asking_location":  False
    }

    result = _graph.invoke(initial_state)

    return {
        "answer":           result["final_answer"],
        "sources":          result["final_sources"],
        "resources":        result["final_resources"],
        "helplines":        result["final_helplines"],
        "safety_plan":      result["final_plan"],
        "document_ready":   result["document_ready"],
        "document_type":    result["document_type"],
        "next_question":    result["next_question"],
        "is_emergency":     result["is_emergency"],
        "activated_agents": result["activated_agents"],
        "asking_location":  result["asking_location"]
    }