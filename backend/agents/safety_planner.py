from core.groq_client import chat as groq_chat

# ── situational questions ─────────────────────────────────────────────────────
SITUATION_QUESTIONS = [
    {
        "id":       "immediate_safety",
        "question": "Are you safe right now, or are you in immediate danger?",
        "keywords": ["safe", "danger", "immediate", "right now", "tonight"]
    },
    {
        "id":       "children",
        "question": "Do you have children with you who also need help?",
        "keywords": ["children", "kids", "child", "baby", "son", "daughter"]
    },
    {
        "id":       "escape_plan",
        "question": "Do you have a trusted person — family member or friend — you can go to right now?",
        "keywords": ["family", "friend", "trusted", "go to", "stay with"]
    }
]

# ── safety plan generator prompt ─────────────────────────────────────────────
SAFETY_PROMPT = """You are SakhiBot, a compassionate legal rights assistant for women in India.

Based on the situation described below, create a clear, numbered safety plan.
The plan must be practical, specific, and immediately actionable.

Rules:
1. Maximum 6 steps — keep it simple and clear
2. Start with the most urgent step (if in danger, Step 1 is always "Call 181 now")
3. Include document collection if relevant (Aadhaar, marriage cert, bank passbook)
4. Mention the nearest One Stop Centre as a safe destination
5. Reference specific laws where helpful (DV Act Section 18, CrPC Section 154)
6. Use simple language — the user may have limited education
7. Be warm and encouraging — the user may be frightened
8. End with "You are not alone. Help is available."

Format EXACTLY like this — numbered steps only, no headers:
1. [First immediate action]
2. [Second action]
3. [Third action]
...

Situation details:
{situation}
"""


def extract_situation_from_history(history: list) -> dict:
    """
    Extracts situational details from conversation history.
    Returns dict with keys: immediate_safety, children, escape_plan,
    location, incident_type, has_document_need
    """
    if not history:
        return {}

    situation = {
        "immediate_safety": "unknown",
        "children":         "unknown",
        "escape_plan":      "unknown",
        "location":         "",
        "incident_type":    "domestic violence",
        "raw_messages":     []
    }

    for msg in history:
        if not isinstance(msg, dict):
            continue
        role    = msg.get("role", "")
        content = msg.get("content", "").lower()

        if role != "user":
            continue

        situation["raw_messages"].append(content)

        # detect immediate danger
        danger_words = ["danger", "hitting me", "beating me", "scared",
                        "afraid", "threatening", "hurt me", "violent",
                        "maar raha", "darr", "help me now", "bachao"]
        safe_words   = ["safe", "not in danger", "safe right now", "okay now"]

        if any(w in content for w in danger_words):
            situation["immediate_safety"] = "danger"
        elif any(w in content for w in safe_words):
            situation["immediate_safety"] = "safe"

        # detect children
        child_words = ["children", "child", "kids", "baby", "son", "daughter",
                       "bachche", "bacha"]
        if any(w in content for w in child_words):
            situation["children"] = "yes"

        # detect escape plan
        escape_words = ["family", "parents", "mother", "sister", "friend",
                        "can go to", "stay with", "maike"]
        if any(w in content for w in escape_words):
            situation["escape_plan"] = "yes"

        # detect incident type
        if "workplace" in content or "office" in content or "boss" in content:
            situation["incident_type"] = "workplace harassment"
        elif "dowry" in content or "dahej" in content:
            situation["incident_type"] = "dowry harassment"
        elif "498" in content or "cruelty" in content:
            situation["incident_type"] = "cruelty by husband"

    return situation


def build_situation_summary(situation: dict) -> str:
    """Builds a text summary of the situation for the LLM prompt."""
    lines = []

    if situation.get("immediate_safety") == "danger":
        lines.append("⚠ IMMEDIATE DANGER: The person is in danger right now.")
    elif situation.get("immediate_safety") == "safe":
        lines.append("The person is currently safe but needs guidance.")
    else:
        lines.append("Safety status is unknown — assume caution.")

    if situation.get("children") == "yes":
        lines.append("The person has children who also need to be considered in the plan.")

    if situation.get("escape_plan") == "yes":
        lines.append("The person has a trusted person (family/friend) they can go to.")
    else:
        lines.append("The person may not have a trusted escape route — include shelter options.")

    inc = situation.get("incident_type", "domestic violence")
    lines.append(f"Type of situation: {inc}")

    msgs = situation.get("raw_messages", [])
    if msgs:
        lines.append(f"User described: {' | '.join(msgs[-3:])}")

    return "\n".join(lines)


def parse_plan_steps(raw_plan: str) -> list[str]:
    """
    Parses the LLM output into a clean list of steps.
    """
    steps = []
    for line in raw_plan.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # remove numbering prefix like "1." or "1)"
        import re
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
        if cleaned:
            steps.append(cleaned)
    return steps


def get_next_question(history: list) -> str:
    """
    Returns the next situational question to ask,
    or empty string if enough info collected.
    """
    # If no history at all, always start with safety
    if not history:
        return SITUATION_QUESTIONS[0]["question"]

    situation = extract_situation_from_history(history)

    if situation.get("immediate_safety") == "unknown":
        return SITUATION_QUESTIONS[0]["question"]

    if situation.get("children") == "unknown":
        return SITUATION_QUESTIONS[1]["question"]

    if situation.get("escape_plan") == "unknown":
        return SITUATION_QUESTIONS[2]["question"]

    return ""   # all questions answered

def run(query: str, history: list = []) -> dict:
    """
    Full Agent 4 pipeline.

    Input:
        query:   current user message
        history: full conversation history

    Output: {
        plan_steps:      list[str],
        plan_text:       str,
        is_urgent:       bool,
        situation:       dict,
        next_question:   str,
        ready:           bool
    }
    """
    situation     = extract_situation_from_history(history)
    next_question = get_next_question(history)
    is_urgent     = situation.get("immediate_safety") == "danger"

    # if urgent — generate plan immediately without asking all questions
    if is_urgent or not next_question:
        situation_summary = build_situation_summary(situation)

        prompt = SAFETY_PROMPT.format(situation=situation_summary)
        messages = [{"role": "user", "content": prompt}]

        raw_plan = groq_chat(messages, temperature=0.2, max_tokens=512)
        steps    = parse_plan_steps(raw_plan)

        # ensure step 1 is always call 181 if urgent
        if is_urgent and steps:
            if "181" not in steps[0]:
                steps.insert(0, "Call 181 (Women's Helpline) RIGHT NOW — "
                               "tell them you are in danger and need help immediately.")

        plan_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))

        return {
            "plan_steps":    steps,
            "plan_text":     plan_text,
            "is_urgent":     is_urgent,
            "situation":     situation,
            "next_question": "",
            "ready":         True
        }

    # not urgent — still collecting info
    return {
        "plan_steps":    [],
        "plan_text":     "",
        "is_urgent":     False,
        "situation":     situation,
        "next_question": next_question,
        "ready":         False
    }
