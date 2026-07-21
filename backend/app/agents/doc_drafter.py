"""
Agent 2 — Police Complaint / Legal Document Drafter
-----------------------------------------------------
Detects which legal document a user needs, collects the required details
as a SINGLE form (not one question at a time), and generates a properly
formatted, multilingual PDF using ReportLab.

Flow:
  1. run(query, history) -> detects doc type, returns a `document_form`
     schema (all fields at once, pre-filled from anything already said
     in the conversation).
  2. Frontend renders that schema as an actual <form>.
  3. On submit, the frontend calls POST /api/document/form directly with
     the filled values -> generate_from_form() -> quality-gated PDF.
"""

import io
import re
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)
from reportlab.lib import colors

from app.core.groq_client import chat as groq_chat
from app.core.translate import translate_from_english
from app.core.quality_gates import audit_form_fields, log_verdict


# ── document type detector ───────────────────────────────────────────────────
def detect_document_type(query: str) -> str:
    """
    Detects which document the user needs.
    Returns: 'fir_letter' | 'dv_application' | 'posh_complaint' | 'none'
    """
    q = query.lower()

    posh_kw = [
        "sexual harassment", "workplace harassment", "posh",
        "icc", "internal complaints", "internal committee",
        "office harassment", "employer harassment", "harassment at work",
        "boss harassment", "boss harassing", "boss is harassing",
        "manager harassing", "supervisor harassment", "colleague harassment",
        "workplace abuse", "harassed at office", "harassed at workplace",
    ]
    dv_kw = [
        "domestic violence", "dv act", "protection order",
        "residence order", "magistrate complaint", "dv complaint",
        "section 12", "shelter order", "husband violence", "court complaint",
    ]
    fir_kw = [
        "fir", "police complaint", "file complaint", "register case",
        "police station", "498a", "beating", "assault", "attack",
        "theft", "harassment", "hurt", "complaint letter",
        "application to police", "file fir", "write complaint", "arrest",
    ]

    for kw in posh_kw:
        if kw in q:
            return "posh_complaint"
    for kw in dv_kw:
        if kw in q:
            if "file" in q or "complaint" in q or "draft" in q or "apply" in q:
                return "dv_application"
            return "none"  # let the Legal Rights agent handle definitions/rights
    for kw in fir_kw:
        if kw in q:
            return "fir_letter"

    if re.search(r"(boss|manager|supervisor).+harass", q):
        return "posh_complaint"

    return "none"


# ── required fields, labels, form field types ─────────────────────────────────
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
        "complainant_name", "complainant_designation", "complainant_department",
        "complainant_phone", "organization_name", "accused_name",
        "accused_designation", "incident_date", "incident_place",
        "incident_description",
    ],
}

# Fields that are useful but not strictly mandatory for the letter to be valid
OPTIONAL_FIELDS = {"accused_address"}

FIELD_LABELS = {
    "complainant_name":        "Full Name",
    "complainant_age":         "Age",
    "complainant_address":     "Current Address",
    "complainant_phone":       "Phone Number",
    "guardian_name":           "Father's / Husband's Name",
    "police_station":          "Nearest Police Station",
    "district":                "District",
    "incident_date":           "Date of Incident",
    "incident_time":           "Time of Incident",
    "incident_place":          "Place of Incident",
    "accused_name":            "Accused's Full Name",
    "accused_relationship":    "Relationship to Accused",
    "accused_address":         "Accused's Address (if known)",
    "incident_description":    "Description of Incident",
    "relief_sought":           "Relief Sought",
    "court_district":          "Court District",
    "complainant_designation": "Your Designation",
    "complainant_department":  "Your Department",
    "organization_name":       "Organisation Name",
    "accused_designation":     "Accused's Designation",
}

FIELD_PLACEHOLDERS = {
    "complainant_name":        "e.g. Priya Sharma",
    "complainant_age":         "e.g. 28",
    "complainant_address":     "House no, street, city, PIN",
    "complainant_phone":       "10-digit mobile number",
    "guardian_name":           "e.g. Ramesh Sharma",
    "police_station":          "e.g. Salt Lake Police Station",
    "district":                "e.g. Kolkata",
    "incident_date":           "",
    "incident_time":           "",
    "incident_place":          "e.g. residence, workplace, public road",
    "accused_name":            "e.g. Rakesh Kumar",
    "accused_relationship":    "e.g. husband, employer, colleague, neighbour",
    "accused_address":         "Leave blank if not known",
    "incident_description":    "Describe what happened, in your own words",
    "relief_sought":           "e.g. protection order, residence order, monetary relief",
    "court_district":          "District where the magistrate court is located",
    "complainant_designation": "e.g. Software Engineer",
    "complainant_department":  "e.g. Engineering",
    "organization_name":       "Company / organisation name",
    "accused_designation":     "e.g. Team Lead",
}

FIELD_TYPES = {
    "complainant_name":        "text",
    "complainant_age":         "number",
    "complainant_address":     "textarea",
    "complainant_phone":       "tel",
    "guardian_name":           "text",
    "police_station":          "text",
    "district":                "text",
    "incident_date":           "date",
    "incident_time":           "time",
    "incident_place":          "text",
    "accused_name":            "text",
    "accused_relationship":    "text",
    "accused_address":         "textarea",
    "incident_description":    "textarea",
    "relief_sought":           "textarea",
    "court_district":          "text",
    "complainant_designation": "text",
    "complainant_department":  "text",
    "organization_name":       "text",
    "accused_designation":     "text",
}

DOC_LABELS = {
    "fir_letter":     "Police Complaint Letter (for FIR registration)",
    "dv_application": "Application under DV Act Section 12 (to Magistrate)",
    "posh_complaint": "Complaint under POSH Act 2013 (to ICC/LCC)",
}


# ── best-effort pre-fill from conversation (does NOT block the form) ─────────
def extract_fields(history: list) -> dict:
    """
    Uses Groq to pre-fill whatever the user has already mentioned in the
    conversation, so the form isn't blank. This is a convenience only —
    the user can edit/correct every field before submitting, so there is
    no hallucination risk carried into the final document (unlike the old
    one-question-at-a-time flow, nothing here is trusted without the user
    reviewing it in the form).
    """
    if not history:
        return {}

    conversation = "\n".join([
        f"{m.get('role','').upper()}: {m.get('content','')}"
        for m in history
        if isinstance(m, dict) and m.get("content")
    ])
    if not conversation.strip():
        return {}

    all_fields = sorted({f for fields in REQUIRED_FIELDS.values() for f in fields})

    prompt = f"""Extract information from this conversation. Return ONLY valid JSON.
Include a field only if it was clearly stated. Do not guess.

Fields to extract:
{', '.join(all_fields)}

Conversation:
{conversation}

Return ONLY a JSON object, no markdown, no explanation."""

    try:
        raw = groq_chat(
            [{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=600
        )
        raw = raw.replace("```json", "").replace("```", "").strip()
        import json
        return json.loads(raw)
    except Exception as e:
        print(f"  [DOC] Pre-fill extraction skipped: {e}")
        return {}


# backwards-compat alias used elsewhere in the codebase
def extract_collected_fields(history: list) -> dict:
    return extract_fields(history)


# ── form schema builder (this is what the frontend renders) ──────────────────
def build_form_schema(doc_type: str, prefilled: dict | None = None) -> dict:
    prefilled = prefilled or {}
    required = REQUIRED_FIELDS.get(doc_type, [])

    fields = [{
        "name":        name,
        "label":       FIELD_LABELS.get(name, name.replace("_", " ").title()),
        "type":        FIELD_TYPES.get(name, "text"),
        "placeholder": FIELD_PLACEHOLDERS.get(name, ""),
        "required":    name not in OPTIONAL_FIELDS,
        "value":       str(prefilled.get(name, "") or ""),
    } for name in required]

    return {
        "doc_type": doc_type,
        "title":    DOC_LABELS.get(doc_type, "Legal Document"),
        "fields":   fields,
    }


# ── translation + font helpers for multilingual PDF output ───────────────────
_translation_cache: dict[tuple[str, str], str] = {}

def T(text: str, lang: str) -> str:
    """
    Translates STATIC template text (headings, legal boilerplate, labels)
    into the target language, with caching so the same heading isn't
    re-translated on every document generated.

    User-typed field VALUES (names, addresses, descriptions) are never
    passed through this — they stay exactly as the user typed them, since
    force-translating a proper noun or a personal account of an incident
    would risk corrupting it.
    """
    if not text or lang == "en":
        return text
    key = (text, lang)
    if key in _translation_cache:
        return _translation_cache[key]
    try:
        translated = translate_from_english(text, lang)
    except Exception as exc:
        print(f"  [DOC-TRANSLATE] failed for '{text[:40]}...': {exc}")
        translated = text
    _translation_cache[key] = translated
    return translated


# Maps language code -> font name expected to already be registered with
# reportlab's pdfmetrics (see backend/document_fonts.py, which registers
# these at server startup — confirmed in the boot log: NotoSans,
# NotoDevanagari, NotoBengali, NotoTamil, NotoTelugu, NotoGujarati).
# NOTE: verify these exact strings match document_fonts.py's registerFont()
# calls — if they differ, update this map. The fallback below prevents a
# crash either way.
_FONT_FOR_LANG = {
    "hi": "NotoDevanagari",
    "mr": "NotoDevanagari",
    "bn": "NotoBengali",
    "ta": "NotoTamil",
    "te": "NotoTelugu",
    "gu": "NotoGujarati",
}

def _resolve_font(lang: str) -> str:
    if lang == "en":
        return "Helvetica"
    return _FONT_FOR_LANG.get(lang, "NotoSans")


# Bold variants. "Helvetica-Bold" is a built-in PDF standard font, so
# English is always safe. For Indic scripts, a "<Font>-Bold" TTF must
# already be registered in document_fonts.py for these names to resolve —
# if it isn't, _resolve_bold_font falls back to the regular weight rather
# than crash on an unregistered font name (matches the original behaviour
# for languages where only the regular weight was ever registered).
_BOLD_FONT_FOR_LANG = {
    "hi": "NotoDevanagari-Bold",
    "mr": "NotoDevanagari-Bold",
    "bn": "NotoBengali-Bold",
    "ta": "NotoTamil-Bold",
    "te": "NotoTelugu-Bold",
    "gu": "NotoGujarati-Bold",
}

def _resolve_bold_font(lang: str) -> str:
    if lang == "en":
        return "Helvetica-Bold"
    return _BOLD_FONT_FOR_LANG.get(lang, _resolve_font(lang))


def _base_doc_styles(lang: str = "en"):
    """Returns reportlab paragraph styles using the font resolved for `lang`."""
    font = _resolve_font(lang)
    bold_font = _resolve_bold_font(lang)
    styles = getSampleStyleSheet()

    heading = ParagraphStyle(
        "DocHeading", parent=styles["Normal"], fontSize=13, fontName=bold_font,
        alignment=TA_CENTER, spaceAfter=3, textColor=colors.HexColor("#1a1a1a"),
    )
    subheading = ParagraphStyle(
        "DocSubheading", parent=styles["Normal"], fontSize=11, fontName=bold_font,
        alignment=TA_CENTER, spaceAfter=10, textColor=colors.HexColor("#333333"),
    )
    body = ParagraphStyle(
        "DocBody", parent=styles["Normal"], fontSize=11, fontName=font,
        leading=14.5, alignment=TA_JUSTIFY, spaceAfter=6,
        textColor=colors.HexColor("#1a1a1a"),
    )
    bold_body = ParagraphStyle("DocBoldBody", parent=body, fontName=bold_font)
    small = ParagraphStyle(
        "DocSmall", parent=styles["Normal"], fontSize=9, fontName=font,
        textColor=colors.HexColor("#666666"), alignment=TA_CENTER, spaceAfter=2,
    )
    label = ParagraphStyle(
        "DocLabel", parent=styles["Normal"], fontSize=10, fontName=bold_font,
        textColor=colors.HexColor("#444444"), spaceAfter=1,
    )
    right = ParagraphStyle("DocRight", parent=body, alignment=TA_RIGHT)

    return {
        "heading": heading, "subheading": subheading, "body": body,
        "bold_body": bold_body, "small": small, "label": label, "right": right,
        "font": font, "bold_font": bold_font,
    }


def _footer_note(lang: str):
    styles = _base_doc_styles(lang)
    return Paragraph(
        T(
            "Generated by SakhiBot — AI Legal Rights Assistant for Women in India. "
            "This letter is a draft. Please read it carefully before submission. "
            "The police are legally required to register your complaint under "
            "Section 154 CrPC (now Section 173 BNSS 2023) and provide you with "
            "a copy free of cost.",
            lang
        ),
        styles["small"]
    )


# ── document generators (each with an English/Helvetica safety-net retry) ────
def generate_fir_complaint_letter(fields: dict, language: str = "en") -> bytes:
    try:
        return _build_fir_letter(fields, language)
    except Exception as exc:
        print(f"  [DOC] FIR generation failed in '{language}' ({exc}); "
              f"falling back to English/Helvetica")
        return _build_fir_letter(fields, "en")


def _build_fir_letter(fields: dict, lang: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.8*cm, leftMargin=1.8*cm,
        topMargin=1.6*cm, bottomMargin=1.6*cm
    )
    s = _base_doc_styles(lang)
    story = []

    story.append(Paragraph(T("COMPLAINT APPLICATION", lang), s["heading"]))
    story.append(Paragraph(
        T("For Registration of First Information Report (FIR)", lang) + "<br/>" +
        T("Under Section 173, Bharatiya Nagarik Suraksha Sanhita (BNSS) 2023", lang),
        s["subheading"]
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 0.18*cm))

    story.append(Paragraph(
        f"{T('From', lang)}:<br/>"
        f"<b>{fields.get('complainant_name', '_________________')}</b><br/>"
        f"{T('D/o or W/o', lang)}: {fields.get('guardian_name', '_________________')}<br/>"
        f"{T('Age', lang)}: {fields.get('complainant_age', '___')}<br/>"
        f"{fields.get('complainant_address', '_________________')}<br/>"
        f"{T('Phone', lang)}: {fields.get('complainant_phone', '_________________')}",
        s["body"]
    ))
    story.append(Spacer(1, 0.25*cm))

    story.append(Paragraph(f"{T('Date', lang)}: {date.today().strftime('%d %B %Y')}", s["body"]))
    story.append(Spacer(1, 0.25*cm))

    story.append(Paragraph(T("To,", lang), s["body"]))
    story.append(Paragraph(
        f"{T('The Station House Officer (SHO)', lang)},<br/>"
        f"{fields.get('police_station', '_____________')} {T('Police Station', lang)},<br/>"
        f"{fields.get('district', '_____________')} {T('District', lang)}",
        s["bold_body"]
    ))
    story.append(Spacer(1, 0.18*cm))

    story.append(Paragraph(
        f"<b>{T('Subject', lang)}:</b> "
        f"{T('Complaint for registration of FIR against', lang)} "
        f"{fields.get('accused_name', T('the accused person', lang))} "
        f"({fields.get('accused_relationship', '')})",
        s["body"]
    ))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd")))
    story.append(Spacer(1, 0.18*cm))

    story.append(Paragraph(T("Respected Sir / Madam,", lang), s["body"]))
    story.append(Spacer(1, 0.12*cm))

    story.append(Paragraph(
        f"{T('I,', lang)} <b>{fields.get('complainant_name', '_______________')}</b>, "
        f"{T('aged', lang)} <b>{fields.get('complainant_age', '___')}</b> "
        f"{T('years, daughter / wife of', lang)} "
        f"<b>{fields.get('guardian_name', '_______________')}</b>, "
        f"{T('residing at', lang)} "
        f"<b>{fields.get('complainant_address', '_______________')}</b>, "
        f"{T('hereby submit this complaint and request you to register a First Information Report (FIR) against the accused person(s) named below.', lang)}",
        s["body"]
    ))
    story.append(Spacer(1, 0.18*cm))

    story.append(Paragraph(T("1. DETAILS OF THE INCIDENT", lang), s["label"]))
    not_specified = T("Not specified", lang)
    incident_data = [
        [T("Date of incident", lang),  fields.get("incident_date",  not_specified)],
        [T("Time of incident", lang),  fields.get("incident_time",  not_specified)],
        [T("Place of incident", lang), fields.get("incident_place", not_specified)],
        [T("Name of accused", lang),   fields.get("accused_name",   not_specified)],
        [T("Relationship", lang),      fields.get("accused_relationship", not_specified)],
    ]
    if fields.get("accused_address"):
        incident_data.append([T("Address of accused", lang), fields["accused_address"]])

    table = Table(incident_data, colWidths=[5*cm, 11*cm])
    table.setStyle(TableStyle([
        ("FONTNAME",       (0, 0), (-1, -1), s["font"]),
        ("FONTNAME",       (0, 0), (0, -1),  s["bold_font"]),
        ("FONTSIZE",       (0, 0), (-1, -1), 10),
        ("TEXTCOLOR",      (0, 0), (0, -1),  colors.HexColor("#444444")),
        ("BACKGROUND",     (0, 0), (-1, 0),  colors.HexColor("#f5f5f5")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f9f9f9"), colors.white]),
        ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.25*cm))

    story.append(Paragraph(T("2. DESCRIPTION OF THE INCIDENT", lang), s["label"]))
    story.append(Paragraph(
        fields.get("incident_description", T("Please insert your description of the incident here.", lang)),
        s["body"]
    ))
    story.append(Spacer(1, 0.25*cm))

    story.append(Paragraph(T("3. LEGAL BASIS", lang), s["label"]))
    story.append(Paragraph(
        T("The above acts constitute offences under the following laws "
          "(applicable sections to be determined by the police officer):", lang),
        s["body"]
    ))
    legal_items = [
        T("Protection of Women from Domestic Violence Act, 2005", lang),
        T("Indian Penal Code / Bharatiya Nyaya Sanhita 2023 — Section 498A "
          "(cruelty by husband or relatives)", lang),
        T("Any other applicable sections as deemed fit by the investigating officer", lang),
    ]
    for item in legal_items:
        story.append(Paragraph(f"• {item}", s["body"]))
    story.append(Spacer(1, 0.25*cm))

    story.append(Paragraph(T("4. PRAYER", lang), s["label"]))
    story.append(Paragraph(T("In light of the above facts, I humbly request you to:", lang), s["body"]))
    prayers = [
        T("Register a First Information Report (FIR) against the above-named accused", lang),
        T("Take necessary legal action and arrest the accused", lang),
        T("Ensure my safety and the safety of my family members", lang),
        T("Provide me with a free copy of the registered FIR as required by law", lang),
    ]
    for i, prayer in enumerate(prayers, 1):
        story.append(Paragraph(f"{i}. {prayer}", s["body"]))
    story.append(Spacer(1, 0.25*cm))

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd")))
    story.append(Spacer(1, 0.12*cm))
    story.append(Paragraph(
        T("I hereby declare that the information provided above is true and "
          "correct to the best of my knowledge and belief. I have not filed any "
          "other complaint in this matter.", lang),
        s["body"]
    ))
    story.append(Spacer(1, 0.35*cm))

    sig_data = [
        [
            Paragraph(T("Yours faithfully,", lang), s["body"]),
            Paragraph(f"{T('Date', lang)}: {date.today().strftime('%d %B %Y')}", s["right"])
        ],
        [
            Paragraph(
                f"<b>{fields.get('complainant_name', '_________________')}</b><br/>"
                f"{fields.get('complainant_address', '')}<br/>"
                f"{T('Phone', lang)}: {fields.get('complainant_phone', '')}",
                s["body"]
            ),
            Paragraph("", s["body"])
        ],
    ]
    sig_table = Table(sig_data, colWidths=[8*cm, 8*cm])
    sig_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 0.25*cm))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 0.12*cm))
    story.append(Paragraph(
        T("IMPORTANT: Under Section 173 of BNSS 2023 (formerly Section 154 CrPC), "
          "the police officer at the station is LEGALLY REQUIRED to register your FIR "
          "and give you a FREE copy. If the police refuse to register your FIR, "
          "you can send this letter by registered post to the Superintendent of Police "
          "or approach the nearest Magistrate directly.", lang),
        ParagraphStyle(
            "ImportantNote", parent=getSampleStyleSheet()["Normal"], fontSize=9,
            fontName=s["font"], textColor=colors.HexColor("#8B0000"),
            alignment=TA_JUSTIFY, spaceAfter=8, leftIndent=8, rightIndent=8,
        )
    ))
    story.append(Spacer(1, 0.12*cm))
    story.append(_footer_note(lang))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_dv_application(fields: dict, language: str = "en") -> bytes:
    try:
        return _build_dv_application(fields, language)
    except Exception as exc:
        print(f"  [DOC] DV application generation failed in '{language}' ({exc}); "
              f"falling back to English/Helvetica")
        return _build_dv_application(fields, "en")


def _build_dv_application(fields: dict, lang: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.8*cm, leftMargin=1.8*cm,
        topMargin=1.6*cm, bottomMargin=1.6*cm
    )
    s = _base_doc_styles(lang)
    story = []

    story.append(Paragraph(T("APPLICATION UNDER SECTION 12", lang), s["heading"]))
    story.append(Paragraph(
        T("Protection of Women from Domestic Violence Act, 2005", lang) + "<br/>" +
        T("Before the Judicial Magistrate / Metropolitan Magistrate", lang),
        s["subheading"]
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 0.25*cm))

    parties_data = [
        [T("Applicant (Aggrieved Person)", lang), T("Respondent", lang)],
        [
            f"{fields.get('complainant_name', '_______________')}\n"
            f"{T('Age', lang)}: {fields.get('complainant_age', '___')}\n"
            f"{fields.get('complainant_address', '_______________')}\n"
            f"{T('Phone', lang)}: {fields.get('complainant_phone', '_______________')}",
            f"{fields.get('accused_name', '_______________')}\n"
            f"{T('Relationship', lang)}: {fields.get('accused_relationship', '___')}\n"
            f"{fields.get('accused_address', T('Address as known', lang))}"
        ]
    ]
    pt = Table(parties_data, colWidths=[8*cm, 8*cm])
    pt.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), s["font"]),
        ("FONTNAME", (0, 0), (-1, 0),  s["bold_font"]),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
    ]))
    story.append(pt)
    story.append(Spacer(1, 0.18*cm))

    story.append(Paragraph(T("PETITION", lang), s["bold_body"]))
    story.append(Paragraph(
        T("The above-named applicant most respectfully submits as follows:", lang),
        s["body"]
    ))
    story.append(Spacer(1, 0.12*cm))

    sections = [
        (T("1. RELATIONSHIP", lang),
         f"{T('The applicant and respondent are in a domestic relationship as', lang)} "
         f"{fields.get('accused_relationship', T('stated', lang))}."),
        (T("2. ACTS OF DOMESTIC VIOLENCE", lang),
         fields.get("incident_description",
             T("The respondent has subjected the applicant to acts of domestic "
               "violence as defined under Section 3 of the DV Act 2005.", lang))),
        (T("3. DATE OF LAST INCIDENT", lang),
         fields.get("incident_date", T("As stated in the application", lang))),
        (T("4. RELIEF SOUGHT", lang),
         fields.get("relief_sought",
             T("Protection Order under Section 18, Residence Order under Section 19, "
               "and Monetary Relief under Section 20 of the DV Act 2005.", lang))),
    ]
    for title, content in sections:
        story.append(Paragraph(title, s["label"]))
        story.append(Paragraph(content, s["body"]))
        story.append(Spacer(1, 0.12*cm))

    story.append(Paragraph(T("PRAYER", lang), s["label"]))
    prayers = [
        T("Pass a Protection Order under Section 18 of the DV Act", lang),
        T("Pass a Residence Order under Section 19 of the DV Act", lang),
        T("Direct payment of Monetary Relief under Section 20", lang),
        T("Pass an interim ex-parte order pending hearing under Section 23", lang),
        T("Any other relief as this Hon'ble Court deems fit and proper", lang),
    ]
    for p in prayers:
        story.append(Paragraph(f"• {p}", s["body"]))
    story.append(Spacer(1, 0.25*cm))

    story.append(Paragraph(
        T("The applicant declares that the contents are true and correct.", lang),
        s["body"]
    ))
    story.append(Spacer(1, 0.35*cm))

    story.append(Paragraph(
        f"{T('Place', lang)}: {fields.get('court_district', '_______________')}<br/>"
        f"{T('Date', lang)}: {date.today().strftime('%d %B %Y')}",
        s["body"]
    ))
    story.append(Spacer(1, 0.25*cm))
    story.append(Paragraph(
        f"{T('Signature of Applicant', lang)}<br/>"
        f"<b>{fields.get('complainant_name', '_______________')}</b>",
        s["body"]
    ))
    story.append(Spacer(1, 0.18*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 0.12*cm))
    story.append(_footer_note(lang))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_posh_complaint(fields: dict, language: str = "en") -> bytes:
    try:
        return _build_posh_complaint(fields, language)
    except Exception as exc:
        print(f"  [DOC] POSH complaint generation failed in '{language}' ({exc}); "
              f"falling back to English/Helvetica")
        return _build_posh_complaint(fields, "en")


def _build_posh_complaint(fields: dict, lang: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.8*cm, leftMargin=1.8*cm,
        topMargin=1.6*cm, bottomMargin=1.6*cm
    )
    s = _base_doc_styles(lang)
    story = []

    story.append(Paragraph(T("COMPLAINT OF SEXUAL HARASSMENT", lang), s["heading"]))
    story.append(Paragraph(
        T("Under Section 9 of the Sexual Harassment of Women at Workplace", lang) + "<br/>" +
        T("(Prevention, Prohibition and Redressal) Act, 2013", lang),
        s["subheading"]
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 0.25*cm))

    story.append(Paragraph(f"{T('Date', lang)}: {date.today().strftime('%d %B %Y')}", s["right"]))
    story.append(Spacer(1, 0.18*cm))

    story.append(Paragraph(T("To,", lang), s["body"]))
    story.append(Paragraph(
        f"{T('The Presiding Officer / Chairperson', lang)},<br/>"
        f"{T('Internal Complaints Committee (ICC)', lang)},<br/>"
        f"<b>{fields.get('organization_name', '_______________')}</b>",
        s["bold_body"]
    ))
    story.append(Spacer(1, 0.25*cm))

    story.append(Paragraph(T("Respected Madam / Sir,", lang), s["body"]))
    story.append(Paragraph(
        f"{T('I,', lang)} <b>{fields.get('complainant_name', '_______________')}</b>, "
        f"{T('working as', lang)} <b>{fields.get('complainant_designation', '_______________')}</b> "
        f"{T('in the', lang)} <b>{fields.get('complainant_department', '_______________')}</b> "
        f"{T('department, hereby file a formal complaint of sexual harassment against', lang)} "
        f"<b>{fields.get('accused_name', '_______________')}</b>, "
        f"{T('designated as', lang)} <b>{fields.get('accused_designation', '_______________')}</b>.",
        s["body"]
    ))
    story.append(Spacer(1, 0.18*cm))

    story.append(Paragraph(T("1. INCIDENT DETAILS", lang), s["label"]))
    not_specified = T("Not specified", lang)
    rows = [
        [T("Date", lang),  fields.get("incident_date",  not_specified)],
        [T("Place", lang), fields.get("incident_place", not_specified)],
        [T("Accused", lang), fields.get("accused_name", not_specified)],
        [T("Designation of accused", lang), fields.get("accused_designation", not_specified)],
    ]
    t = Table(rows, colWidths=[5*cm, 11*cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), s["font"]),
        ("FONTNAME", (0, 0), (0, -1),  s["bold_font"]),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f9f9f9"), colors.white]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.18*cm))

    story.append(Paragraph(T("2. DESCRIPTION OF INCIDENT", lang), s["label"]))
    story.append(Paragraph(
        fields.get("incident_description", T("Please describe the incident in detail.", lang)),
        s["body"]
    ))
    story.append(Spacer(1, 0.18*cm))

    story.append(Paragraph(T("3. RELIEF REQUESTED", lang), s["label"]))
    posh_reliefs = [
        T("Conduct an inquiry into this complaint as per Section 11 of POSH Act", lang),
        T("Take appropriate disciplinary action against the respondent", lang),
        T("Ensure I am not penalised, transferred, or victimised during the inquiry", lang),
        T("Maintain strict confidentiality of this complaint as per Section 16", lang),
    ]
    for r in posh_reliefs:
        story.append(Paragraph(f"• {r}", s["body"]))
    story.append(Spacer(1, 0.25*cm))

    story.append(Paragraph(
        T("I declare that the above information is true and correct. "
          "This complaint is not malicious or frivolous.", lang),
        s["body"]
    ))
    story.append(Spacer(1, 0.18*cm))
    story.append(Paragraph(
        f"{T('Yours faithfully,', lang)}<br/>"
        f"<b>{fields.get('complainant_name', '_______________')}</b><br/>"
        f"{T('Phone', lang)}: {fields.get('complainant_phone', '_______________')}",
        s["body"]
    ))
    story.append(Spacer(1, 0.18*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 0.12*cm))
    story.append(_footer_note(lang))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ── dispatcher ─────────────────────────────────────────────────────────────
def generate_document(doc_type: str, fields: dict, language: str = "en") -> bytes:
    if doc_type == "fir_letter":
        return generate_fir_complaint_letter(fields, language)
    elif doc_type == "dv_application":
        return generate_dv_application(fields, language)
    elif doc_type == "posh_complaint":
        return generate_posh_complaint(fields, language)
    else:
        raise ValueError(f"Unknown document type: {doc_type}")


# backwards-compat name used by the existing /api/document endpoint in main.py
def docx_to_pdf_bytes(doc_type: str, fields: dict, language: str = "en") -> bytes:
    return generate_document(doc_type, fields, language)


# ── quality-gated generation from a submitted FORM (new primary path) ────────
def generate_from_form(doc_type: str, fields: dict, language: str = "en") -> tuple[bytes, dict]:
    """
    Called by POST /api/document/form once the user submits the filled form.

    Unlike the old LLM-extraction flow, these field values were typed
    directly by the user — so there is no hallucination/traceability risk
    to audit. Instead, the quality gate here checks COMPLETENESS and basic
    SANITY (required fields non-empty, phone number looks like a phone
    number, description isn't a one-word stub) and logs the verdict via
    the same quality_gates logging used by the other three agents.
    """
    if doc_type not in DOC_LABELS:
        raise ValueError(f"Unknown document type: {doc_type}")

    required = REQUIRED_FIELDS.get(doc_type, [])
    verdict = audit_form_fields(doc_type, fields, required)

    clean_fields = {k: str(v).strip() for k, v in fields.items() if str(v).strip()}
    pdf_bytes = generate_document(doc_type, clean_fields, language)

    return pdf_bytes, verdict


# ── main agent entry point (called by the LangGraph orchestrator) ────────────
def run(query: str, history: list | None = None) -> dict:
    """
    Full Agent 2 pipeline — now single-shot: as soon as a document type is
    detected, return the complete form schema (pre-filled from history
    where possible) instead of asking one question per turn.

    Returns {
        needs_document: bool,
        document_type:  str,
        document_ready: bool,        # always False here — becomes True only
                                      # after the form is submitted via the
                                      # separate /api/document/form endpoint
        document_form:  dict | None, # the form schema for the frontend
        filename:       str,
        next_question:  str,         # kept empty; retained for schema compat
        message:        str,
    }
    """
    history = history or []
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
            "document_form": None, "filename": "",
            "next_question": "", "message": "",
        }

    prefilled = extract_fields(history) if history else {}
    form = build_form_schema(doc_type, prefilled)
    label = DOC_LABELS.get(doc_type, "legal document")

    filled_count = sum(1 for f in form["fields"] if f["value"])
    prefill_note = (
        f" I've already filled in {filled_count} field(s) from what you told me — "
        f"please check them before submitting."
        if filled_count else ""
    )

    return {
        "needs_document": True,
        "document_type":  doc_type,
        "document_ready": False,
        "document_bytes": None,
        "document_form":  form,
        "filename":       "",
        "next_question":  "",
        "message": (
            f"I can help you prepare a {label}. "
            f"Please fill in the form below with the details.{prefill_note}"
        ),
    }
