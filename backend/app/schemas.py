import re
from typing import Any

from pydantic import BaseModel, field_validator, model_validator


VALID_RELATIONSHIPS = {
    "Mother", "Father", "Sister", "Brother", "Husband", "Friend",
    "Neighbor", "Colleague", "Aunt", "Uncle", "Cousin", "Guardian", "Other",
}


class EmergencyContactCreate(BaseModel):
    name: str
    phone: str
    relationship: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Name must be at least 2 characters")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"\+?\d{7,15}", value):
            raise ValueError("Phone number must contain 7 to 15 digits")
        return value

    @field_validator("relationship")
    @classmethod
    def validate_relationship(cls, value: str) -> str:
        value = value.strip()
        if value not in VALID_RELATIONSHIPS:
            raise ValueError("Please select a valid relationship")
        return value


class EmergencyContactOut(BaseModel):
    id: int
    name: str
    phone: str
    relationship: str

    model_config = {"from_attributes": True}


class EmergencyContactsSetupRequest(BaseModel):
    contacts: list[EmergencyContactCreate]


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    emergency_contacts: list[EmergencyContactCreate] = []


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    has_emergency_contacts: bool = False
    emergency_contacts: list[EmergencyContactOut] = []

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def populate_contacts(cls, data: Any) -> Any:
        # When building from an ORM object, `contacts` is the relationship name
        # and `relationship_type` is the column — map them to schema fields.
        if hasattr(data, "contacts"):
            raw_contacts = data.contacts or []
            ec_list = [
                EmergencyContactOut(
                    id=c.id,
                    name=c.name,
                    phone=c.phone,
                    relationship=c.relationship_type,
                )
                for c in raw_contacts
            ]
            # Return a plain dict so Pydantic can populate the model
            return {
                "id": data.id,
                "name": data.name,
                "email": data.email,
                "is_active": data.is_active,
                "has_emergency_contacts": len(ec_list) >= 3,
                "emergency_contacts": ec_list,
            }
        return data


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

