from groq_client import chat as groq_chat
from quality_gates import critique_safety_output

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

SAFETY_PROMPT = """You are SakhiBot, a compassionate legal rights assistant for women in India.

Based on the situation described below, create a clear, numbered safety plan.
The plan must be practical, specific, and immediately actionable.

Rules:
1. Maximum 6 steps — keep it simple and clear
2. Start with the most urgent step (if in danger, Step 1 is always "Call 181 now")
3. Include document collection if relevant (Aadhaar, marriage cert, bank passbook)
4. Mention the nearest One Stop Centre as a safe destination
5. ONLY cite a specific Act or Section if it appears in "Legally grounded acts available"
   below. If that list is empty, give practical guidance WITHOUT naming any Act or Section.
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

Legally grounded acts available: {available_acts}
{feedback_block}
"""

MAX_ATTEMPTS = 2


def extract_situation_from_history(history: list) -> dict:
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

        danger_words = ["danger", "hitting me", "beating me", "scared",
                        "afraid", "threatening", "hurt me", "violent",
                        "maar raha", "darr", "help me now", "bachao"]
        safe_words   = ["safe", "not in danger", "safe right now", "okay now"]

        if any(w in content for w in danger_words):
            situation["immediate_safety"] = "danger"
        elif any(w in content for w in safe_words):
            situation["immediate_safety"] = "safe"

        child_words = ["children", "child", "kids", "baby", "son", "daughter",
                       "bachche", "bacha"]
        if any(w in content for w in child_words):
            situation["children"] = "yes"

        escape_words = ["family", "parents", "mother", "sister", "friend",
                        "can go to", "stay with", "maike"]
        if any(w in content for w in escape_words):
            situation["escape_plan"] = "yes"

        if "workplace" in content or "office" in content or "boss" in content:
            situation["incident_type"] = "workplace harassment"
        elif "dowry" in content or "dahej" in content:
            situation["incident_type"] = "dowry harassment"
        elif "498" in content or "cruelty" in content:
            situation["incident_type"] = "cruelty by husband"

    return situation


def build_situation_summary(situation: dict) -> str:
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
    import re
    steps = []
    for line in raw_plan.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
        if cleaned:
            steps.append(cleaned)
    return steps


def get_next_question(history: list) -> str:
    if not history:
        return SITUATION_QUESTIONS[0]["question"]

    situation = extract_situation_from_history(history)

    if situation.get("immediate_safety") == "unknown":
        return SITUATION_QUESTIONS[0]["question"]
    if situation.get("children") == "unknown":
        return SITUATION_QUESTIONS[1]["question"]
    if situation.get("escape_plan") == "unknown":
        return SITUATION_QUESTIONS[2]["question"]
    return ""


def _available_act_names(retrieved_sources: list[dict] | None) -> str:
    """Turns retrieved legal sources into a short comma list for the prompt."""
    if not retrieved_sources:
        return "(none retrieved this session)"
    names = {s.get("source", "") for s in retrieved_sources if isinstance(s, dict)}
    names.discard("")
    return ", ".join(sorted(names)) if names else "(none retrieved this session)"


def _generate_plan(
    situation_summary: str,
    available_acts: str,
    feedback: list[str]
) -> list[str]:
    """Runs one LLM generation attempt, folding in prior critique warnings."""
    feedback_block = ""
    if feedback:
        feedback_block = (
            "\nIMPORTANT — fix these problems from your previous attempt:\n"
            + "\n".join(f"- {w}" for w in feedback)
        )

    prompt = SAFETY_PROMPT.format(
        situation=situation_summary,
        available_acts=available_acts,
        feedback_block=feedback_block
    )
    raw_plan = groq_chat(
        [{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=512
    )
    return parse_plan_steps(raw_plan)


def run(
    query: str,
    history: list = [],
    retrieved_sources: list[dict] | None = None
) -> dict:
    ...
    combined_history = history + [{"role": "user", "content": query}]
    situation     = extract_situation_from_history(combined_history)
    next_question = get_next_question(combined_history)
    is_urgent     = situation.get("immediate_safety") == "danger"

    if not (is_urgent or not next_question):
        return {
            "plan_steps":      [],
            "plan_text":       "",
            "is_urgent":       False,
            "situation":       situation,
            "next_question":   next_question,
            "ready":           False,
            "quality_verdict": None,
        }

    situation_summary = build_situation_summary(situation)
    available_acts     = _available_act_names(retrieved_sources)

    feedback     = []
    steps        = []
    last_verdict = {}

    for attempt in range(1, MAX_ATTEMPTS + 1):
        steps = _generate_plan(situation_summary, available_acts, feedback)

        # deterministic fix — always applied before the gate, never worth a retry
        if is_urgent and steps and "181" not in steps[0]:
            steps.insert(0, "Call 181 (Women's Helpline) RIGHT NOW — "
                            "tell them you are in danger and need help immediately.")

        candidate_result = {
            "plan_steps": steps,
            "is_urgent":  is_urgent,
        }
        last_verdict = critique_safety_output(candidate_result, retrieved_sources)
        last_verdict["attempt"] = attempt

        if last_verdict.get("passed"):
            break

        # feed the specific warnings back in for the retry
        feedback = last_verdict.get("warnings", [])

    plan_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))

    return {
        "plan_steps":      steps,
        "plan_text":        plan_text,
        "is_urgent":        is_urgent,
        "situation":        situation,
        "next_question":    "",
        "ready":            True,
        "quality_verdict":  last_verdict,
    }