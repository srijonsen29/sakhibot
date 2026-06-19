"""
Consent Management API Endpoints
Privacy compliance for data protection laws.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from core.consent import (
    grant_consent, revoke_consent, check_consent,
    get_user_consents, get_active_consents,
    check_feature_consent, get_consent_text,
    bulk_grant_consents, export_consent_history,
    delete_all_user_consents, CONSENT_POLICIES
)


router = APIRouter(prefix="/api/consent", tags=["consent"])


# ── Request Models ───────────────────────────────────────────────────────────

class GrantConsentRequest(BaseModel):
    user_id: str
    consent_type: str
    duration_days: Optional[int] = None
    

class BulkConsentRequest(BaseModel):
    user_id: str
    consent_types: List[str]
    

class RevokeConsentRequest(BaseModel):
    user_id: str
    consent_type: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/policies")
async def list_consent_policies():
    """List all available consent types and their policies"""
    return {
        "policies": [
            {
                "consent_type": p.consent_type,
                "required": p.required,
                "purpose": p.purpose,
                "data_types": p.data_types,
                "legal_basis": p.legal_basis,
                "retention": p.retention_period
            }
            for p in CONSENT_POLICIES.values()
        ]
    }


@router.get("/policy/{consent_type}")
async def get_policy(consent_type: str, language: str = "en"):
    """Get detailed consent policy text for UI display"""
    text = get_consent_text(consent_type, language)
    
    if not text:
        raise HTTPException(
            status_code=404,
            detail=f"Consent type '{consent_type}' not found"
        )
        
    return text


@router.post("/grant")
async def grant_user_consent(req: GrantConsentRequest):
    """Grant consent for a specific data usage"""
    try:
        record = grant_consent(
            req.user_id,
            req.consent_type,
            req.duration_days
        )
        
        return {
            "status": "consent_granted",
            "consent_id": record.consent_id,
            "consent_type": record.consent_type,
            "purpose": record.purpose,
            "granted_at": record.granted_at,
            "expires_at": record.expires_at
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/grant-bulk")
async def grant_bulk(req: BulkConsentRequest):
    """Grant multiple consents at once (onboarding)"""
    records = bulk_grant_consents(req.user_id, req.consent_types)
    
    return {
        "status": "consents_granted",
        "total_granted": len(records),
        "consents": [
            {
                "consent_type": r.consent_type,
                "granted_at": r.granted_at
            }
            for r in records
        ]
    }


@router.post("/revoke")
async def revoke_user_consent(req: RevokeConsentRequest):
    """Revoke a previously granted consent"""
    success = revoke_consent(req.user_id, req.consent_type)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Consent not found or already revoked"
        )
        
    return {
        "status": "consent_revoked",
        "consent_type": req.consent_type
    }


@router.get("/check/{user_id}/{consent_type}")
async def check_user_consent(user_id: str, consent_type: str):
    """Check if user has granted specific consent"""
    granted = check_consent(user_id, consent_type)
    
    return {
        "user_id": user_id,
        "consent_type": consent_type,
        "granted": granted
    }


@router.get("/check-feature/{user_id}/{feature}")
async def check_feature_access(user_id: str, feature: str):
    """Check if user has all required consents for a feature"""
    result = check_feature_consent(user_id, feature)
    
    return {
        "user_id": user_id,
        "feature": feature,
        "allowed": result["allowed"],
        "missing_consents": result["missing_consents"],
        "required_consents": result["required_consents"]
    }


@router.get("/list/{user_id}")
async def list_user_consents(user_id: str, active_only: bool = False):
    """List all consents for a user"""
    if active_only:
        records = get_active_consents(user_id)
    else:
        records = get_user_consents(user_id)
        
    return {
        "user_id": user_id,
        "total": len(records),
        "consents": [
            {
                "consent_id": r.consent_id,
                "consent_type": r.consent_type,
                "granted": r.granted,
                "purpose": r.purpose,
                "data_types": r.data_types,
                "granted_at": r.granted_at,
                "revoked_at": r.revoked_at,
                "expires_at": r.expires_at
            }
            for r in records
        ]
    }


@router.get("/export/{user_id}")
async def export_user_consents(user_id: str):
    """Export user's consent history (data portability)"""
    export = export_consent_history(user_id)
    
    return export


@router.delete("/delete-all/{user_id}")
async def delete_user_consents(user_id: str):
    """Delete all consent records (right to erasure)"""
    count = delete_all_user_consents(user_id)
    
    return {
        "status": "consents_deleted",
        "user_id": user_id,
        "consents_deleted": count
    }
