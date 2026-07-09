import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

# ── language → font mapping ───────────────────────────────────────────────────
LANG_FONT_MAP = {
    "hi": "NotoDevanagari",    # Hindi
    "mr": "NotoDevanagari",    # Marathi
    "bn": "NotoBengali",       # Bengali
    "ta": "NotoTamil",         # Tamil
    "te": "NotoTelugu",        # Telugu
    "gu": "NotoGujarati",      # Gujarati
    "kn": "NotoSans",          # Kannada — fallback to NotoSans
    "ml": "NotoSans",          # Malayalam — fallback
    "pa": "NotoSans",          # Punjabi — fallback
    "en": "NotoSans",          # English
}

FONT_FILES = {
    "NotoSans":        "NotoSans-Regular.ttf",
    "NotoDevanagari":  "NotoSansDevanagari-Regular.ttf",
    "NotoBengali":     "NotoSansBengali-Regular.ttf",
    "NotoTamil":       "NotoSansTamil-Regular.ttf",
    "NotoTelugu":      "NotoSansTelugu-Regular.ttf",
    "NotoGujarati":    "NotoSansGujarati-Regular.ttf",
}

_registered = set()


def register_fonts():
    """Register all available Noto fonts with ReportLab."""
    for font_name, font_file in FONT_FILES.items():
        if font_name in _registered:
            continue
        path = os.path.join(FONTS_DIR, font_file)
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(font_name, path))
                _registered.add(font_name)
                print(f"  [FONTS] Registered: {font_name}")
            except Exception as e:
                print(f"  [FONTS] Failed to register {font_name}: {e}")
        else:
            # fallback — use Helvetica if font file missing
            print(f"  [FONTS] Not found: {font_file} — will use Helvetica")


def get_font_for_lang(lang: str) -> str:
    """Returns the registered font name for the given language code."""
    font_name = LANG_FONT_MAP.get(lang, "NotoSans")
    if font_name in _registered:
        return font_name
    return "Helvetica"


# register on import
register_fonts()