import quality_gates
from quality_gates import (
    SAFE_LEGAL_FALLBACK,
    critique_doc_output,
    critique_resource_output,
    critique_safety_output,
    run_legal_accuracy_gate,
)


def test_legal_gate_falls_back_on_repeated_unsupported_claims():
    original_audit = quality_gates.audit_legal_answer
    calls = {"count": 0}

    def fake_audit(question, answer, chunks):
        calls["count"] += 1
        return {
            "grounded": False,
            "score": 20,
            "unsupported_claims": ["False claim about instant arrest"],
            "reason": "golden_hallucination",
        }

    quality_gates.audit_legal_answer = fake_audit
    try:
        answer, verdict = run_legal_accuracy_gate(
            question="Can police arrest immediately?",
            chunks=["Section text about procedure."],
            generate=lambda unsupported: "Police will definitely arrest him immediately.",
        )
    finally:
        quality_gates.audit_legal_answer = original_audit

    assert calls["count"] == 3  # Updated to 3 attempts (max 2 retries)
    assert answer == SAFE_LEGAL_FALLBACK
    assert verdict["final_action"] == "safe_fallback"


def test_doc_gate_catches_ready_document_without_history():
    verdict = critique_doc_output(
        {"document_ready": True, "document_type": "fir"},
        []
    )
    assert not verdict["passed"]
    assert verdict["warnings"]


def test_doc_gate_catches_untraceable_fields():
    history = [{"role": "user", "content": "My name is Priya."}]
    result = {
        "document_ready": True,
        "document_type": "fir",
        "fields": {
            "complainant_name": "Priya",
            "accused_name": "Ramesh"  # untraceable/fabricated field
        }
    }
    verdict = critique_doc_output(result, history)
    assert not verdict["passed"]
    assert any("Ramesh" in w or "accused_name" in w for w in verdict["warnings"])


def test_resource_gate_catches_hallucinated_resource():
    result = {
        "needs_location": True,
        "location_found": True,
        "resources": [{"name": "Imaginary Shelter", "type": "shelter"}],
        "helplines": [],
    }
    mock_db = {
        "one_stop_centres": [],
        "shelter_homes": [],
        "legal_aid_offices": []
    }
    verdict = critique_resource_output(result, "find shelter", mock_db)
    assert not verdict["passed"]
    assert any("Imaginary Shelter" in w for w in verdict["warnings"])


def test_resource_gate_strips_hallucinated_resource():
    result = {
        "needs_location": True,
        "location_found": True,
        "resources": [
            {"name": "Real One Stop Centre", "type": "osc"},
            {"name": "Hallucinated Safe Haven", "type": "shelter"}
        ],
        "helplines": []
    }
    mock_db = {
        "one_stop_centres": [{"name": "Real One Stop Centre", "type": "osc"}],
        "shelter_homes": [],
        "legal_aid_offices": []
    }
    verdict = critique_resource_output(result, "find osc", mock_db)
    assert not verdict["passed"]
    assert any("Hallucinated Safe Haven" in w for w in verdict["warnings"])


def test_safety_gate_catches_unretrieved_legal_citation():
    verdict = critique_safety_output(
        {
            "plan_steps": ["Use Section 999 to force immediate arrest."],
            "is_urgent": False,
        },
        retrieved_sources=None,
    )
    assert not verdict["passed"]
    assert verdict["cited_sections"] == ["Section 999"]


def test_safety_gate_catches_unretrieved_act_sections():
    result = {
        "plan_steps": ["Step 1: File complaint under Section 18 of the Domestic Violence Act."],
        "is_urgent": False
    }
    # Legal sources only has POSH, so Domestic Violence citation is invalid/unretrieved
    retrieved = [{"source": "POSH Act 2013"}]
    verdict = critique_safety_output(result, retrieved)
    assert not verdict["passed"]
    assert any("Domestic Violence Act" in w for w in verdict["warnings"])


if __name__ == "__main__":
    tests = [
        test_legal_gate_falls_back_on_repeated_unsupported_claims,
        test_doc_gate_catches_ready_document_without_history,
        test_doc_gate_catches_untraceable_fields,
        test_resource_gate_catches_hallucinated_resource,
        test_resource_gate_strips_hallucinated_resource,
        test_safety_gate_catches_unretrieved_legal_citation,
        test_safety_gate_catches_unretrieved_act_sections,
    ]
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
            print(f"PASS {test.__name__}")
        except Exception as exc:
            print(f"FAIL {test.__name__}: {exc}")
    print(f"Golden quality gate catch-rate: {passed}/{len(tests)}")
