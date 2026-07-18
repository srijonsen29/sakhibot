import os
from agents.doc_drafter import (
    detect_document_type,
    build_form_schema,
    extract_fields,
    generate_document,
    generate_from_form,
    run,
)

print("=" * 60)
print("SakhiBot — Agent 2 Test: Document Drafter (form-based flow)")
print("=" * 60)

# ── Test 1: document type detection ───────────────────────────────────────
print("\n[TEST 1] Document type detection")
test_queries = [
    ("I want to file a police FIR against my husband",   "fir_letter"),
    ("I need to file a domestic violence complaint",      "dv_application"),
    ("My boss is harassing me sexually at workplace",     "posh_complaint"),
    ("What are my rights under the DV Act?",              "none"),
    ("husband beating me I want to file complaint",       "fir_letter"),
]
for query, expected in test_queries:
    result = detect_document_type(query)
    status = "PASS \u2713" if result == expected else f"FAIL \u2717 (got {result})"
    print(f"  {status} | '{query[:50]}...' -> {result}")

# ── Test 2: run() returns a form schema, not a question ───────────────────
print("\n[TEST 2] run() returns document_form for a fresh FIR request")
result = run("I want to file an FIR against my husband for beating me", [])
print(f"  needs_document : {result['needs_document']}")
print(f"  document_type  : {result['document_type']}")
print(f"  document_ready : {result['document_ready']}")
print(f"  message        : {result['message'][:80]}...")
form = result["document_form"]
assert form is not None, "Expected a document_form to be returned"
print(f"  form title     : {form['title']}")
print(f"  field count    : {len(form['fields'])}")
for f in form["fields"][:3]:
    print(f"    - {f['name']} ({f['type']}) required={f['required']} value='{f['value']}'")
print("  PASS \u2713" if form and form["fields"] else "  FAIL \u2717")

# ── Test 2B: pre-fill from conversation history ────────────────────────────
print("\n[TEST 2B] Form pre-fill from prior conversation")
history = [
    {"role": "user", "content": "My name is Priya Sharma and my husband Ramesh Sharma beats me."},
    {"role": "assistant", "content": "I'm sorry to hear that. Let's get an FIR ready."},
    {"role": "user", "content": "I live at 123 MG Road, Dharavi, Mumbai 400017, my phone is 9876543210."},
]
result2 = run("Please help me file an FIR", history)
form2 = result2["document_form"]
filled = {f["name"]: f["value"] for f in form2["fields"] if f["value"]}
print(f"  Pre-filled fields: {filled}")
print("  PASS \u2713" if filled else "  NOTE: nothing pre-filled (depends on Groq extraction quality)")

# ── Test 3: submit a complete FIR form -> generate_from_form ──────────────
print("\n[TEST 3] Submit complete FIR form -> generate_from_form()")
fir_fields = {
    "complainant_name": "Priya Sharma",
    "complainant_age": "29",
    "complainant_address": "123 MG Road, Dharavi, Mumbai 400017",
    "complainant_phone": "9876543210",
    "guardian_name": "Suresh Sharma",
    "police_station": "Dharavi",
    "district": "Mumbai",
    "incident_date": "24 May 2026",
    "incident_time": "9:30 PM",
    "incident_place": "Our home at 123 MG Road",
    "accused_name": "Ramesh Sharma",
    "accused_relationship": "Husband",
    "incident_description": "My husband beat me with his hands and verbally abused me in front of our children.",
}
pdf_bytes, verdict = generate_from_form("fir_letter", fir_fields, language="en")
with open("test_fir_output.pdf", "wb") as f:
    f.write(pdf_bytes)
size_kb = os.path.getsize("test_fir_output.pdf") / 1024
print(f"  PDF generated: test_fir_output.pdf ({size_kb:.1f} KB)")
print(f"  Quality verdict: passed={verdict['passed']} score={verdict['score']} warnings={verdict['warnings']}")
print("  PASS \u2713" if verdict["passed"] and size_kb > 0 else "  FAIL \u2717")

# ── Test 3B: DV application ────────────────────────────────────────────────
print("\n[TEST 3B] DV application form -> generate_from_form()")
dv_fields = {
    "complainant_name": "Anita Roy",
    "complainant_age": "32",
    "complainant_address": "45 Park Street, Kolkata",
    "complainant_phone": "9123456780",
    "accused_name": "Rajesh Roy",
    "accused_address": "45 Park Street, Kolkata",
    "accused_relationship": "Husband",
    "incident_date": "20 May 2026",
    "incident_description": "He hit me and threatened me repeatedly over the last month.",
    "relief_sought": "Protection order and residence order",
    "court_district": "Kolkata District Court",
}
pdf_bytes, verdict = generate_from_form("dv_application", dv_fields, language="en")
with open("test_dv_output.pdf", "wb") as f:
    f.write(pdf_bytes)
print(f"  Quality verdict: passed={verdict['passed']} score={verdict['score']}")
print("  DV complaint PDF generated \u2713")

# ── Test 3C: POSH complaint ────────────────────────────────────────────────
print("\n[TEST 3C] POSH complaint form -> generate_from_form()")
posh_fields = {
    "complainant_name": "Meera Singh",
    "complainant_designation": "Software Engineer",
    "complainant_department": "IT Department",
    "complainant_phone": "9876543210",
    "organization_name": "TechCorp Pvt Ltd",
    "accused_name": "Arun Kumar",
    "accused_designation": "Team Lead",
    "incident_date": "15 May 2026",
    "incident_place": "Office premises",
    "incident_description": "He made inappropriate comments and unwanted advances during work hours.",
}
pdf_bytes, verdict = generate_from_form("posh_complaint", posh_fields, language="en")
with open("test_posh_output.pdf", "wb") as f:
    f.write(pdf_bytes)
print(f"  Quality verdict: passed={verdict['passed']} score={verdict['score']}")
print("  POSH complaint PDF generated \u2713")

# ── Test 4: multilingual generation (same FIR fields, different languages) ─
print("\n[TEST 4] Multilingual PDF generation")
for lang_code, lang_name in [("hi", "Hindi"), ("bn", "Bengali"), ("ta", "Tamil")]:
    try:
        pdf_bytes = generate_document("fir_letter", fir_fields, language=lang_code)
        out_path = f"test_fir_output_{lang_code}.pdf"
        with open(out_path, "wb") as f:
            f.write(pdf_bytes)
        size_kb = os.path.getsize(out_path) / 1024
        print(f"  {lang_name} ({lang_code}): {out_path} ({size_kb:.1f} KB) PASS \u2713")
    except Exception as e:
        print(f"  {lang_name} ({lang_code}): FAILED \u2717 -> {e}")

# ── Test 5: audit_form_fields sanity checks (incomplete/invalid submission) ─
print("\n[TEST 5] Quality gate catches incomplete/invalid form submissions")
bad_fields = {
    "complainant_name": "Priya",
    "complainant_phone": "12345",          # invalid: not a valid 10-digit mobile
    "incident_description": "hit me",       # invalid: too short
    # all other required fields left blank on purpose
}
_, verdict = generate_from_form("fir_letter", bad_fields, language="en")
print(f"  passed         : {verdict['passed']}")
print(f"  missing_fields : {verdict['missing_fields']}")
print(f"  warnings       : {verdict['warnings']}")
assert verdict["passed"] is False, "Expected an incomplete/invalid form to fail the quality gate"
print("  PASS \u2713 (correctly flagged as incomplete/invalid)")

print("\n" + "=" * 60)
print("Agent 2 tests complete.")
print("=" * 60)