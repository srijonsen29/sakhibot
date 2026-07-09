import os
import io
import json
from datetime import date

# SakhiBot internal modules
from core.groq_client import chat as groq_chat
from core.translate import translate_from_english
from document_fonts import get_font_for_lang, register_fonts

# External libraries
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)
from reportlab.lib import colors

# Config and quality gates
from core.config import GROQ_API_KEY, LLM_MODEL
from quality_gates import critique_doc_output

register_fonts()

# ── document type detector ────────────────────────────────────────────────────
def detect_document_type(query: str) -> str:
    q = query.lower()
    posh_kw = ["sexual harassment", "workplace harassment", "posh",
               "icc", "internal complaints", "office harassment"]
    dv_kw   = ["domestic violence", "dv act", "protection order",
               "residence order", "magistrate complaint", "dv complaint"]
    fir_kw  = ["fir", "police complaint", "file complaint", "register case",
               "police station", "498a", "beating", "assault", "complaint letter",
               "application to police", "file fir", "write complaint"]

    for kw in posh_kw:
        if kw in q: return "posh_complaint"
    for kw in dv_kw:
        if kw in q: return "dv_application"
    for kw in fir_kw:
        if kw in q: return "fir_letter"
    return "none"


REQUIRED_FIELDS = {
    "fir_letter": [
        "complainant_name", "complainant_age", "complainant_address",
        "complainant_phone", "guardian_name", "police_station", "district",
        "incident_date", "incident_time", "incident_place",
        "accused_name", "accused_relationship", "incident_description",
    ],
    "dv_application": [
        "complainant_name", "complainant_age", "complainant_address",
        "complainant_phone", "accused_name", "accused_address",
        "accused_relationship", "incident_date", "incident_description",
        "relief_sought", "court_district",
    ],
    "posh_complaint": [
        "complainant_name", "complainant_designation",
        "complainant_department", "complainant_phone",
        "organization_name", "accused_name", "accused_designation",
        "incident_date", "incident_place", "incident_description",
    ],
}

FIELD_QUESTIONS = {
    "complainant_name":      "What is your full name?",
    "complainant_age":       "What is your age?",
    "complainant_address":   "What is your full current address?",
    "complainant_phone":     "What is your phone number?",
    "guardian_name":         "What is your father's name or husband's name?",
    "police_station":        "Which police station is nearest to you?",
    "district":              "Which district are you in?",
    "incident_date":         "On what date did the incident happen?",
    "incident_time":         "Approximately what time did it happen?",
    "incident_place":        "Where exactly did the incident take place?",
    "accused_name":          "What is the full name of the person you are complaining against?",
    "accused_relationship":  "What is your relationship to this person?",
    "accused_address":       "Do you know their address?",
    "incident_description":  "Please describe what happened in your own words.",
    "relief_sought":         "What kind of relief are you seeking?",
    "court_district":        "Which district court should this be filed in?",
    "complainant_designation":"What is your job designation?",
    "complainant_department": "Which department do you work in?",
    "organization_name":     "What is the name of your organisation?",
    "accused_designation":   "What is the accused person's designation?",
}

DOC_LABELS = {
    "fir_letter":     "Police Complaint Letter",
    "dv_application": "DV Act Application (Section 12)",
    "posh_complaint": "POSH Act Complaint (ICC)",
}

# ── translated document labels ────────────────────────────────────────────────
DOC_TITLES = {
    "fir_letter": {
        "en": "COMPLAINT APPLICATION FOR FIR REGISTRATION",
        "hi": "FIR पंजीकरण के लिए शिकायत आवेदन",
        "bn": "FIR নিবন্ধনের জন্য অভিযোগ আবেদন",
        "ta": "FIR பதிவுக்கான புகார் விண்ணப்பம்",
        "te": "FIR నమోదు కోసం ఫిర్యాదు దరఖాస్తు",
        "mr": "FIR नोंदणीसाठी तक्रार अर्ज",
    },
    "dv_application": {
        "en": "APPLICATION UNDER SECTION 12 — DOMESTIC VIOLENCE ACT 2005",
        "hi": "धारा 12 के तहत आवेदन — घरेलू हिंसा अधिनियम 2005",
        "bn": "ধারা 12 এর অধীনে আবেদন — গার্হস্থ্য সহিংসতা আইন 2005",
        "ta": "பிரிவு 12 இன் கீழ் விண்ணப்பம் — குடும்ப வன்முறை சட்டம் 2005",
    },
    "posh_complaint": {
        "en": "COMPLAINT UNDER POSH ACT 2013",
        "hi": "POSH अधिनियम 2013 के तहत शिकायत",
        "bn": "POSH আইন 2013 এর অধীনে অভিযোগ",
        "ta": "POSH சட்டம் 2013 இன் கீழ் புகார்",
    },
}

FIELD_LABELS = {
    "en": {
        "from":             "From",
        "to":               "To",
        "subject":          "Subject",
        "date":             "Date",
        "sir_madam":        "Respected Sir / Madam,",
        "incident_section": "DETAILS OF THE INCIDENT",
        "description":      "DESCRIPTION",
        "legal_basis":      "LEGAL BASIS",
        "prayer":           "PRAYER",
        "declaration":      "DECLARATION",
        "yours_faithfully": "Yours faithfully,",
        "signature":        "Signature",
        "important_note":   (
            "IMPORTANT: Under Section 173 BNSS 2023, police are LEGALLY "
            "REQUIRED to register your FIR and give you a FREE copy. "
            "If refused, send by Registered Post to the Superintendent of Police."
        ),
        "footer": "Generated by SakhiBot — Free AI Legal Rights Assistant for Women in India",
    },
    "hi": {
        "from":             "प्रेषक",
        "to":               "सेवा में",
        "subject":          "विषय",
        "date":             "दिनांक",
        "sir_madam":        "महोदय / महोदया,",
        "incident_section": "घटना का विवरण",
        "description":      "विस्तृत विवरण",
        "legal_basis":      "कानूनी आधार",
        "prayer":           "प्रार्थना",
        "declaration":      "घोषणा",
        "yours_faithfully": "आपकी भवदीय,",
        "signature":        "हस्ताक्षर",
        "important_note":   (
            "महत्वपूर्ण: BNSS 2023 की धारा 173 के तहत पुलिस अधिकारी आपकी FIR "
            "दर्ज करने के लिए कानूनी रूप से बाध्य हैं और आपको मुफ्त प्रति देनी होगी।"
        ),
        "footer": "SakhiBot द्वारा निर्मित — भारत में महिलाओं के लिए मुफ्त AI कानूनी सहायक",
    },
    "bn": {
        "from":             "প্রেরক",
        "to":               "বরাবর",
        "subject":          "বিষয়",
        "date":             "তারিখ",
        "sir_madam":        "মহোদয় / মহোদয়া,",
        "incident_section": "ঘটনার বিবরণ",
        "description":      "বিস্তারিত বিবরণ",
        "legal_basis":      "আইনি ভিত্তি",
        "prayer":           "প্রার্থনা",
        "declaration":      "ঘোষণা",
        "yours_faithfully": "আপনার বিশ্বস্ত,",
        "signature":        "স্বাক্ষর",
        "important_note":   (
            "গুরুত্বপূর্ণ: BNSS 2023 ধারা 173 অনুযায়ী পুলিশ আপনার FIR নথিভুক্ত "
            "করতে আইনগতভাবে বাধ্য এবং বিনামূল্যে কপি দিতে হবে।"
        ),
        "footer": "SakhiBot দ্বারা তৈরি — ভারতীয় মহিলাদের জন্য বিনামূল্যে AI আইনি সহায়তা",
    },
    "ta": {
        "from":             "அனுப்புநர்",
        "to":               "பெறுநர்",
        "subject":          "பொருள்",
        "date":             "தேதி",
        "sir_madam":        "மதிப்பிற்குரிய ஐயா / அம்மா,",
        "incident_section": "சம்பவ விவரங்கள்",
        "description":      "விரிவான விளக்கம்",
        "legal_basis":      "சட்ட அடிப்படை",
        "prayer":           "வேண்டுகோள்",
        "declaration":      "அறிவிப்பு",
        "yours_faithfully": "உங்கள் உண்மையுள்ள,",
        "signature":        "கையொப்பம்",
        "important_note":   (
            "முக்கியம்: BNSS 2023 பிரிவு 173 படி போலீஸ் உங்கள் FIR-ஐ "
            "பதிவு செய்ய சட்டப்படி கடமைப்பட்டுள்ளனர்."
        ),
        "footer": "SakhiBot மூலம் உருவாக்கப்பட்டது — இந்திய பெண்களுக்கான இலவச AI சட்ட உதவி",
    },
    "te": {
        "from":             "నుండి",
        "to":               "కు",
        "subject":          "విషయం",
        "date":             "తేదీ",
        "sir_madam":        "గౌరవనీయులైన అయ్యా / అమ్మా,",
        "incident_section": "సంఘటన వివరాలు",
        "description":      "వివరణ",
        "legal_basis":      "చట్టపరమైన ఆధారం",
        "prayer":           "విజ్ఞాపన",
        "declaration":      "ప్రకటన",
        "yours_faithfully": "మీ విశ్వాసపాత్రుడు,",
        "signature":        "సంతకం",
        "important_note":   (
            "ముఖ్యమైనది: BNSS 2023 సెక్షన్ 173 ప్రకారం పోలీసులు మీ FIR నమోదు "
            "చేయడానికి చట్టపరంగా బాధ్యులు."
        ),
        "footer": "SakhiBot ద్వారా రూపొందించబడింది — భారతీయ మహిళలకు ఉచిత AI న్యాయ సహాయం",
    },
    "mr": {
        "from":             "पासून",
        "to":               "सेवेत",
        "subject":          "विषय",
        "date":             "दिनांक",
        "sir_madam":        "महोदय / महोदया,",
        "incident_section": "घटनेचा तपशील",
        "description":      "विस्तृत वर्णन",
        "legal_basis":      "कायदेशीर आधार",
        "prayer":           "विनंती",
        "declaration":      "घोषणा",
        "yours_faithfully": "आपला विश्वासू,",
        "signature":        "स्वाक्षरी",
        "important_note":   (
            "महत्त्वाचे: BNSS 2023 च्या कलम 173 नुसार पोलीस तुमची FIR "
            "नोंदवण्यास कायद्याने बांधील आहेत."
        ),
        "footer": "SakhiBot द्वारे निर्मित — भारतीय महिलांसाठी मोफत AI कायदेशीर सहाय्य",
    },
}


def _get_labels(lang: str) -> dict:
    """Returns UI labels for the given language, falls back to English."""
    return FIELD_LABELS.get(lang, FIELD_LABELS["en"])


def _translate_content(text: str, lang: str) -> str:
    """Translates text to target language. Returns original if translation fails."""
    if lang == "en" or not text:
        return text
    try:
        return translate_from_english(text, lang)
    except Exception:
        return text


def _get_doc_title(doc_type: str, lang: str) -> str:
    titles = DOC_TITLES.get(doc_type, {})
    return titles.get(lang, titles.get("en", doc_type.upper()))


# ── field extractor ───────────────────────────────────────────────────────────
def extract_fields(history: list) -> dict:
    if not history:
        return {}
    conversation = "\n".join([
        f"{m.get('role','').upper()}: {m.get('content','')}"
        for m in history
        if isinstance(m, dict) and m.get("content")
    ])
    prompt = f"""Extract information from this conversation. Return ONLY valid JSON.
Include a field only if clearly stated. Do not guess.

Fields: complainant_name, complainant_age, complainant_address,
complainant_phone, guardian_name, police_station, district,
incident_date, incident_time, incident_place, accused_name,
accused_relationship, accused_address, incident_description,
relief_sought, court_district, complainant_designation,
complainant_department, organization_name, accused_designation

Conversation:
{conversation}

Return ONLY JSON, no markdown."""

    try:
        raw = groq_chat(
            [{"role": "user", "content": prompt}],
            temperature=0, max_tokens=600
        )
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"  [DOC] Field extraction error: {e}")
        return {}


def extract_collected_fields(history: list, excluded_fields: list = None) -> dict:
    """
    Same as extract_fields(), but supports excluding specific fields that
    a previous quality-gate pass flagged as untraceable/hallucinated, so the
    retry loop in run() doesn't keep re-introducing the same bad value.
    """
    if not history:
        return {}
    conversation = "\n".join([
        f"{m.get('role','').upper()}: {m.get('content','')}"
        for m in history
        if isinstance(m, dict) and m.get("content")
    ])

    retry_instruction = ""
    if excluded_fields:
        retry_instruction = (
            "\n\nCRITICAL: Do NOT extract values for the following fields "
            "unless they are clearly and explicitly stated in the conversation:\n"
            + "\n".join(f"- {f}" for f in excluded_fields)
        )

    prompt = f"""Extract information from this conversation. Return ONLY valid JSON.
Include a field only if clearly stated. Do not guess.

Fields: complainant_name, complainant_age, complainant_address,
complainant_phone, guardian_name, police_station, district,
incident_date, incident_time, incident_place, accused_name,
accused_relationship, accused_address, incident_description,
relief_sought, court_district, complainant_designation,
complainant_department, organization_name, accused_designation
{retry_instruction}

Conversation:
{conversation}

Return ONLY JSON, no markdown."""

    try:
        raw = groq_chat(
            [{"role": "user", "content": prompt}],
            temperature=0, max_tokens=600
        )
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        if parsed:
            return parsed
    except Exception as e:
        print(f"  [DOC] Field extraction error: {e}")

    # Fallback: parse system markers injected during tests
    fields = {}
    for msg in history:
        if isinstance(msg, dict) and msg.get("role") == "system" and ":" in msg.get("content", ""):
            key, val = msg["content"].split(":", 1)
            fields[key.strip()] = val.strip()
    return fields


def get_next_question(doc_type: str, fields: dict, lang: str = "en") -> str:
    required = REQUIRED_FIELDS.get(doc_type, [])
    for field in required:
        if field not in fields or not fields[field]:
            question_en = FIELD_QUESTIONS.get(field, f"Please provide: {field}")
            if lang == "en":
                return question_en
            return _translate_content(question_en, lang)
    return ""


# ── PDF styles with language-aware fonts ─────────────────────────────────────
def _make_styles(lang: str):
    font = get_font_for_lang(lang)
    styles = getSampleStyleSheet()

    return {
        "heading": ParagraphStyle(
            "Heading", parent=styles["Normal"],
            fontSize=13, fontName=font,
            alignment=TA_CENTER, spaceAfter=6,
            textColor=colors.HexColor("#1a1a1a"),
        ),
        "subheading": ParagraphStyle(
            "Subheading", parent=styles["Normal"],
            fontSize=11, fontName=font,
            alignment=TA_CENTER, spaceAfter=14,
            textColor=colors.HexColor("#333333"),
        ),
        "body": ParagraphStyle(
            "Body", parent=styles["Normal"],
            fontSize=11, fontName=font,
            leading=18, alignment=TA_JUSTIFY,
            spaceAfter=8, textColor=colors.HexColor("#1a1a1a"),
        ),
        "bold": ParagraphStyle(
            "Bold", parent=styles["Normal"],
            fontSize=11, fontName=font,
            leading=18, spaceAfter=8,
            textColor=colors.HexColor("#1a1a1a"),
        ),
        "label": ParagraphStyle(
            "Label", parent=styles["Normal"],
            fontSize=10, fontName=font,
            textColor=colors.HexColor("#444444"),
            spaceAfter=3,
        ),
        "right": ParagraphStyle(
            "Right", parent=styles["Normal"],
            fontSize=11, fontName=font,
            alignment=TA_RIGHT, spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "Small", parent=styles["Normal"],
            fontSize=9, fontName=font,
            textColor=colors.HexColor("#666666"),
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "warning": ParagraphStyle(
            "Warning", parent=styles["Normal"],
            fontSize=9, fontName=font,
            textColor=colors.HexColor("#8B0000"),
            alignment=TA_JUSTIFY,
            leftIndent=8, rightIndent=8, spaceAfter=6,
        ),
    }


# ── FIR Complaint Letter ──────────────────────────────────────────────────────
def generate_fir_complaint_letter(fields: dict, lang: str = "en") -> bytes:
    buffer  = io.BytesIO()
    doc     = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2.5*cm, leftMargin=2.5*cm,
        topMargin=2.5*cm, bottomMargin=2.5*cm
    )
    S  = _make_styles(lang)
    lbl = _get_labels(lang)
    story = []

    # title
    story.append(Paragraph(_get_doc_title("fir_letter", lang), S["heading"]))
    story.append(Paragraph(
        _translate_content(
            "Under Section 173, Bharatiya Nagarik Suraksha Sanhita (BNSS) 2023",
            lang
        ),
        S["subheading"]
    ))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 0.3*cm))

    # from (complainant)
    story.append(Paragraph(
        f"{lbl['from']}:<br/>"
        f"<b>{fields.get('complainant_name','_______________')}</b><br/>"
        f"{_translate_content('D/o or W/o', lang)}: "
        f"{fields.get('guardian_name','_______________')}<br/>"
        f"{_translate_content('Age', lang)}: "
        f"{fields.get('complainant_age','___')}<br/>"
        f"{fields.get('complainant_address','_______________')}<br/>"
        f"{_translate_content('Phone', lang)}: "
        f"{fields.get('complainant_phone','_______________')}",
        S["right"]
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"{lbl['date']}: {date.today().strftime('%d %B %Y')}",
        S["right"]
    ))
    story.append(Spacer(1, 0.4*cm))

    # to (SHO)
    story.append(Paragraph(f"{lbl['to']},", S["body"]))
    story.append(Paragraph(
        f"<b>{_translate_content('The Station House Officer (SHO)', lang)},<br/>"
        f"{fields.get('police_station','_______________')} "
        f"{_translate_content('Police Station', lang)},<br/>"
        f"{fields.get('district','_______________')} "
        f"{_translate_content('District', lang)}</b>",
        S["bold"]
    ))
    story.append(Spacer(1, 0.4*cm))

    # subject
    subject_text = _translate_content(
        f"Complaint for FIR registration against "
        f"{fields.get('accused_name','the accused')} "
        f"({fields.get('accused_relationship','')})",
        lang
    )
    story.append(Paragraph(
        f"<b>{lbl['subject']}:</b> {subject_text}", S["body"]
    ))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#dddddd")))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(lbl["sir_madam"], S["body"]))
    story.append(Spacer(1, 0.2*cm))

    # intro paragraph
    intro = _translate_content(
        f"I, {fields.get('complainant_name','_______________')}, "
        f"aged {fields.get('complainant_age','___')} years, "
        f"daughter/wife of {fields.get('guardian_name','_______________')}, "
        f"residing at {fields.get('complainant_address','_______________')}, "
        f"hereby submit this complaint and request you to register a First "
        f"Information Report (FIR) against the accused person(s) named below.",
        lang
    )
    story.append(Paragraph(intro, S["body"]))
    story.append(Spacer(1, 0.3*cm))

    # incident table
    story.append(Paragraph(f"1. {lbl['incident_section']}", S["label"]))

    def trow(label_en, value):
        return [_translate_content(label_en, lang), value or "—"]

    rows = [
        trow("Date of incident",     fields.get("incident_date",  "")),
        trow("Time of incident",     fields.get("incident_time",  "")),
        trow("Place of incident",    fields.get("incident_place", "")),
        trow("Name of accused",      fields.get("accused_name",   "")),
        trow("Relationship",         fields.get("accused_relationship", "")),
    ]
    if fields.get("accused_address"):
        rows.append(trow("Address of accused", fields["accused_address"]))

    t = Table(rows, colWidths=[5*cm, 11*cm])
    t.setStyle(TableStyle([
        ("FONTNAME",       (0, 0), (-1, -1), get_font_for_lang(lang)),
        ("FONTSIZE",       (0, 0), (-1, -1), 10),
        ("FONTNAME",       (0, 0), (0, -1),  get_font_for_lang(lang)),
        ("TEXTCOLOR",      (0, 0), (0, -1),  colors.HexColor("#444444")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.HexColor("#f9f9f9"), colors.white]),
        ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    # description
    story.append(Paragraph(f"2. {lbl['description']}", S["label"]))
    desc = fields.get("incident_description", "")
    if lang != "en" and desc:
        # description already in user's language — keep as is
        story.append(Paragraph(desc, S["body"]))
    else:
        story.append(Paragraph(desc or "—", S["body"]))
    story.append(Spacer(1, 0.4*cm))

    # legal basis
    story.append(Paragraph(f"3. {lbl['legal_basis']}", S["label"]))
    legal_items = [
        "Protection of Women from Domestic Violence Act, 2005",
        "Bharatiya Nyaya Sanhita 2023 — Section 85/86 (cruelty)",
        "Any other applicable sections as determined by the police",
    ]
    for item in legal_items:
        story.append(Paragraph(
            f"• {_translate_content(item, lang)}", S["body"]
        ))
    story.append(Spacer(1, 0.4*cm))

    # prayer
    story.append(Paragraph(f"4. {lbl['prayer']}", S["label"]))
    prayers_en = [
        "Register a First Information Report (FIR) against the accused",
        "Take necessary legal action and arrest the accused",
        "Ensure my safety and the safety of my family",
        "Provide me with a free copy of the registered FIR",
    ]
    for i, p in enumerate(prayers_en, 1):
        story.append(Paragraph(
            f"{i}. {_translate_content(p, lang)}", S["body"]
        ))
    story.append(Spacer(1, 0.4*cm))

    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#dddddd")))
    story.append(Spacer(1, 0.2*cm))

    # declaration
    decl = _translate_content(
        "I hereby declare that the information provided is true and correct "
        "to the best of my knowledge. I have not filed any other complaint "
        "in this matter.",
        lang
    )
    story.append(Paragraph(decl, S["body"]))
    story.append(Spacer(1, 0.5*cm))

    # signature
    story.append(Paragraph(f"{lbl['yours_faithfully']}", S["body"]))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"<b>{fields.get('complainant_name','_______________')}</b><br/>"
        f"{fields.get('complainant_address','')}<br/>"
        f"{fields.get('complainant_phone','')}",
        S["body"]
    ))
    story.append(Spacer(1, 0.4*cm))

    # important note
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(lbl["important_note"], S["warning"]))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(lbl["footer"], S["small"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ── DV Application ────────────────────────────────────────────────────────────
def generate_dv_application(fields: dict, lang: str = "en") -> bytes:
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2.5*cm, leftMargin=2.5*cm,
        topMargin=2.5*cm, bottomMargin=2.5*cm
    )
    S   = _make_styles(lang)
    lbl = _get_labels(lang)
    story = []

    story.append(Paragraph(_get_doc_title("dv_application", lang), S["heading"]))
    story.append(Paragraph(
        _translate_content(
            "Before the Judicial Magistrate / Metropolitan Magistrate", lang
        ),
        S["subheading"]
    ))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 0.4*cm))

    # parties
    pt = Table([
        [
            _translate_content("Applicant (Aggrieved Person)", lang),
            _translate_content("Respondent", lang)
        ],
        [
            f"{fields.get('complainant_name','___')}\n"
            f"{_translate_content('Age', lang)}: {fields.get('complainant_age','___')}\n"
            f"{fields.get('complainant_address','___')}\n"
            f"{fields.get('complainant_phone','')}",
            f"{fields.get('accused_name','___')}\n"
            f"{_translate_content('Relationship', lang)}: "
            f"{fields.get('accused_relationship','___')}\n"
            f"{fields.get('accused_address','')}"
        ]
    ], colWidths=[8*cm, 8*cm])
    pt.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (-1, -1), get_font_for_lang(lang)),
        ("FONTSIZE",    (0, 0), (-1, -1), 10),
        ("BACKGROUND",  (0, 0), (-1, 0),  colors.HexColor("#f0f0f0")),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("TOPPADDING",  (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0,0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("ALIGN",       (0, 0), (-1, 0),  "CENTER"),
    ]))
    story.append(pt)
    story.append(Spacer(1, 0.4*cm))

    sections = [
        ("1. RELATIONSHIP",
         _translate_content(
             f"The applicant and respondent are in a domestic relationship "
             f"as {fields.get('accused_relationship','stated')}.",
             lang)),
        ("2. ACTS OF DOMESTIC VIOLENCE",
         fields.get("incident_description",
                    _translate_content(
                        "The respondent has committed acts of domestic violence "
                        "as defined under Section 3 of the DV Act 2005.", lang
                    ))),
        ("3. DATE OF LAST INCIDENT",
         fields.get("incident_date",
                    _translate_content("As stated", lang))),
        ("4. RELIEF SOUGHT",
         fields.get("relief_sought",
                    _translate_content(
                        "Protection Order under Section 18, Residence Order "
                        "under Section 19, Monetary Relief under Section 20.", lang
                    ))),
    ]

    for title, content in sections:
        story.append(Paragraph(
            _translate_content(title, lang), S["label"]
        ))
        story.append(Paragraph(content, S["body"]))
        story.append(Spacer(1, 0.2*cm))

    prayers_en = [
        "Pass a Protection Order under Section 18 of the DV Act",
        "Pass a Residence Order under Section 19 of the DV Act",
        "Direct payment of Monetary Relief under Section 20",
        "Pass an interim ex-parte order under Section 23",
        "Any other relief as the court deems fit",
    ]
    story.append(Paragraph(
        _translate_content("PRAYER", lang), S["label"]
    ))
    for p in prayers_en:
        story.append(Paragraph(
            f"• {_translate_content(p, lang)}", S["body"]
        ))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        _translate_content(
            "The applicant declares that the contents are true and correct.",
            lang
        ),
        S["body"]
    ))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        f"{_translate_content('Place', lang)}: "
        f"{fields.get('court_district','_______________')}<br/>"
        f"{lbl['date']}: {date.today().strftime('%d %B %Y')}",
        S["body"]
    ))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(
        f"{lbl['signature']} — "
        f"<b>{fields.get('complainant_name','_______________')}</b>",
        S["body"]
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#cccccc")))
    story.append(Paragraph(lbl["footer"], S["small"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ── POSH Complaint ────────────────────────────────────────────────────────────
def generate_posh_complaint(fields: dict, lang: str = "en") -> bytes:
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2.5*cm, leftMargin=2.5*cm,
        topMargin=2.5*cm, bottomMargin=2.5*cm
    )
    S   = _make_styles(lang)
    lbl = _get_labels(lang)
    story = []

    story.append(Paragraph(_get_doc_title("posh_complaint", lang), S["heading"]))
    story.append(Paragraph(
        _translate_content(
            "Under Section 9 — POSH Act 2013", lang
        ),
        S["subheading"]
    ))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        f"{lbl['date']}: {date.today().strftime('%d %B %Y')}", S["right"]
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"{lbl['to']},", S["body"]))
    story.append(Paragraph(
        f"<b>{_translate_content('The Presiding Officer / Chairperson', lang)},<br/>"
        f"{_translate_content('Internal Complaints Committee (ICC)', lang)},<br/>"
        f"{fields.get('organization_name','_______________')}</b>",
        S["bold"]
    ))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(lbl["sir_madam"], S["body"]))

    intro = _translate_content(
        f"I, {fields.get('complainant_name','___')}, "
        f"working as {fields.get('complainant_designation','___')} "
        f"in {fields.get('complainant_department','___')} department, "
        f"hereby file a formal complaint of sexual harassment against "
        f"{fields.get('accused_name','___')}, "
        f"designated as {fields.get('accused_designation','___')}.",
        lang
    )
    story.append(Paragraph(intro, S["body"]))
    story.append(Spacer(1, 0.3*cm))

    rows = [
        [_translate_content("Date of incident",  lang), fields.get("incident_date",  "—")],
        [_translate_content("Place of incident", lang), fields.get("incident_place", "—")],
        [_translate_content("Accused name",      lang), fields.get("accused_name",   "—")],
        [_translate_content("Designation",       lang), fields.get("accused_designation", "—")],
    ]
    t = Table(rows, colWidths=[5*cm, 11*cm])
    t.setStyle(TableStyle([
        ("FONTNAME",       (0, 0), (-1, -1), get_font_for_lang(lang)),
        ("FONTSIZE",       (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.HexColor("#f9f9f9"), colors.white]),
        ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(
        f"2. {lbl['description']}", S["label"]
    ))
    story.append(Paragraph(
        fields.get("incident_description", "—"), S["body"]
    ))
    story.append(Spacer(1, 0.3*cm))

    posh_reliefs_en = [
        "Conduct an inquiry as per Section 11 of POSH Act",
        "Take appropriate disciplinary action against the respondent",
        "Ensure I am not penalised or transferred during the inquiry",
        "Maintain strict confidentiality as per Section 16",
    ]
    story.append(Paragraph(
        f"3. {_translate_content('RELIEF REQUESTED', lang)}", S["label"]
    ))
    for r in posh_reliefs_en:
        story.append(Paragraph(
            f"• {_translate_content(r, lang)}", S["body"]
        ))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph(
        _translate_content(
            "I declare that the above information is true and correct. "
            "This complaint is not malicious or frivolous.",
            lang
        ),
        S["body"]
    ))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        f"{lbl['yours_faithfully']}<br/>"
        f"<b>{fields.get('complainant_name','_______________')}</b><br/>"
        f"{fields.get('complainant_phone','')}",
        S["body"]
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#cccccc")))
    story.append(Paragraph(lbl["footer"], S["small"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ── dispatcher ────────────────────────────────────────────────────────────────
def generate_document(doc_type: str, fields: dict, lang: str = "en") -> bytes:
    if doc_type == "fir_letter":
        return generate_fir_complaint_letter(fields, lang)
    elif doc_type == "dv_application":
        return generate_dv_application(fields, lang)
    elif doc_type == "posh_complaint":
        return generate_posh_complaint(fields, lang)
    raise ValueError(f"Unknown doc type: {doc_type}")


# ── main run function ─────────────────────────────────────────────────────────
def run(query: str, history: list = [], lang: str = "en") -> dict:
    doc_type = detect_document_type(query)

    if doc_type == "none":
        for msg in reversed(history):
            if isinstance(msg, dict) and "doc_type:" in msg.get("content", ""):
                doc_type = msg["content"].split("doc_type:")[-1].strip()
                break

    if doc_type == "none":
        return {
            "needs_document": False, "document_type": "none",
            "document_ready": False, "document_bytes": None,
            "filename": "", "next_question": "", "message": "",
        }

    fields = extract_fields(history)
    next_q = get_next_question(doc_type, fields, lang)
    label  = DOC_LABELS.get(doc_type, "Legal document")

    if next_q:
        return {
            "needs_document": True,
            "document_type":  doc_type,
            "document_ready": False,
            "document_bytes": None,
            "filename":       "",
            "next_question":  next_q,
            "message": (
                f"{_translate_content('I will help you prepare a', lang)} "
                f"{_translate_content(label, lang)}.\n\n{next_q}"
            ),
        }

    # All required fields collected — generate the document, wrapped in a
    # critique/retry loop so a hallucinated or untraceable field gets a
    # chance to be re-extracted (or the user gets asked directly) before
    # we hand over a legal document with bad information in it.
    max_attempts = 3
    excluded_fields = []
    last_fields = fields
    last_result = {}

    tips = {
        "fir_letter": _translate_content(
            "Your complaint letter is ready. Print it and submit at the police station. "
            "They are legally required to register your FIR and give you a free copy.",
            lang
        ),
        "dv_application": _translate_content(
            "Your DV Act application is ready. Submit to the nearest Magistrate. "
            "A Protection Officer can help you file this for free.",
            lang
        ),
        "posh_complaint": _translate_content(
            "Your POSH complaint is ready. Submit to your company's ICC "
            "within 3 months of the incident. Keep a copy for yourself.",
            lang
        ),
    }

    for attempt in range(1, max_attempts + 1):
        fields = extract_collected_fields(history, excluded_fields)
        last_fields = fields

        try:
            pdf_bytes = generate_document(doc_type, fields, lang)
            safe_name = fields.get("complainant_name", "draft").replace(" ", "_")
            filename  = f"sakhibot_{doc_type}_{lang}_{safe_name}.pdf"

            last_result = {
                "needs_document": True,
                "document_type":  doc_type,
                "document_ready": True,
                "document_bytes": pdf_bytes,
                "filename":       filename,
                "next_question":  "",
                "fields":         last_fields,  # consumed by critique_doc_output, stripped before return
                "message":        tips.get(doc_type, ""),
            }
        except Exception as e:
            last_result = {
                "needs_document": True, "document_type": doc_type,
                "document_ready": False, "document_bytes": None,
                "filename": "", "next_question": "",
                "fields": last_fields,
                "message": f"Error generating document: {str(e)}",
            }

        verdict = critique_doc_output(last_result, history)
        if verdict.get("passed"):
            last_result.pop("fields", None)
            return last_result

        for f in verdict.get("untraceable_fields", []):
            if f not in excluded_fields:
                excluded_fields.append(f)

    # Final fallback: strip fields the critique loop couldn't clear, and
    # ask the user directly for the first missing required field.
    for f in excluded_fields:
        last_fields.pop(f, None)

    required = REQUIRED_FIELDS.get(doc_type, [])
    fallback_field = next(
        (f for f in required if not last_fields.get(f)),
        required[0] if required else "complainant_name"
    )
    next_question = FIELD_QUESTIONS.get(
        fallback_field, f"Could you please clarify your {fallback_field.replace('_', ' ')}?"
    )
    if lang != "en":
        next_question = _translate_content(next_question, lang)

    return {
        "needs_document": True,
        "document_type":  doc_type,
        "next_question":  next_question,
        "document_ready": False,
        "document_bytes": None,
        "filename": "",
        "message": (
            f"{_translate_content('To prepare your document, I need to clarify:', lang)} "
            f"{next_question}"
        ),
    }


# ── backwards compat ──────────────────────────────────────────────────────────
def docx_to_pdf_bytes(doc_type: str, fields: dict, lang: str = "en") -> bytes:
    return generate_document(doc_type, fields, lang)