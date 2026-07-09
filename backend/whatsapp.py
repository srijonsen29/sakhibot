import re
from fastapi import APIRouter, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
from core.translate import detect_language, translate_to_english, translate_from_english
from core.emergency import detect_emergency, build_emergency_response
from orchestrator import run as orchestrate

router = APIRouter()

# ── in-memory session store ───────────────────────────────────────────────────
# stores conversation history per phone number
# in production use Redis — for now dict works fine for demo
_sessions: dict[str, list] = {}

MAX_HISTORY = 10   # keep last 10 messages per session
WA_CHAR_LIMIT = 1600  # WhatsApp message character limit


def _get_history(phone: str) -> list:
    return _sessions.get(phone, [])


def _save_message(phone: str, role: str, content: str):
    if phone not in _sessions:
        _sessions[phone] = []
    _sessions[phone].append({"role": role, "content": content})
    # keep only last N messages to avoid token overflow
    if len(_sessions[phone]) > MAX_HISTORY:
        _sessions[phone] = _sessions[phone][-MAX_HISTORY:]


def _format_for_whatsapp(result: dict, lang: str) -> str:
    """
    Formats the full SakhiBot response into a WhatsApp-friendly message.
    WhatsApp supports *bold* and line breaks.
    Max 1600 chars.
    """
    parts = []

    # main answer
    answer = result.get("answer", "")
    if answer:
        parts.append(answer)

    # sources
    sources = result.get("sources", [])
    if sources:
        unique = list({s["source"] for s in sources})
        parts.append(f"\n📚 *Source:* {', '.join(unique[:2])}")

    # emergency helplines
    if result.get("is_emergency"):
        parts.append(
            "\n🚨 *Emergency helplines:*\n"
            "📞 *181* — Women's Helpline (24x7 free)\n"
            "📞 *100* — Police\n"
            "📞 *112* — National Emergency"
        )

    # resources
    resources = result.get("resources", [])
    if resources:
        parts.append("\n📍 *Nearby resources:*")
        for r in resources[:2]:
            parts.append(
                f"• *{r.get('name', '')}*\n"
                f"  {r.get('address', '')}\n"
                f"  📞 {r.get('phone', '')}"
            )

    # safety plan
    safety_plan = result.get("safety_plan", [])
    if safety_plan:
        parts.append("\n📋 *Your safety plan:*")
        for i, step in enumerate(safety_plan[:4], 1):
            parts.append(f"{i}. {step}")

    # document ready
    if result.get("document_ready"):
        doc_type = result.get("document_type", "")
        labels = {
            "fir_letter":     "Police Complaint Letter",
            "dv_application": "DV Act Application",
            "posh_complaint": "POSH Complaint",
        }
        label = labels.get(doc_type, "Legal Document")
        parts.append(
            f"\n📄 *{label} is ready.*\n"
            f"Please open SakhiBot on your browser to download it:\n"
            f"http://YOUR_DEPLOYED_URL"
        )

    # next question (document collection)
    next_q = result.get("next_question", "")
    if next_q and not result.get("document_ready"):
        parts.append(f"\n❓ {next_q}")

    # footer
    parts.append("\n_SakhiBot — Free legal help for women_")
    parts.append("_Type *HELP* for helplines · *STOP* to clear history_")

    full_msg = "\n".join(parts)

    # truncate if too long
    if len(full_msg) > WA_CHAR_LIMIT:
        full_msg = full_msg[:WA_CHAR_LIMIT - 50] + "\n\n_...Reply to continue_"

    return full_msg


@router.post("/api/whatsapp")
async def whatsapp_webhook(
    Body: str = Form(...),
    From: str = Form(...),
):
    """
    Twilio WhatsApp webhook.
    Receives incoming WhatsApp messages, processes through SakhiBot pipeline,
    returns response as TwiML.
    """
    phone   = From.strip()
    message = Body.strip()
    resp    = MessagingResponse()

    print(f"\n[WHATSAPP] From: {phone} | Message: {message[:60]}")

    # ── special commands ──────────────────────────────────────────────────────
    if message.lower() in ["stop", "clear", "reset", "start over"]:
        _sessions[phone] = []
        resp.message(
            "Your conversation has been cleared. "
            "Send any message to start again. "
            "For emergency help call 181."
        )
        return Response(content=str(resp), media_type="application/xml")

    if message.lower() in ["help", "helpline", "helplines", "181"]:
        resp.message(
            "🆘 *Emergency Helplines India*\n\n"
            "📞 *181* — Women's Helpline (24x7 free)\n"
            "📞 *1091* — Women in Distress (Police)\n"
            "📞 *100* — Police Emergency\n"
            "📞 *112* — National Emergency\n"
            "📞 *7827170170* — NCW Helpline\n\n"
            "_SakhiBot — Free legal help for women_"
        )
        return Response(content=str(resp), media_type="application/xml")

    # ── get session history ───────────────────────────────────────────────────
    history = _get_history(phone)

    # ── detect language ───────────────────────────────────────────────────────
    lang = detect_language(message)
    print(f"[WHATSAPP] Detected language: {lang}")

    # ── emergency check ───────────────────────────────────────────────────────
    em = detect_emergency(message, lang)
    if em.is_emergency and em.severity in ["critical", "high"]:
        print(f"[WHATSAPP] EMERGENCY: {em.severity}")
        sos = (
            "🚨 *You appear to be in danger. Help is available NOW.*\n\n"
            "📞 *Call 181* — Women's Helpline (free, 24x7)\n"
            "📞 *Call 100* — Police Emergency\n"
            "📞 *Call 112* — National Emergency\n\n"
            "You are not alone. Help is one call away. 💙"
        )
        if lang == "hi":
            sos = (
                "🚨 *आप खतरे में हैं। अभी मदद लें।*\n\n"
                "📞 *181* पर कॉल करें — महिला हेल्पलाइन (मुफ्त)\n"
                "📞 *100* पर कॉल करें — पुलिस\n"
                "📞 *112* — राष्ट्रीय आपातकाल\n\n"
                "आप अकेली नहीं हैं। 💙"
            )
        elif lang == "bn":
            sos = (
                "🚨 *আপনি বিপদে আছেন। এখনই সাহায্য নিন।*\n\n"
                "📞 *181* তে কল করুন — মহিলা হেল্পলাইন\n"
                "📞 *100* — পুলিশ\n\n"
                "আপনি একা নন। 💙"
            )
        resp.message(sos)
        _save_message(phone, "user",      message)
        _save_message(phone, "assistant", sos)
        return Response(content=str(resp), media_type="application/xml")

    # ── translate to English ──────────────────────────────────────────────────
    english_msg = translate_to_english(message, lang)
    print(f"[WHATSAPP] Translated: {english_msg[:60]}")

    # ── save user message ─────────────────────────────────────────────────────
    _save_message(phone, "user", message)

    # ── run orchestrator ──────────────────────────────────────────────────────
    try:
        result = orchestrate(
            message=english_msg,
            language=lang,
            history=history,
        )
        print(f"[WHATSAPP] Agents: {result.get('activated_agents', [])}")

    except Exception as e:
        print(f"[WHATSAPP] Orchestrator error: {e}")
        resp.message(
            "I'm having trouble right now. "
            "Please try again or call 181 for immediate help."
        )
        return Response(content=str(resp), media_type="application/xml")

    # ── translate answer back ─────────────────────────────────────────────────
    result["answer"] = translate_from_english(result.get("answer", ""), lang)

    # ── format for WhatsApp ───────────────────────────────────────────────────
    wa_response = _format_for_whatsapp(result, lang)

    # ── save bot response ─────────────────────────────────────────────────────
    _save_message(phone, "assistant", result.get("answer", ""))

    resp.message(wa_response)
    return Response(content=str(resp), media_type="application/xml")