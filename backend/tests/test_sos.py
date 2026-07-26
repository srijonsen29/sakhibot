import os
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup test DB URL
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["BYPASS_AUTH"] = "true"

from app.database import Base
from app.models import User, EmergencyContact
from app.api.auth import trigger_sos, SOSRequest

class TestSOSAlert(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()

        # Add a test user
        self.user = User(
            id=1,
            name="Jane Doe",
            email="jane@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        self.db.add(self.user)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def test_sos_no_contacts(self):
        from fastapi import HTTPException
        # Should raise 404 since no emergency contacts are saved yet
        with self.assertRaises(HTTPException) as ctx:
            trigger_sos(
                payload=SOSRequest(latitude=12.9716, longitude=77.5946),
                current_user=self.user,
                db=self.db
            )
        self.assertEqual(ctx.exception.status_code, 404)

    def test_sos_with_contacts(self):
        # Add 3 emergency contacts
        contacts = [
            EmergencyContact(user_id=1, name="Alice", phone="+919876543210", relationship_type="Sister"),
            EmergencyContact(user_id=1, name="Bob", phone="+919876543211", relationship_type="Friend"),
            EmergencyContact(user_id=1, name="Charlie", phone="+919876543212", relationship_type="Brother"),
        ]
        self.db.add_all(contacts)
        self.db.commit()

        # Execute SOS alert endpoint
        res = trigger_sos(
            payload=SOSRequest(latitude=12.9716, longitude=77.5946),
            current_user=self.user,
            db=self.db
        )

        self.assertEqual(res["contacts_notified"], 3)
        self.assertEqual(res["total_contacts"], 3)
        self.assertIn("SOS alerts processed successfully", res["message"])

if __name__ == "__main__":
    unittest.main()
