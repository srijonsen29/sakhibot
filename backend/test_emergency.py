"""
Emergency Features Test Suite
Run this to test GPS location, guardian network, and emergency alerts.
"""
import requests
import json
from datetime import datetime

# Base URL - adjust if needed
BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_health():
    """Test API health"""
    print_section("1. Health Check")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200

def test_consent_policies():
    """Test consent management"""
    print_section("2. Consent Policies")
    
    # List all policies
    response = requests.get(f"{BASE_URL}/api/consent/policies")
    policies = response.json()
    print(f"Available consent types: {len(policies['policies'])}")
    for policy in policies['policies']:
        print(f"  - {policy['consent_type']}: {policy['purpose'][:50]}...")
    
    return response.status_code == 200

def test_grant_consents(user_id):
    """Test granting consents"""
    print_section("3. Grant Consents")
    
    # Grant multiple consents
    response = requests.post(
        f"{BASE_URL}/api/consent/grant-bulk",
        json={
            "user_id": user_id,
            "consent_types": [
                "emergency_location",
                "guardian_alerts",
                "analytics"
            ]
        }
    )
    
    result = response.json()
    print(f"Granted {result['total_granted']} consents")
    for consent in result['consents']:
        print(f"  ✓ {consent['consent_type']}")
    
    return response.status_code == 200

def test_add_guardians(user_id):
    """Test adding guardians"""
    print_section("4. Add Guardian Network")
    
    # Quick setup with multiple guardians
    guardians = [
        {
            "name": "Mom",
            "phone": "+919876543210",
            "email": "mom@example.com",
            "relation": "family",
            "priority": 1
        },
        {
            "name": "Best Friend",
            "phone": "+919876543211",
            "email": "friend@example.com",
            "relation": "friend",
            "priority": 2
        },
        {
            "name": "Neighbor",
            "phone": "+919876543212",
            "relation": "neighbor",
            "priority": 3
        }
    ]
    
    response = requests.post(
        f"{BASE_URL}/api/emergency/guardians/quick-setup",
        json={
            "user_id": user_id,
            "guardians": guardians
        }
    )
    
    result = response.json()
    print(f"Added {result['guardians_added']} guardians:")
    for guardian in result['guardians']:
        print(f"  ✓ {guardian['name']} ({guardian['relation']}) - Priority {guardian['priority']}")
    
    return response.status_code == 200

def test_list_guardians(user_id):
    """Test listing guardians"""
    print_section("5. List Guardians")
    
    response = requests.get(f"{BASE_URL}/api/emergency/guardians/{user_id}")
    result = response.json()
    
    print(f"Total guardians: {result['total']}")
    for guardian in result['guardians']:
        verified = "✓ Verified" if guardian['verified'] else "⚠ Not verified"
        print(f"  {guardian['name']} - {guardian['phone']} [{verified}]")
    
    return response.status_code == 200

def test_set_alert_preferences(user_id):
    """Test setting alert channel preferences"""
    print_section("6. Set Alert Preferences")
    
    response = requests.post(
        f"{BASE_URL}/api/emergency/preferences",
        json={
            "user_id": user_id,
            "channels": [
                {"channel_type": "sms", "enabled": True, "priority": 1},
                {"channel_type": "whatsapp", "enabled": True, "priority": 2},
                {"channel_type": "call", "enabled": True, "priority": 3}
            ],
            "auto_alert_on_sos": True,
            "include_location": True
        }
    )
    
    result = response.json()
    print("Alert preferences set:")
    for channel in result['preferences']['channels']:
        status = "✓ Enabled" if channel['enabled'] else "✗ Disabled"
        print(f"  {channel['channel_type']}: {status} (priority {channel['priority']})")
    
    return response.status_code == 200

def test_location_sharing(user_id):
    """Test non-emergency location sharing"""
    print_section("7. Location Sharing (Non-Emergency)")
    
    # Delhi coordinates (near India Gate)
    response = requests.post(
        f"{BASE_URL}/api/emergency/location/share",
        json={
            "user_id": user_id,
            "latitude": 28.6139,
            "longitude": 77.2090,
            "accuracy": 10.0,
            "duration_minutes": 60
        }
    )
    
    result = response.json()
    print(f"Location sharing started")
    print(f"  Share ID: {result['share_id']}")
    print(f"  Share link: {result['share_link']}")
    print(f"  Recipients: {', '.join(result['recipients'])}")
    print(f"  Expires: {result['expires_at']}")
    print(f"  Location: {result['location']['address']}")
    
    return response.status_code == 200, result['share_id']

def test_location_update(share_id):
    """Test updating shared location"""
    print_section("8. Update Shared Location")
    
    # Update to slightly different coordinates
    response = requests.post(
        f"{BASE_URL}/api/emergency/location/update",
        json={
            "share_id": share_id,
            "latitude": 28.6150,
            "longitude": 77.2100,
            "accuracy": 8.0
        }
    )
    
    result = response.json()
    print(f"Location updated:")
    print(f"  New address: {result['location']['address']}")
    print(f"  Timestamp: {result['location']['timestamp']}")
    
    return response.status_code == 200

def test_track_location(share_id):
    """Test tracking shared location (guardian view)"""
    print_section("9. Track Location (Guardian View)")
    
    response = requests.get(f"{BASE_URL}/api/emergency/location/track/{share_id}")
    result = response.json()
    
    print(f"Tracking information:")
    print(f"  Emergency: {'YES' if result['is_emergency'] else 'No'}")
    print(f"  Location: {result['location']['address']}")
    print(f"  Coordinates: {result['location']['latitude']:.4f}, {result['location']['longitude']:.4f}")
    print(f"  Accuracy: {result['location']['accuracy']:.0f}m")
    print(f"  Status: {result['status']}")
    print(f"  Expires: {result['expires_at']}")
    
    return response.status_code == 200

def test_trigger_sos(user_id):
    """Test emergency SOS trigger"""
    print_section("10. 🚨 TRIGGER EMERGENCY SOS")
    
    # Mumbai coordinates (near CST)
    response = requests.post(
        f"{BASE_URL}/api/emergency/sos",
        json={
            "user_id": user_id,
            "latitude": 18.9398,
            "longitude": 72.8355,
            "accuracy": 5.0,
            "message": "URGENT! I need help NOW! Please come immediately!"
        }
    )
    
    result = response.json()
    print(f"🚨 SOS Alert sent!")
    print(f"  Alert ID: {result['alert_id']}")
    print(f"  Guardians notified: {result['guardians_notified']}")
    print(f"  Share link: {result.get('share_link', 'N/A')}")
    
    if result.get('location'):
        loc = result['location']
        print(f"\n📍 Location shared:")
        print(f"  Address: {loc['address']}")
        print(f"  District: {loc['district']}, {loc['state']}")
        print(f"  Nearest police: {loc['nearest_station']}")
    
    print(f"\n📞 Emergency numbers displayed:")
    for number in result['emergency_numbers']:
        print(f"  {number['name']}: {number['number']}")
    
    if result.get('nearby_police'):
        print(f"\n🚓 Nearby police stations:")
        for station in result['nearby_police']:
            print(f"  {station['name']} - {station['distance_km']}km - {station['phone']}")
    
    print(f"\n✉️ Delivery status:")
    for guardian_id, status in result['delivery_status'].items():
        print(f"  {status['guardian_name']}: {status['attempts'][0]['status'] if status['attempts'] else 'pending'}")
    
    return response.status_code == 200, result['alert_id']

def test_alert_status(alert_id):
    """Test checking alert status"""
    print_section("11. Check SOS Alert Status")
    
    response = requests.get(f"{BASE_URL}/api/emergency/sos/status/{alert_id}")
    result = response.json()
    
    print(f"Alert status:")
    print(f"  Alert ID: {result['alert_id']}")
    print(f"  Severity: {result['severity']}")
    print(f"  Sent to: {len(result['sent_to'])} guardians")
    print(f"  Created: {result['created_at']}")
    
    return response.status_code == 200

def test_alert_history(user_id):
    """Test getting alert history"""
    print_section("12. Alert History")
    
    response = requests.get(f"{BASE_URL}/api/emergency/alerts/{user_id}")
    result = response.json()
    
    print(f"Total alerts: {result['total']}")
    for alert in result['alerts']:
        print(f"\n  Alert {alert['alert_id']}:")
        print(f"    Message: {alert['message'][:50]}...")
        print(f"    Severity: {alert['severity']}")
        print(f"    Guardians notified: {alert['guardians_notified']}")
        print(f"    Created: {alert['created_at']}")
    
    return response.status_code == 200

def test_cancel_location_share(share_id):
    """Test canceling location share"""
    print_section("13. Cancel Location Share")
    
    response = requests.post(f"{BASE_URL}/api/emergency/location/cancel/{share_id}")
    result = response.json()
    
    print(f"Location share cancelled: {result['share_id']}")
    
    return response.status_code == 200

def run_all_tests():
    """Run complete test suite"""
    print("\n" + "🔥" * 30)
    print("  SAKHIBOT EMERGENCY FEATURES TEST SUITE")
    print("🔥" * 30)
    
    test_user_id = f"test_user_{int(datetime.now().timestamp())}"
    print(f"\nTest User ID: {test_user_id}")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    results.append(("Consent Policies", test_consent_policies()))
    results.append(("Grant Consents", test_grant_consents(test_user_id)))
    results.append(("Add Guardians", test_add_guardians(test_user_id)))
    results.append(("List Guardians", test_list_guardians(test_user_id)))
    results.append(("Set Preferences", test_set_alert_preferences(test_user_id)))
    
    success, share_id = test_location_sharing(test_user_id)
    results.append(("Location Sharing", success))
    
    if success:
        results.append(("Location Update", test_location_update(share_id)))
        results.append(("Track Location", test_track_location(share_id)))
    
    success, alert_id = test_trigger_sos(test_user_id)
    results.append(("SOS Trigger", success))
    
    if success:
        results.append(("Alert Status", test_alert_status(alert_id)))
    
    results.append(("Alert History", test_alert_history(test_user_id)))
    
    if share_id:
        results.append(("Cancel Share", test_cancel_location_share(share_id)))
    
    # Print summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    if passed == total:
        print("🎉 All tests passed! Emergency features are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

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
