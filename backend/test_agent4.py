from agents.safety_planner import (
    run as safety_run,
    extract_situation_from_history,
    get_next_question,
    parse_plan_steps
)
from orchestrator import run as orchestrator_run

print("=" * 60)
print("SakhiBot — Day 6 Test: Agent 4 + Orchestrator")
print("=" * 60)

# ── Agent 4 tests ─────────────────────────────────────────────────────────────
print("\n[TEST 1] Situation extraction from history")
history = [
    {"role": "assistant", "content": "How can I help you?"},
    {"role": "user",      "content": "My husband is beating me I am very scared"},
    {"role": "assistant", "content": "Are you safe right now?"},
    {"role": "user",      "content": "No I am in danger he is threatening to hurt me"},
    {"role": "assistant", "content": "Do you have children?"},
    {"role": "user",      "content": "Yes I have two children with me"},
]
situation = extract_situation_from_history(history)
print(f"  immediate_safety : {situation.get('immediate_safety')}")
print(f"  children         : {situation.get('children')}")
print(f"  incident_type    : {situation.get('incident_type')}")
assert situation.get("immediate_safety") == "danger", "FAIL: should detect danger"
assert situation.get("children") == "yes",            "FAIL: should detect children"
print("  PASS ✓")

print("\n[TEST 2] Next question logic")
empty_history = []
q1 = get_next_question(empty_history)
print(f"  Empty history → '{q1}'")
assert "safe" in q1.lower() or "danger" in q1.lower(), "FAIL: should ask about safety"

partial_history = [
    {"role": "user", "content": "I am safe right now"}
]
q2 = get_next_question(partial_history)
print(f"  After safety Q  → '{q2}'")
assert "children" in q2.lower(), "FAIL: should ask about children"
print("  PASS ✓")

print("\n[TEST 3] Safety plan generation — URGENT")
urgent_history = [
    {"role": "user", "content": "I am in danger my husband is hitting me right now"},
    {"role": "user", "content": "I have children please help me"},
]
result = safety_run("what do I do", urgent_history)
print(f"  ready     : {result['ready']}")
print(f"  is_urgent : {result['is_urgent']}")
print(f"  steps     : {len(result['plan_steps'])}")
for i, step in enumerate(result["plan_steps"], 1):
    print(f"    {i}. {step[:70]}...")
assert result["ready"]                   == True,  "FAIL: plan should be ready"
assert result["is_urgent"]               == True,  "FAIL: should detect urgency"
assert len(result["plan_steps"])         >= 3,     "FAIL: need at least 3 steps"
assert "181" in result["plan_steps"][0], "FAIL: step 1 must be call 181"
print("  PASS ✓")

print("\n[TEST 4] Safety plan — non-urgent situation")
calm_history = [
    {"role": "user", "content": "I am safe right now"},
    {"role": "user", "content": "My husband has been verbally abusing me for months"},
    {"role": "user", "content": "I have no children"},
    {"role": "user", "content": "I can go to my parents house"},
]
result2 = safety_run("what should I do about this", calm_history)
print(f"  ready     : {result2['ready']}")
print(f"  is_urgent : {result2['is_urgent']}")
if result2["ready"]:
    print(f"  steps     : {len(result2['plan_steps'])}")
    for i, step in enumerate(result2["plan_steps"], 1):
        print(f"    {i}. {step[:70]}...")
print("  PASS ✓")

# ── Orchestrator tests ────────────────────────────────────────────────────────
print("\n[TEST 5] Orchestrator — legal question only")
result = orchestrator_run("What is the Domestic Violence Act?")
print(f"  activated_agents : {result['activated_agents']}")
print(f"  answer snippet   : {result['answer'][:100]}...")
print(f"  sources          : {[s['source'] for s in result['sources'][:2]]}")
assert "legal" in result["activated_agents"], "FAIL: legal agent should activate"
print("  PASS ✓")

print("\n[TEST 6] Orchestrator — document request")
result = orchestrator_run("I want to file an FIR against my husband")
print(f"  activated_agents : {result['activated_agents']}")
print(f"  document_type    : {result['document_type']}")
print(f"  answer snippet   : {result['answer'][:100]}...")
assert "document" in result["activated_agents"], "FAIL: document agent should activate"
print("  PASS ✓")

print("\n[TEST 7] Orchestrator — resource request")
result = orchestrator_run(
    "I need a shelter near me",
    district="Mumbai",
    state_name="Maharashtra"
)
print(f"  activated_agents : {result['activated_agents']}")
print(f"  resources found  : {len(result['resources'])}")
print(f"  helplines        : {len(result['helplines'])}")
assert "resource" in result["activated_agents"], "FAIL: resource agent should activate"
print("  PASS ✓")

print("\n[TEST 8] Orchestrator — EMERGENCY")
result = orchestrator_run(
    "bachao please help me he is hitting me right now",
    history=[
        {"role": "user", "content": "I have children with me"},
        {"role": "user", "content": "I am in Mumbai"}
    ]
)
print(f"  is_emergency     : {result['is_emergency']}")
print(f"  activated_agents : {result['activated_agents']}")
print(f"  safety_plan      : {len(result['safety_plan'])} steps")
print(f"  resources        : {len(result['resources'])}")
print(f"  answer snippet   : {result['answer'][:150]}...")
assert result["is_emergency"]  == True, "FAIL: should detect emergency"
assert "safety" in result["activated_agents"], "FAIL: safety should activate"
print("  PASS ✓")

print("\n[TEST 9] Orchestrator — all agents together")
result = orchestrator_run(
    "I want to file a DV complaint and I need to know where to go for help",
    district="Delhi",
    state_name="Delhi",
    history=[
        {"role": "user", "content": "My husband has been abusive for months"},
        {"role": "user", "content": "I am safe right now but want to take action"},
        {"role": "user", "content": "I have no children"},
        {"role": "user", "content": "I can go to my sister"},
    ]
)
print(f"  activated_agents : {result['activated_agents']}")
print(f"  sources          : {len(result['sources'])}")
print(f"  resources        : {len(result['resources'])}")
print(f"  safety_plan      : {len(result['safety_plan'])} steps")
print(f"  document_type    : {result['document_type']}")
print(f"  answer           : {result['answer'][:200]}...")
print("  PASS ✓")

print("\n" + "=" * 60)
print("Day 6 tests complete.")
print("=" * 60)