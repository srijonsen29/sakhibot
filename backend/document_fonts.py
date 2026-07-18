import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

LANG_FONT_MAP = {
    "hi": "NotoDevanagari",
    "mr": "NotoDevanagari",
    "bn": "NotoBengali",
    "ta": "NotoTamil",
    "te": "NotoTelugu",
    "gu": "NotoGujarati",
    "kn": "NotoSans",
    "ml": "NotoSans",
    "pa": "NotoSans",
    "en": "NotoSans",
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
            print(f"  [FONTS] Not found: {font_file} — will use Helvetica")


def get_font_for_lang(lang: str) -> str:
    font_name = LANG_FONT_MAP.get(lang, "NotoSans")
    if font_name in _registered:
        return font_name
    return "Helvetica"


register_fonts()