"""Emergency Features Test Suite"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health():
    print_section("1. Health Check")
    r = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    return r.status_code == 200

def test_consent_policies():
    print_section("2. Consent Policies")
    r = requests.get(f"{BASE_URL}/api/consent/policies")
    policies = r.json()
    print(f"Available consent types: {len(policies['policies'])}")
    for p in policies['policies']:
        print(f"  - {p['consent_type']}: {p['purpose'][:50]}...")
    return r.status_code == 200

def test_grant_consents(user_id):
    print_section("3. Grant Consents")
    r = requests.post(f"{BASE_URL}/api/consent/grant-bulk",
        json={"user_id": user_id, "consent_types": ["emergency_location", "guardian_alerts", "analytics"]})
    result = r.json()
    print(f"Granted {result['total_granted']} consents")
    for c in result['consents']:
        print(f"  ✓ {c['consent_type']}")
    return r.status_code == 200

def test_add_guardians(user_id):
    print_section("4. Add Guardian Network")
    guardians = [
        {"name": "Mom", "phone": "+919876543210", "email": "mom@example.com", "relation": "family", "priority": 1},
        {"name": "Best Friend", "phone": "+919876543211", "email": "friend@example.com", "relation": "friend", "priority": 2},
        {"name": "Neighbor", "phone": "+919876543212", "relation": "neighbor", "priority": 3}
    ]
    r = requests.post(f"{BASE_URL}/api/emergency/guardians/quick-setup",
        json={"user_id": user_id, "guardians": guardians})
    result = r.json()
    print(f"Added {result['guardians_added']} guardians:")
    for g in result['guardians']:
        print(f"  ✓ {g['name']} ({g['relation']}) - Priority {g['priority']}")
    return r.status_code == 200

def test_trigger_sos(user_id):
    print_section("5. 🚨 TRIGGER EMERGENCY SOS")
    r = requests.post(f"{BASE_URL}/api/emergency/sos",
        json={"user_id": user_id, "latitude": 18.9398, "longitude": 72.8355, "accuracy": 5.0,
              "message": "URGENT! I need help NOW!"})
    result = r.json()
    print(f"🚨 SOS Alert sent!")
    print(f"  Alert ID: {result['alert_id']}")
    print(f"  Guardians notified: {result['guardians_notified']}")
    if result.get('location'):
        loc = result['location']
        print(f"\n📍 Location: {loc['address']}")
        print(f"  District: {loc['district']}, {loc['state']}")
    print(f"\n✉️ Delivery status:")
    for gid, status in result['delivery_status'].items():
        print(f"  {status['guardian_name']}: {status['attempts'][0]['status'] if status['attempts'] else 'pending'}")
    return r.status_code == 200, result['alert_id']

def run_all_tests():
    print("\n" + "🔥"*30)
    print("  SAKHIBOT EMERGENCY FEATURES TEST")
    print("🔥"*30)
    
    test_user_id = f"test_user_{int(datetime.now().timestamp())}"
    print(f"\nTest User ID: {test_user_id}")
    
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Consent Policies", test_consent_policies()))
    results.append(("Grant Consents", test_grant_consents(test_user_id)))
    results.append(("Add Guardians", test_add_guardians(test_user_id)))
    success, alert_id = test_trigger_sos(test_user_id)
    results.append(("SOS Trigger", success))
    
    print_section("TEST SUMMARY")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed.")

if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API server")
        print("Make sure the server is running:")
        print("  cd backend")
        print("  uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
