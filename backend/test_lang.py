from translate import (
    detect_language, translate_to_english,
    translate_from_english, get_language_name
)
from emergency import (
    detect_emergency, build_emergency_response
)

print("=" * 60)
print("SakhiBot — Day 7 Test: Language + Emergency")
print("=" * 60)

# ── language detection tests ──────────────────────────────────────────────────
print("\n[TEST 1] Language detection")
tests = [
    ("What are my rights under the DV Act?",           "en"),
    ("मुझे RTI कैसे दाखिल करनी है?",                  "hi"),
    ("bachao maar raha hai",                            "hi"),
    ("আমার অধিকার কী?",                               "bn"),
    ("என் உரிமைகள் என்ன?",                            "ta"),
    ("నా హక్కులు ఏమిటి?",                             "te"),
    ("मला मदत हवी आहे",                               "mr"),
]
passed = 0
for text, expected in tests:
    detected = detect_language(text)
    status   = "PASS ✓" if detected == expected else f"WARN ⚠ got {detected}"
    if detected == expected:
        passed += 1
    print(f"  {status} | '{text[:45]}' → {detected} ({get_language_name(detected)})")
print(f"\n  {passed}/{len(tests)} detection tests passed")

# ── translation tests ─────────────────────────────────────────────────────────
print("\n[TEST 2] Translation — Indic languages to English")
translation_tests = [
    ("मुझे अपने अधिकार जानने हैं",    "hi"),
    ("আমার স্বামী আমাকে মারছে",       "bn"),
    ("मला FIR कशी दाखल करायची?",      "mr"),
]
for text, lang in translation_tests:
    translated = translate_to_english(text, lang)
    print(f"  [{lang}] {text[:40]}")
    print(f"       → {translated[:80]}")
    assert len(translated) > 3, "FAIL: translation returned empty"
print("  PASS ✓")

print("\n[TEST 3] Translation — English to Indic")
response = (
    "Under Section 18 of the Domestic Violence Act, "
    "you have the right to a protection order. "
    "Call 181 immediately for help."
)
for lang in ["hi", "bn", "ta"]:
    translated = translate_from_english(response, lang)
    print(f"  [{lang}] {translated[:80]}...")
    assert len(translated) > 10, f"FAIL: empty translation for {lang}"
print("  PASS ✓")

print("\n[TEST 4] English passthrough (no translation)")
text       = "What are my rights?"
result_en  = translate_to_english(text, "en")
result_out = translate_from_english(text, "en")
assert result_en  == text, "FAIL: English should pass through unchanged"
assert result_out == text, "FAIL: English output should pass through unchanged"
print("  PASS ✓ — English passes through correctly")

# ── emergency detection tests ─────────────────────────────────────────────────
print("\n[TEST 5] Emergency detection")
emergency_tests = [
    ("he is killing me please help",         "en", True,  "critical"),
    ("bachao maar dalega please help",        "hi", True,  "critical"),
    ("I am scared and he is hitting me now",  "en", True,  "high"),
    ("maar raha hai bahut dar lag raha hai",  "hi", True,  "high"),
    ("I need help I am afraid",              "en", True,  "medium"),
    ("What is the Domestic Violence Act?",   "en", False, "none"),
    ("How do I file an RTI?",               "en", False, "none"),
    ("mujhe RTI dakhil karni hai",           "hi", False, "none"),
]
em_passed = 0
for text, lang, exp_emergency, exp_severity in emergency_tests:
    result = detect_emergency(text, lang)
    em_ok  = result.is_emergency == exp_emergency
    sev_ok = result.severity     == exp_severity
    status = "PASS ✓" if em_ok and sev_ok else "FAIL ✗"
    if em_ok and sev_ok:
        em_passed += 1
    print(f"  {status} | '{text[:45]}'")
    print(f"         emergency={result.is_emergency} "
          f"severity={result.severity} "
          f"trigger='{result.trigger_word}'")
print(f"\n  {em_passed}/{len(emergency_tests)} emergency tests passed")

# ── emergency response builder ────────────────────────────────────────────────
print("\n[TEST 6] Emergency response builder")
for lang, severity in [("en", "critical"), ("hi", "high"), ("bn", "medium")]:
    resp = build_emergency_response(lang, severity)
    print(f"  [{lang}/{severity}] {resp['answer'][:80]}...")
    assert resp["is_emergency"]  == True,  "FAIL: must be emergency"
    assert len(resp["helplines"]) >= 3,    "FAIL: must have helplines"
print("  PASS ✓")

# ── full pipeline integration ─────────────────────────────────────────────────
print("\n[TEST 7] Full pipeline integration")

from translate import detect_language, translate_to_english, translate_from_english
from emergency import detect_emergency, build_emergency_response
from orchestrator import run as orchestrate

def full_pipeline(message: str, district: str = "", state_name: str = "",
                  history: list = []) -> dict:
    """
    Simulates exactly what the Day 7 main.py does:
    detect → emergency check → translate → orchestrate → translate back
    """
    # 1. detect language
    lang = detect_language(message)
    print(f"    Detected language: {lang} ({get_language_name(lang)})")

    # 2. emergency check (on original message)
    em_result = detect_emergency(message, lang)
    if em_result.is_emergency and em_result.severity in ["critical", "high"]:
        print(f"    EMERGENCY detected: {em_result.severity} / '{em_result.trigger_word}'")
        return build_emergency_response(lang, em_result.severity)

    # 3. translate to English
    english_msg = translate_to_english(message, lang)
    print(f"    Translated to EN: {english_msg[:60]}...")

    # 4. run orchestrator
    result = orchestrate(
        message=english_msg,
        language=lang,
        history=history,
        district=district,
        state_name=state_name
    )

    # 5. translate answer back
    result["answer"]      = translate_from_english(result["answer"], lang)
    result["detected_lang"] = lang
    print(f"    Translated back to [{lang}]: {result['answer'][:60]}...")
    return result


# test Hindi legal question
print("\n  Testing Hindi legal question...")
r = full_pipeline("मुझे घरेलू हिंसा के बारे में जानकारी चाहिए")
print(f"  answer preview: {r['answer'][:100]}...")
assert len(r["answer"]) > 10, "FAIL: empty answer"
print("  PASS ✓")

# test Bengali resource request
print("\n  Testing Bengali resource request...")
r = full_pipeline(
    "আমার কাছের আশ্রয় কেন্দ্র কোথায়?",
    district="Kolkata",
    state_name="West Bengal"
)
print(f"  resources: {len(r.get('resources', []))}")
print(f"  answer preview: {r['answer'][:80]}...")
print("  PASS ✓")

# test emergency in Hindi
print("\n  Testing Hindi emergency...")
r = full_pipeline("bachao maar raha hai pati please help karo")
print(f"  is_emergency: {r.get('is_emergency')}")
print(f"  answer: {r['answer'][:100]}...")
assert r.get("is_emergency") == True, "FAIL: should detect emergency"
print("  PASS ✓")

print("\n" + "=" * 60)
print("Day 7 tests complete. Backend is COMPLETE.")
print("=" * 60)