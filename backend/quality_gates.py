import json
import os
import re
import time
from typing import Callable

from groq_client import chat as groq_chat


LOG_DIR = "quality_logs"
LOG_PATH = os.path.join(LOG_DIR, "verifier.jsonl")

SAFE_LEGAL_FALLBACK = (
    "I could not verify this answer strongly enough against my legal knowledge "
    "base. Please consult a qualified lawyer or call 181 (Women's Helpline) "
    "for immediate guidance."
)


def audit_doc_fields(fields: dict, history: list) -> dict:
    """
    LLM audit to check if extracted fields are traceable to the conversation history.
    """
    if not fields:
        return {"passed": True, "untraceable_fields": []}

    history_text = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in history
        if isinstance(msg, dict) and "role" in msg and "content" in msg
    ])

    prompt = f"""You are a strict legal document auditor.
Your job is to check if the extracted details below are traceable to the conversation history.
Every value in the fields MUST be directly supported by a statement in the conversation history.
If a value is fabricated, guessed, or hallucinated, list it as untraceable.
Do NOT flag default or placeholder values (like "As known to complainant", "As applicable", "India", or "Your District") as untraceable.

Conversation History:
{history_text}

Extracted Fields:
{json.dumps(fields, indent=2)}

Return ONLY a valid JSON object with the following structure:
{{
  "passed": true/false,
  "untraceable_fields": ["list of field names that are untraceable or hallucinated"]
}}
"""
    try:
        raw = groq_chat(
            [{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=256
        )
        verdict = _extract_json(raw)
        return {
            "passed": bool(verdict.get("passed", True)),
            "untraceable_fields": verdict.get("untraceable_fields", []) or []
        }
    except Exception as exc:
        print(f"[QUALITY] audit_doc_fields failed: {exc}")
        return {"passed": True, "untraceable_fields": []}


def log_verdict(agent: str, verdict: dict) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "agent": agent,
        **verdict,
    }
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as exc:
        print(f"[QUALITY] log failed for {agent}: {exc}")


def _extract_json(text: str) -> dict:
    cleaned = text.strip().replace("```json", "").replace("```", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start:end + 1]
    return json.loads(cleaned)


def audit_legal_answer(question: str, answer: str, chunks: list[str]) -> dict:
    if not chunks:
        return {
            "grounded": False,
            "score": 0,
            "unsupported_claims": ["No retrieved chunks were available."],
            "reason": "missing_context"
        }

    context = "\n\n---\n\n".join(
        f"Chunk {i + 1}:\n{chunk}" for i, chunk in enumerate(chunks)
    )
    prompt = f"""You are a strict Indian legal grounding judge.

Check whether every legal claim in ANSWER is directly traceable to CONTEXT.
Do not use outside knowledge. If a claim is useful but not in CONTEXT, mark it unsupported.

Return ONLY valid JSON with this exact shape:
{{
  "grounded": true,
  "score": 0-100,
  "unsupported_claims": [],
  "reason": "short explanation"
}}

QUESTION:
{question}

CONTEXT:
{context}

ANSWER:
{answer}
"""
    try:
        raw = groq_chat(
            [{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=600
        )
        verdict = _extract_json(raw)
        return {
            "grounded": bool(verdict.get("grounded")),
            "score": int(verdict.get("score", 0)),
            "unsupported_claims": verdict.get("unsupported_claims", []) or [],
            "reason": verdict.get("reason", "")
        }
    except Exception as exc:
        return {
            "grounded": False,
            "score": 0,
            "unsupported_claims": [f"Judge call failed: {exc}"],
            "reason": "judge_error"
        }


def run_legal_accuracy_gate(
    *,
    question: str,
    chunks: list[str],
    generate: Callable[[list[str]], str],
    max_attempts: int = 3
) -> tuple[str, dict]:
    unsupported_claims: list[str] = []
    last_answer = ""
    last_verdict = {}

    for attempt in range(1, max_attempts + 1):
        last_answer = generate(unsupported_claims)
        last_verdict = audit_legal_answer(question, last_answer, chunks)
        last_verdict["attempt"] = attempt
        last_verdict["max_attempts"] = max_attempts
        log_verdict("legal_retriever", last_verdict)

        if last_verdict.get("grounded") and last_verdict.get("score", 0) >= 75:
            return last_answer, last_verdict

        unsupported_claims = last_verdict.get("unsupported_claims", [])

    fallback_verdict = {
        **last_verdict,
        "grounded": False,
        "final_action": "safe_fallback",
        "attempt": max_attempts,
    }
    log_verdict("legal_retriever", fallback_verdict)
    return SAFE_LEGAL_FALLBACK, fallback_verdict


def critique_doc_output(result: dict, history: list) -> dict:
    history_text = "\n".join(
        str(msg.get("content", "")) for msg in history
        if isinstance(msg, dict)
    ).lower()
    warnings = []
    untraceable = []

    if result.get("document_ready"):
        if not history_text.strip():
            warnings.append("Document marked ready without conversation history.")
        if result.get("document_type") in ("", "none"):
            warnings.append("Document ready but document_type is missing.")

    fields = result.get("fields")
    if fields:
        audit = audit_doc_fields(fields, history)
        if not audit["passed"]:
            untraceable = audit["untraceable_fields"]
            for field in untraceable:
                warnings.append(f"Field '{field}' is not traceable to conversation.")

    verdict = {
        "passed": not warnings,
        "score": 100 if not warnings else 45,
        "warnings": warnings,
        "untraceable_fields": untraceable,
        "final_action": "pass" if not warnings else "allow_with_log"
    }
    log_verdict("doc_drafter", verdict)
    return verdict


def critique_resource_output(result: dict, query: str, db: dict) -> dict:
    warnings = []
    known_names = set()
    for group in ("one_stop_centres", "shelter_homes", "legal_aid_offices"):
        for entry in db.get(group, []):
            known_names.add(entry.get("name", ""))

    for item in result.get("resources", []):
        if item.get("name") not in known_names:
            warnings.append(f"Resource not found in DB: {item.get('name', '')}")

    if result.get("needs_location") and result.get("location_found"):
        if not result.get("resources") and "181" not in json.dumps(result.get("helplines", [])):
            warnings.append("Location flow has no resource and no 181 fallback.")

    verdict = {
        "passed": not warnings,
        "score": 100 if not warnings else 50,
        "warnings": warnings,
        "query": query[:120],
        "final_action": "pass" if not warnings else "allow_with_log"
    }
    log_verdict("resource_locator", verdict)
    return verdict


def critique_safety_output(result: dict, retrieved_sources: list[dict] | None = None) -> dict:
    warnings = []
    plan_text = "\n".join(result.get("plan_steps", []))
    cited_sections = re.findall(
        r"\b(?:section|article)\s+\d+[a-zA-Z]?\b",
        plan_text,
        flags=re.IGNORECASE
    )

    if result.get("is_urgent") and result.get("plan_steps"):
        if "181" not in result["plan_steps"][0]:
            warnings.append("Urgent safety plan does not start with 181.")

    if cited_sections:
        if not retrieved_sources:
            warnings.append("Safety plan cites legal sections without session sources.")
        else:
            source_text = " ".join([s.get("source", "").lower() for s in retrieved_sources if isinstance(s, dict)])
            plan_text_lower = plan_text.lower()
            for section in cited_sections:
                if "domestic violence" in plan_text_lower and "domestic violence" not in source_text:
                    warnings.append("Cites Domestic Violence Act section but Domestic Violence Act was not retrieved.")
                if "posh" in plan_text_lower and "posh" not in source_text:
                    warnings.append("Cites POSH Act section but POSH Act was not retrieved.")
                if "dowry" in plan_text_lower and "dowry" not in source_text:
                    warnings.append("Cites Dowry Act section but Dowry Act was not retrieved.")
                if "maternity" in plan_text_lower and "maternity" not in source_text:
                    warnings.append("Cites Maternity Benefit Act section but Maternity Benefit Act was not retrieved.")
                if "equal remuneration" in plan_text_lower and "equal remuneration" not in source_text:
                    warnings.append("Cites Equal Remuneration Act section but Equal Remuneration Act was not retrieved.")

    verdict = {
        "passed": not warnings,
        "score": 100 if not warnings else 55,
        "warnings": warnings,
        "cited_sections": cited_sections,
        "final_action": "pass" if not warnings else "allow_with_log"
    }
    log_verdict("safety_planner", verdict)
    return verdict
