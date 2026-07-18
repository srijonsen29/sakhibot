import os
from fastapi.testclient import TestClient
import pytest

# Ensure BYPASS_AUTH is set appropriately during tests
os.environ["BYPASS_AUTH"] = "false"

from main import app
from security import create_access_token

client = TestClient(app)

def test_auth_endpoints_public():
    # Signup/Login should be accessible without credentials
    res = client.post("/api/auth/login", json={"email": "wrong@example.com", "password": "wrongpassword"})
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]

def test_chat_unauthorized():
    res = client.post("/api/chat", json={"message": "hello"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Missing token"

def test_chat_invalid_token():
    headers = {"Authorization": "Bearer invalid_token"}
    res = client.post("/api/chat", json={"message": "hello"}, headers=headers)
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid token"

def test_bypass_auth():
    # Setup override
    os.environ["BYPASS_AUTH"] = "true"
    # reload modules to pick up config change if needed, or check direct behavior
    import config
    config.BYPASS_AUTH = True
    res = client.post("/api/chat", json={"message": "hello"})
    # It should not return 401 now since auth bypass is enabled
    assert res.status_code != 401
