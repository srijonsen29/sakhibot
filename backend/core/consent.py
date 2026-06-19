"""
User Consent Management for Privacy Compliance
Implements GDPR-style consent management for Indian data protection laws.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json


@dataclass
class ConsentRecord:
    """User consent record for specific data usage"""
    consent_id: str
    user_id: str
    consent_type: str       # e.g., 'emergency_location', 'guardian_alerts'
    granted: bool
    purpose: str            # clear explanation of what data is used for
    data_types: List[str]   # e.g., ['gps_location', 'phone_number']
    granted_at: Optional[str] = None
    revoked_at: Optional[str] = None
    expires_at: Optional[str] = None
    

@dataclass
class ConsentPolicy:
    """Defines consent requirements for a feature"""
    consent_type: str
    required: bool          # feature doesn't work without this
    purpose: str
    data_types: List[str]
    legal_basis: str        # IT Act 2000, DPDP Act 2023, etc.
    retention_period: str   # how long data is kept
    

# ── Consent Types ────────────────────────────────────────────────────────────

CONSENT_POLICIES = {
    "emergency_location": ConsentPolicy(
        consent_type="emergency_location",
        required=False,  # implied during SOS, but user can pre-consent
        purpose="Share your GPS location with emergency services and guardians during SOS",
        data_types=["gps_latitude", "gps_longitude", "address"],
        legal_basis="IT Act 2000 Section 43A - Sensitive Personal Data with consent",
        retention_period="Location shared during emergency only, not stored after incident resolved"
    ),
    
    "guardian_alerts": ConsentPolicy(
        consent_type="guardian_alerts",
        required=True,  # explicit opt-in
        purpose="Send emergency alerts to your trusted contacts via SMS/WhatsApp/Call",
        data_types=["phone_number", "name", "emergency_status"],
        legal_basis="DPDP Act 2023 - Explicit consent for processing",
        retention_period="Guardian list stored until you remove them"
    ),
    
    "police_sharing": ConsentPolicy(
        consent_type="police_sharing",
        required=True,  # explicit consent + verification
        purpose="Automatically notify police with your location during critical emergencies",
        data_types=["gps_location", "phone_number", "incident_details"],
        legal_basis="IT Act 2000 + State Police Integration Acts",
        retention_period="Incident data shared with police per legal requirements"
    ),
    
    "evidence_recording": ConsentPolicy(
        consent_type="evidence_recording",
        required=False,  # implicit during emergency button
        purpose="Record audio/video evidence during emergency (stored encrypted)",
        data_types=["audio_recording", "video_recording", "timestamp"],
        legal_basis="Indian Evidence Act - Digital evidence admissibility",
        retention_period="Encrypted recordings stored for 90 days or until case resolution"
    ),
    
    "government_integration": ConsentPolicy(
        consent_type="government_integration",
        required=True,  # opt-in with clear explanation
        purpose="Share anonymized incident data with NCW/State Women's Commission for policy improvement",
        data_types=["incident_type", "location_district", "outcome"],
        legal_basis="DPDP Act 2023 - Public interest processing with consent",
        retention_period="Anonymized data retained indefinitely for research"
    ),
    
    "analytics": ConsentPolicy(
        consent_type="analytics",
        required=False,
        purpose="Improve app features using anonymized usage data",
        data_types=["feature_usage", "response_time", "error_logs"],
        legal_basis="DPDP Act 2023 - Legitimate interest",
        retention_period="Anonymized analytics for 24 months"
    )
}


# ── In-memory storage (replace with database) ────────────────────────────────
_consent_records: Dict[str, List[ConsentRecord]] = {}  # user_id -> list of consents


def grant_consent(
    user_id: str,
    consent_type: str,
    duration_days: Optional[int] = None
) -> ConsentRecord:
    """
    Grant consent for a specific data usage.
    
    Args:
        user_id: User identifier
        consent_type: Type of consent (from CONSENT_POLICIES)
        duration_days: Optional expiration (None = permanent)
        
    Returns:
        ConsentRecord
    """
    policy = CONSENT_POLICIES.get(consent_type)
    if not policy:
        raise ValueError(f"Unknown consent type: {consent_type}")
        
    now = datetime.utcnow()
    expires = None
    if duration_days:
        from datetime import timedelta
        expires = (now + timedelta(days=duration_days)).isoformat()
        
    consent_id = f"{user_id}:{consent_type}:{now.timestamp()}"
    
    record = ConsentRecord(
        consent_id=consent_id,
        user_id=user_id,
        consent_type=consent_type,
        granted=True,
        purpose=policy.purpose,
        data_types=policy.data_types,
        granted_at=now.isoformat(),
        revoked_at=None,
        expires_at=expires
    )
    
    if user_id not in _consent_records:
        _consent_records[user_id] = []
        
    # revoke any existing consent of same type
    for existing in _consent_records[user_id]:
        if existing.consent_type == consent_type and existing.granted:
            existing.granted = False
            existing.revoked_at = now.isoformat()
            
    _consent_records[user_id].append(record)
    return record


def revoke_consent(user_id: str, consent_type: str) -> bool:
    """
    Revoke consent for a specific data usage.
    
    Args:
        user_id: User identifier
        consent_type: Type of consent to revoke
        
    Returns:
        True if consent was revoked, False if not found
    """
    records = _consent_records.get(user_id, [])
    
    for record in records:
        if record.consent_type == consent_type and record.granted:
            record.granted = False
            record.revoked_at = datetime.utcnow().isoformat()
            return True
            
    return False


def check_consent(user_id: str, consent_type: str) -> bool:
    """
    Check if user has granted valid consent.
    
    Args:
        user_id: User identifier
        consent_type: Type of consent to check
        
    Returns:
        True if consent is granted and valid
    """
    records = _consent_records.get(user_id, [])
    now = datetime.utcnow()
    
    for record in records:
        if record.consent_type == consent_type and record.granted:
            # check expiration
            if record.expires_at:
                expires = datetime.fromisoformat(record.expires_at)
                if now > expires:
                    record.granted = False
                    record.revoked_at = now.isoformat()
                    continue
                    
            return True
            
    return False


def get_user_consents(user_id: str) -> List[ConsentRecord]:
    """Get all consent records for a user"""
    return _consent_records.get(user_id, [])


def get_active_consents(user_id: str) -> List[ConsentRecord]:
    """Get only active (granted and not expired) consents"""
    records = _consent_records.get(user_id, [])
    now = datetime.utcnow()
    active = []
    
    for record in records:
        if not record.granted:
            continue
            
        # check expiration
        if record.expires_at:
            expires = datetime.fromisoformat(record.expires_at)
            if now > expires:
                record.granted = False
                record.revoked_at = now.isoformat()
                continue
                
        active.append(record)
        
    return active


def get_required_consents(feature: str) -> List[str]:
    """
    Get list of consent types required for a feature.
    
    Args:
        feature: Feature name (e.g., 'sos_button', 'location_sharing')
        
    Returns:
        List of required consent_type strings
    """
    feature_requirements = {
        "sos_button": ["emergency_location", "guardian_alerts"],
        "location_sharing": ["emergency_location", "guardian_alerts"],
        "police_integration": ["emergency_location", "police_sharing"],
        "evidence_recording": ["evidence_recording"],
        "data_analytics": ["analytics"],
        "government_reporting": ["government_integration"]
    }
    
    return feature_requirements.get(feature, [])


def check_feature_consent(user_id: str, feature: str) -> Dict:
    """
    Check if user has all required consents for a feature.
    
    Args:
        user_id: User identifier
        feature: Feature name
        
    Returns:
        Dict with 'allowed' bool and 'missing_consents' list
    """
    required = get_required_consents(feature)
    missing = []
    
    for consent_type in required:
        if not check_consent(user_id, consent_type):
            missing.append(consent_type)
            
    return {
        "allowed": len(missing) == 0,
        "missing_consents": missing,
        "required_consents": required
    }


def get_consent_text(consent_type: str, language: str = "en") -> Dict:
    """
    Get user-friendly consent text in specified language.
    
    Args:
        consent_type: Type of consent
        language: Language code
        
    Returns:
        Dict with title, description, data_types, legal_basis
    """
    policy = CONSENT_POLICIES.get(consent_type)
    if not policy:
        return {}
        
    # Base English text
    text = {
        "consent_type": consent_type,
        "title": consent_type.replace("_", " ").title(),
        "description": policy.purpose,
        "data_types": policy.data_types,
        "legal_basis": policy.legal_basis,
        "retention": policy.retention_period,
        "required": policy.required
    }
    
    # TODO: Add translations for other languages
    # For now, return English
    
    return text


def bulk_grant_consents(user_id: str, consent_types: List[str]) -> List[ConsentRecord]:
    """
    Grant multiple consents at once (e.g., during onboarding).
    
    Args:
        user_id: User identifier
        consent_types: List of consent types to grant
        
    Returns:
        List of created ConsentRecords
    """
    records = []
    for consent_type in consent_types:
        try:
            record = grant_consent(user_id, consent_type)
            records.append(record)
        except ValueError as e:
            print(f"Skipping invalid consent type: {consent_type}")
            continue
            
    return records


def export_consent_history(user_id: str) -> Dict:
    """
    Export user's consent history (for GDPR-style data portability).
    
    Args:
        user_id: User identifier
        
    Returns:
        Dict with all consent records and metadata
    """
    records = get_user_consents(user_id)
    
    return {
        "user_id": user_id,
        "export_date": datetime.utcnow().isoformat(),
        "total_consents": len(records),
        "active_consents": len([r for r in records if r.granted]),
        "consents": [asdict(r) for r in records]
    }


def delete_all_user_consents(user_id: str) -> int:
    """
    Delete all consent records for a user (for right to erasure).
    
    Args:
        user_id: User identifier
        
    Returns:
        Number of consents deleted
    """
    records = _consent_records.get(user_id, [])
    count = len(records)
    
    if user_id in _consent_records:
        del _consent_records[user_id]
        
    return count
