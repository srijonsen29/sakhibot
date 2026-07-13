from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    has_emergency_contacts: bool = False

    class Config:
        from_attributes = True



class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class EmergencyContactOut(BaseModel):
    id: int
    name: str
    phone: str
    relationship: str

    class Config:
        from_attributes = True


class EmergencyContactCreate(BaseModel):
    name: str
    phone: str
    relationship: str


class EmergencyContactsSetupRequest(BaseModel):
    contacts: list[EmergencyContactCreate]

