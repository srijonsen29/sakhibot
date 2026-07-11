import os
import pytest
from fastapi.testclient import TestClient

os.environ["BYPASS_AUTH"] = "false"

from main import app
from database import SessionLocal, Base, engine
from models import User, EmergencyContact
from security import create_access_token

client = TestClient(app)

@pytest.fixture(autouse=True)
def run_around_tests():
    # Re-create tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_emergency_contact_validation():
    # 1. Register test user
    signup_res = client.post("/api/auth/signup", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    })
    assert signup_res.status_code == 201
    
    # Login
    login_res = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get current user profile -> has_emergency_contacts should be False
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.json()["has_emergency_contacts"] is False
    
    # 2. Try setting less than 3 contacts -> Fail
    contacts_payload = {
        "contacts": [
            {"name": "Contact 1", "phone": "1234567890", "relationship": "Friend"},
            {"name": "Contact 2", "phone": "0987654321", "relationship": "Sister"}
        ]
    }
    setup_res = client.post("/api/auth/emergency-contacts", json=contacts_payload, headers=headers)
    assert setup_res.status_code == 400
    assert "Minimum 3" in setup_res.json()["detail"]

    # 3. Try setting duplicates -> Fail
    contacts_payload = {
        "contacts": [
            {"name": "Contact 1", "phone": "1234567890", "relationship": "Friend"},
            {"name": "Contact 2", "phone": "1234567890", "relationship": "Sister"},
            {"name": "Contact 3", "phone": "1111111111", "relationship": "Brother"}
        ]
    }
    setup_res = client.post("/api/auth/emergency-contacts", json=contacts_payload, headers=headers)
    assert setup_res.status_code == 400
    assert "Duplicate" in setup_res.json()["detail"]

    # 4. Try invalid phone number format -> Fail
    contacts_payload = {
        "contacts": [
            {"name": "Contact 1", "phone": "abc", "relationship": "Friend"},
            {"name": "Contact 2", "phone": "0987654321", "relationship": "Sister"},
            {"name": "Contact 3", "phone": "1111111111", "relationship": "Brother"}
        ]
    }
    setup_res = client.post("/api/auth/emergency-contacts", json=contacts_payload, headers=headers)
    assert setup_res.status_code == 400
    assert "Invalid phone number format" in setup_res.json()["detail"]

    # 5. Correct payload -> Success
    contacts_payload = {
        "contacts": [
            {"name": "Contact 1", "phone": "1234567890", "relationship": "Friend"},
            {"name": "Contact 2", "phone": "0987654321", "relationship": "Sister"},
            {"name": "Contact 3", "phone": "1111111111", "relationship": "Brother"}
        ]
    }
    setup_res = client.post("/api/auth/emergency-contacts", json=contacts_payload, headers=headers)
    assert setup_res.status_code == 200
    assert setup_res.json()["message"] == "Emergency contacts setup successfully"
    
    # 6. Verify has_emergency_contacts is now True
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.json()["has_emergency_contacts"] is True
