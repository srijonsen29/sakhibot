from dataclasses import dataclass

@dataclass
class EmergencyResult:
    is_emergency:   bool
    trigger_word:   str
    severity:       str   # 'critical', 'high', 'medium'
    language:       str


# ── keyword tiers ─────────────────────────────────────────────────────────────
# tier 1 = critical (immediate physical danger)
# tier 2 = high (threats, fear)
# tier 3 = medium (distress signals)

EMERGENCY_KEYWORDS = {
    "en": {
        "critical": [
            "killing me", "will kill me", "going to kill",
            "help me now", "he has a knife", "weapon",
            "please save me", "call police now", "cannot breathe",
            "he is choking", "blood", "dying"
        ],
        "high": [
            "hitting me", "beating me", "in danger",
            "very scared", "he is violent", "being attacked",
            "threatening to kill", "please help me",
            "need help urgently", "emergency", "danger"
        ],
        "medium": [
            "scared", "afraid", "frightened",
            "help me", "what do i do now",
            "i need help", "he hurt me"
        ]
    },
    "hi": {
        "critical": [
            "maar dalega", "jaan se maar", "chaku",
            "bachao bachao", "help karo abhi", "khoon",
            "mar rahi hoon", "chhod do mujhe"
        ],
        "high": [
            "maar raha hai", "peet raha hai", "bahut dar",
            "khatra hai", "please bachao", "madad karo",
            "bahut takleef", "ghar mein maar", "roz maarta"
        ],
        "medium": [
            "dar lag raha", "madad chahiye",
            "kya karoon", "bachao", "help"
        ]
    },
    "bn": {
        "critical": [
            "mere felbe", "khun", "bachao bachao",
            "shomoy nei", "akhon help"
        ],
        "high": [
            "marte ache", "bhoy lagche", "biponno",
            "sahajjo koro", "please help"
        ],
        "medium": [
            "help", "bachao", "bhoy", "koshto"
        ]
    },
    "ta": {
        "critical": [
            "kondruvittaan", "udavi", "inime mudiyathu"
        ],
        "high": [
            "adikkiraan", "bayam", "udavi seyyungal",
            "aapatthu", "help"
        ],
        "medium": [
            "help", "udavi", "bayam"
        ]
    },
    "te": {
        "critical": [
            "champesthunnadu", "blood", "help ippudu"
        ],
        "high": [
            "kottuthunnadu", "bhayam", "help cheseyandi",
            "provaadam", "sahayam"
        ],
        "medium": [
            "help", "sahayam", "bhayam"
        ]
    },
    "mr": {
        "critical": [
            "marun taakto", "waachawa", "khoon"
        ],
        "high": [
            "marto ahe", "bhaiti", "madad kara",
            "please waachawa"
        ],
        "medium": [
            "help", "madad", "bhaiti"
        ]
    },
    "gu": {
        "critical": ["maari nakhe", "khoon", "help karo"],
        "high":     ["maro chhe", "dar lage", "madad karo"],
        "medium":   ["help", "madad", "dar"]
    },
    "kn": {
        "critical": ["kolvanu", "help ippaga"],
        "high":     ["hanitaiddare", "bhaya", "sahaya maadi"],
        "medium":   ["help", "sahaya"]
    },
    "ml": {
        "critical": ["konnan", "rakshikku", "blood"],
        "high":     ["adikkunnu", "bhayam", "sahayikku"],
        "medium":   ["help", "sahayam"]
    }
}

# SOS response cards per language
SOS_MESSAGES = {
    "en": {
        "headline": "You appear to be in danger. Help is available RIGHT NOW.",
        "call_181": "Call 181 — Women's Helpline (free, 24x7)",
        "call_100": "Call 100 — Police Emergency",
        "call_112": "Call 112 — National Emergency",
        "advice":   "If you cannot speak, press and hold the phone button — "
                    "or text 'HELP' to 181. You are not alone."
    },
    "hi": {
        "headline": "आप खतरे में लग रही हैं। अभी मदद उपलब्ध है।",
        "call_181": "181 पर कॉल करें — महिला हेल्पलाइन (मुफ्त, 24x7)",
        "call_100": "100 पर कॉल करें — पुलिस",
        "call_112": "112 पर कॉल करें — राष्ट्रीय आपातकाल",
        "advice":   "अगर बोल नहीं सकतीं तो 181 पर मिस्ड कॉल दें। "
                    "आप अकेली नहीं हैं।"
    },
    "bn": {
        "headline": "আপনি বিপদে আছেন। এখনই সাহায্য পাওয়া যাচ্ছে।",
        "call_181": "181 তে কল করুন — মহিলা হেল্পলাইন",
        "call_100": "100 তে কল করুন — পুলিশ",
        "call_112": "112 — জাতীয় জরুরি নম্বর",
        "advice":   "আপনি একা নন।"
    },
}


def get_sos_message(lang: str) -> dict:
    """Returns SOS message in the user's language, falls back to English."""
    return SOS_MESSAGES.get(lang, SOS_MESSAGES["en"])


def detect_emergency(text: str, lang: str = "en") -> EmergencyResult:
    """
    Detects if the message contains emergency keywords.

    Checks both the detected language keywords AND English keywords
    (in case the user mixes languages).

    Returns EmergencyResult with severity level.
    """
    text_lower = text.lower().strip()

    # check detected language + English
    languages_to_check = list({lang, "en"})

    for check_lang in languages_to_check:
        lang_keywords = EMERGENCY_KEYWORDS.get(check_lang, {})

        # check critical first
        for kw in lang_keywords.get("critical", []):
            if kw in text_lower:
                return EmergencyResult(
                    is_emergency=True,
                    trigger_word=kw,
                    severity="critical",
                    language=check_lang
                )

        # then high
        for kw in lang_keywords.get("high", []):
            if kw in text_lower:
                return EmergencyResult(
                    is_emergency=True,
                    trigger_word=kw,
                    severity="high",
                    language=check_lang
                )

        # then medium
        for kw in lang_keywords.get("medium", []):
            if kw in text_lower:
                return EmergencyResult(
                    is_emergency=True,
                    trigger_word=kw,
                    severity="medium",
                    language=check_lang
                )

    return EmergencyResult(
        is_emergency=False,
        trigger_word="",
        severity="none",
        language=lang
    )


def build_emergency_response(lang: str, severity: str) -> dict:
    """
    Builds the full emergency response object
    to be returned directly to the frontend.
    """
    sos = get_sos_message(lang)

    if severity == "critical":
        answer = (
            f"🚨 {sos['headline']}\n\n"
            f"📞 {sos['call_181']}\n"
            f"📞 {sos['call_100']}\n"
            f"📞 {sos['call_112']}\n\n"
            f"{sos['advice']}"
        )
    elif severity == "high":
        answer = (
            f"🚨 {sos['headline']}\n\n"
            f"📞 {sos['call_181']}\n"
            f"📞 {sos['call_100']}\n\n"
            f"{sos['advice']}"
        )
    else:  # medium
        answer = (
            f"I can hear that you need help. "
            f"Please call 181 (Women's Helpline) right now — "
            f"they are available 24 hours, free of charge.\n\n"
            f"{sos['advice']}"
        )

    return {
        "answer":       answer,
        "is_emergency": True,
        "severity":     severity,
        "helplines": [
            {"name": "Women's Helpline",    "phone": "181",          "type": "helpline"},
            {"name": "Police Emergency",    "phone": "100",          "type": "helpline"},
            {"name": "National Emergency",  "phone": "112",          "type": "helpline"},
            {"name": "NCW Helpline",        "phone": "7827170170",   "type": "helpline"},
        ],
        "sources":       [],
        "resources":     [],
        "safety_plan":   [],
        "document_ready":  False,
        "document_type":   "",
        "next_question":   "",
        "activated_agents": ["emergency"],
        "asking_location":  False,
        "detected_lang":    lang
    }