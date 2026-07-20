import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models import EmergencyContact, User
from app.schemas import (
    EmergencyContactOut,
    EmergencyContactsSetupRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserOut,
)
from app.api.security import (
    create_access_token,
    get_current_user,
    get_db,
    hash_password,
    verify_password,
)


router = APIRouter(prefix="/api/auth", tags=["auth"])


# -- helpers -------------------------------------------------------------------

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


def _validate_contacts_payload(contacts: list) -> list:
    """Shared validation for POST and PUT emergency-contacts endpoints.
    Returns a list of (name, phone, relationship) tuples."""
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
    cleaned = []

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
        cleaned.append((name, phone, relationship))

    return cleaned


# -- auth endpoints ------------------------------------------------------------

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

    # create user
    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.flush()  # get user.id before committing

    # save emergency contacts
    for contact in payload.emergency_contacts:
        db.add(EmergencyContact(
            user_id=user.id,
            name=contact.name,
            phone=contact.phone,
            relationship_type=contact.relationship,
        ))

    db.commit()
    db.refresh(user)
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
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


# -- emergency contacts endpoints ----------------------------------------------

@router.post("/emergency-contacts", status_code=status.HTTP_200_OK)
def setup_emergency_contacts(
    payload: EmergencyContactsSetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Set emergency contacts (replaces any existing)."""
    cleaned = _validate_contacts_payload(payload.contacts)

    db.query(EmergencyContact).filter(EmergencyContact.user_id == current_user.id).delete()
    for name, phone, relationship_val in cleaned:
        db.add(EmergencyContact(
            user_id=current_user.id,
            name=name,
            phone=phone,
            relationship_type=relationship_val,
        ))
    db.commit()
    return {"message": "Emergency contacts setup successfully"}


@router.get("/emergency-contacts", response_model=list[EmergencyContactOut])
def get_emergency_contacts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contacts = (
        db.query(EmergencyContact)
        .filter(EmergencyContact.user_id == current_user.id)
        .all()
    )
    return [
        EmergencyContactOut(
            id=c.id,
            name=c.name,
            phone=c.phone,
            relationship=c.relationship_type,
        )
        for c in contacts
    ]


@router.put("/emergency-contacts", status_code=status.HTTP_200_OK)
def update_emergency_contacts(
    payload: EmergencyContactsSetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Idempotent PUT -- replaces all contacts with the new list."""
    cleaned = _validate_contacts_payload(payload.contacts)

    db.query(EmergencyContact).filter(EmergencyContact.user_id == current_user.id).delete()
    for name, phone, relationship_val in cleaned:
        db.add(EmergencyContact(
            user_id=current_user.id,
            name=name,
            phone=phone,
            relationship_type=relationship_val,
        ))
    db.commit()
    return {"message": "Emergency contacts updated successfully"}