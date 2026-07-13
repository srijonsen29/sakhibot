from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models import User
from app.schemas import TokenResponse, UserCreate, UserLogin, UserOut
from app.api.security import (
    create_access_token,
    get_current_user,
    get_db,
    hash_password,
    verify_password,
)


router = APIRouter(prefix="/api/auth", tags=["auth"])


def normalize_email(email: str) -> str:
    return email.lower().strip()


def validate_email(email: str):
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a valid email address",
        )


def validate_password(password: str):
    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters",
        )

    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be 72 bytes or fewer",
        )


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    name = payload.name.strip()
    email = normalize_email(payload.email)
    password = payload.password

    if len(name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name must be at least 2 characters",
        )

    validate_email(email)
    validate_password(password)

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user.has_emergency_contacts = False
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)
    validate_email(email)
    validate_password(payload.password)

    user = db.query(User).filter(User.email == email).first()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(subject=str(user.id))
    user.has_emergency_contacts = len(user.contacts) >= 3
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    current_user.has_emergency_contacts = len(current_user.contacts) >= 3
    return current_user



from app.schemas import EmergencyContactsSetupRequest, EmergencyContactOut
from app.models import EmergencyContact
import re

@router.post("/emergency-contacts", status_code=status.HTTP_200_OK)
def setup_emergency_contacts(
    payload: EmergencyContactsSetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contacts = payload.contacts
    
    # 1. Validate count
    if len(contacts) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum 3 emergency contacts are required",
        )
    if len(contacts) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 emergency contacts allowed",
        )

    # 2. Validate format, duplicates, details
    seen_phones = set()
    cleaned_contacts = []
    
    for idx, c in enumerate(contacts):
        name = c.name.strip()
        phone = c.phone.strip()
        relationship = c.relationship.strip()
        
        if not name or not phone or not relationship:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"All fields are required for contact #{idx + 1}",
            )
            
        # Basic format check: standard mobile number format (e.g. 10 digits or digits with + prefix)
        # Allows optional country code, min 7 digits, max 15 digits
        if not re.match(r"^\+?[0-9]{7,15}$", phone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid phone number format for contact: {name} ({phone})",
            )
            
        if phone in seen_phones:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate phone number detected: {phone}",
            )
        seen_phones.add(phone)
        cleaned_contacts.append((name, phone, relationship))

    # 3. Clear existing contacts and save new ones
    db.query(EmergencyContact).filter(EmergencyContact.user_id == current_user.id).delete()
    
    for name, phone, relationship_val in cleaned_contacts:
        db.add(EmergencyContact(
            user_id=current_user.id,
            name=name,
            phone=phone,
            relationship_type=relationship_val
        ))
        
    db.commit()
    return {"message": "Emergency contacts setup successfully"}


@router.get("/emergency-contacts", response_model=list[EmergencyContactOut])
def get_emergency_contacts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contacts = db.query(EmergencyContact).filter(EmergencyContact.user_id == current_user.id).all()
    # Map model relationship_type to schema relationship
    return [
        EmergencyContactOut(
            id=c.id,
            name=c.name,
            phone=c.phone,
            relationship=c.relationship_type
        )
        for c in contacts
    ]


# PUT /api/auth/emergency-contacts — allows users to update contacts after initial setup
@router.put("/emergency-contacts", status_code=status.HTTP_200_OK)
def update_emergency_contacts(
    payload: EmergencyContactsSetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Identical validation and upsert as POST; exposed as PUT for idempotent updates."""
    contacts = payload.contacts

    if len(contacts) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum 3 emergency contacts are required",
        )
    if len(contacts) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 emergency contacts allowed",
        )

    seen_phones = set()
    cleaned_contacts = []

    for idx, c in enumerate(contacts):
        name = c.name.strip()
        phone = c.phone.strip()
        relationship = c.relationship.strip()

        if not name or not phone or not relationship:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"All fields are required for contact #{idx + 1}",
            )

        if not re.match(r"^\+?[0-9]{7,15}$", phone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid phone number format for contact: {name} ({phone})",
            )

        if phone in seen_phones:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate phone number detected: {phone}",
            )
        seen_phones.add(phone)
        cleaned_contacts.append((name, phone, relationship))

    db.query(EmergencyContact).filter(EmergencyContact.user_id == current_user.id).delete()

    for name, phone, relationship_val in cleaned_contacts:
        db.add(EmergencyContact(
            user_id=current_user.id,
            name=name,
            phone=phone,
            relationship_type=relationship_val,
        ))

    db.commit()
    return {"message": "Emergency contacts updated successfully"}
