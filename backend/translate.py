from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from deep_translator import GoogleTranslator
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

# make langdetect deterministic
DetectorFactory.seed = 42

# ── translation timeout guard ──────────────────────────────────────────────
# deep_translator raises a clean RequestError on most connection failures
# (already caught below), but a slow/throttled response from the free
# Google Translate endpoint can HANG instead of raising anything at all —
# with no exception to catch, that would block the whole request until the
# frontend's own fetch gives up. This wraps every translate() call in a
# hard timeout so a hang can never block longer than TRANSLATE_TIMEOUT_SECONDS.
_translate_executor = ThreadPoolExecutor(max_workers=4)
TRANSLATE_TIMEOUT_SECONDS = 5


def _run_with_timeout(fn, *args, timeout=TRANSLATE_TIMEOUT_SECONDS, **kwargs):
    future = _translate_executor.submit(fn, *args, **kwargs)
    try:
        return future.result(timeout=timeout)
    except FutureTimeoutError:
        print(f"  [TRANSLATE] call timed out after {timeout}s — aborting wait")
        return None


# ── supported languages ───────────────────────────────────────────────────────
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "ur": "Urdu",
    "or": "Odia",
}

# language codes where langdetect is unreliable
# for these we use a keyword-based fallback
SCRIPT_HINTS = {
    # Devanagari script words → Hindi or Marathi
    "है":    "hi",
    "हूँ":   "hi",
    "मुझे":  "hi",
    "कैसे":  "hi",
    "क्या":  "hi",
    "पति":   "hi",
    "आपका":  "hi",
    "मेरा":  "hi",
    "bachao": "hi",
    "maar":   "hi",
    # Bengali
    "আমি":   "bn",
    "আমার":  "bn",
    "কী":    "bn",
    "কোথায়": "bn",
    "সাহায্য": "bn",
    # Tamil
    "என்":  "ta",
    "நான்": "ta",
    "இந்த": "ta",
    # Telugu
    "నేను": "te",
    "మీరు": "te",
    "ఏమి":  "te",
}


def detect_language(text: str) -> str:
    """
    Detects the language of the input text.
    Returns a language code like 'en', 'hi', 'bn', etc.
    Falls back to 'en' if detection fails.
    """
    if not text or len(text.strip()) < 3:
        return "en"

    # script hint check first (more reliable for Indic scripts)
    for word, lang in SCRIPT_HINTS.items():
        if word in text:
            return lang

    try:
        detected = detect(text)
        # only return if it's a supported language
        if detected in SUPPORTED_LANGUAGES:
            return detected
        return "en"
    except LangDetectException:
        return "en"


def translate_to_english(text: str, source_lang: str) -> str:
    """
    Translates text from source_lang to English.
    Returns original text if already English, translation fails, or
    the call hangs past TRANSLATE_TIMEOUT_SECONDS.
    """
    if source_lang == "en" or not text.strip():
        return text

    try:
        translator = GoogleTranslator(
            source=source_lang,
            target="en"
        )
        translated = _run_with_timeout(translator.translate, text)
        return translated if translated else text
    except Exception as e:
        print(f"  [TRANSLATE] to_english failed ({source_lang}→en): {e}")
        return text  # fall back to original


def translate_from_english(text: str, target_lang: str) -> str:
    """
    Translates text from English to target_lang.
    Returns original text if target is English, translation fails, or
    any chunk's call hangs past TRANSLATE_TIMEOUT_SECONDS.
    """
    if target_lang == "en" or not text.strip():
        return text

    # don't translate very short responses
    if len(text.strip()) < 5:
        return text

    try:
        # split into chunks of 4500 chars (Google Translate limit is 5000)
        chunks      = _split_text(text, max_chars=4500)
        translated  = []
        translator  = GoogleTranslator(source="en", target=target_lang)

        for chunk in chunks:
            result = _run_with_timeout(translator.translate, chunk)
            translated.append(result if result else chunk)

        return "\n".join(translated)
    except Exception as e:
        print(f"  [TRANSLATE] from_english failed (en→{target_lang}): {e}")
        return text  # fall back to English


def _split_text(text: str, max_chars: int = 4500) -> list[str]:
    """Splits long text into chunks at sentence boundaries."""
    if len(text) <= max_chars:
        return [text]

    chunks   = []
    current  = ""

    for sentence in text.replace("\n", " \n ").split(". "):
        if len(current) + len(sentence) < max_chars:
            current += sentence + ". "
        else:
            if current:
                chunks.append(current.strip())
            current = sentence + ". "

    if current:
        chunks.append(current.strip())

    return chunks if chunks else [text]


def get_language_name(lang_code: str) -> str:
    """Returns the full language name for a code."""
    return SUPPORTED_LANGUAGES.get(lang_code, "English")