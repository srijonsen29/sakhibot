"""
User Consent Management for Privacy Compliance
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class ConsentRecord:
    consent_id: str
    user_id: str
    consent_type: str
    granted: bool
    purpose: str
    data_types: List[str]
    granted_at: Optional[str] = None
    revoked_at: Optional[str] = None
    expires_at: Optional[str] = None


@dataclass
class ConsentPolicy:
    consent_type: str
    required: bool
    purpose: str
    data_types: List[str]
    legal_basis: str
    retention_period: str


CONSENT_POLICIES = {
    "emergency_location": ConsentPolicy(
        consent_type="emergency_location", required=False,
        purpose="Share your GPS location with emergency services and guardians during SOS",
        data_types=["gps_latitude", "gps_longitude", "address"],
        legal_basis="IT Act 2000 Section 43A - Sensitive Personal Data with consent",
        retention_period="Location shared during emergency only, not stored after incident resolved"
    ),
    "guardian_alerts": ConsentPolicy(
        consent_type="guardian_alerts", required=True,
        purpose="Send emergency alerts to your trusted contacts via SMS/WhatsApp/Call",
        data_types=["phone_number", "name", "emergency_status"],
        legal_basis="DPDP Act 2023 - Explicit consent for processing",
        retention_period="Guardian list stored until you remove them"
    ),
    "police_sharing": ConsentPolicy(
        consent_type="police_sharing", required=True,
        purpose="Automatically notify police with your location during critical emergencies",
        data_types=["gps_location", "phone_number", "incident_details"],
        legal_basis="IT Act 2000 + State Police Integration Acts",
        retention_period="Incident data shared with police per legal requirements"
    ),
    "evidence_recording": ConsentPolicy(
        consent_type="evidence_recording", required=False,
        purpose="Record audio/video evidence during emergency (stored encrypted)",
        data_types=["audio_recording", "video_recording", "timestamp"],
        legal_basis="Indian Evidence Act - Digital evidence admissibility",
        retention_period="Encrypted recordings stored for 90 days or until case resolution"
    ),
    "government_integration": ConsentPolicy(
        consent_type="government_integration", required=True,
        purpose="Share anonymized incident data with NCW/State Women's Commission for policy improvement",
        data_types=["incident_type", "location_district", "outcome"],
        legal_basis="DPDP Act 2023 - Public interest processing with consent",
        retention_period="Anonymized data retained indefinitely for research"
    ),
    "analytics": ConsentPolicy(
        consent_type="analytics", required=False,
        purpose="Improve app features using anonymized usage data",
        data_types=["feature_usage", "response_time", "error_logs"],
        legal_basis="DPDP Act 2023 - Legitimate interest",
        retention_period="Anonymized analytics for 24 months"
    )
}

_consent_records: Dict[str, List[ConsentRecord]] = {}


def grant_consent(user_id: str, consent_type: str, duration_days: Optional[int] = None) -> ConsentRecord:
    policy = CONSENT_POLICIES.get(consent_type)
    if not policy:
        raise ValueError(f"Unknown consent type: {consent_type}")
    
    now = datetime.utcnow()
    expires = None
    if duration_days:
        expires = (now + timedelta(days=duration_days)).isoformat()
    
    consent_id = f"{user_id}:{consent_type}:{now.timestamp()}"
    record = ConsentRecord(
        consent_id=consent_id, user_id=user_id, consent_type=consent_type,
        granted=True, purpose=policy.purpose, data_types=policy.data_types,
        granted_at=now.isoformat(), revoked_at=None, expires_at=expires
    )
    
    if user_id not in _consent_records:
        _consent_records[user_id] = []
    
    for existing in _consent_records[user_id]:
        if existing.consent_type == consent_type and existing.granted:
            existing.granted = False
            existing.revoked_at = now.isoformat()
    
    _consent_records[user_id].append(record)
    return record


def revoke_consent(user_id: str, consent_type: str) -> bool:
    records = _consent_records.get(user_id, [])
    for record in records:
        if record.consent_type == consent_type and record.granted:
            record.granted = False
            record.revoked_at = datetime.utcnow().isoformat()
            return True
    return False


def check_consent(user_id: str, consent_type: str) -> bool:
    records = _consent_records.get(user_id, [])
    now = datetime.utcnow()
    for record in records:
        if record.consent_type == consent_type and record.granted:
            if record.expires_at:
                expires = datetime.fromisoformat(record.expires_at)
                if now > expires:
                    record.granted = False
                    record.revoked_at = now.isoformat()
                    continue
            return True
    return False


def get_user_consents(user_id: str) -> List[ConsentRecord]:
    return _consent_records.get(user_id, [])


def get_active_consents(user_id: str) -> List[ConsentRecord]:
    records = _consent_records.get(user_id, [])
    now = datetime.utcnow()
    active = []
    for record in records:
        if not record.granted:
            continue
        if record.expires_at:
            expires = datetime.fromisoformat(record.expires_at)
            if now > expires:
                record.granted = False
                record.revoked_at = now.isoformat()
                continue
        active.append(record)
    return active


def check_feature_consent(user_id: str, feature: str) -> Dict:
    feature_requirements = {
        "sos_button": ["emergency_location", "guardian_alerts"],
        "location_sharing": ["emergency_location", "guardian_alerts"],
        "police_integration": ["emergency_location", "police_sharing"],
    }
    required = feature_requirements.get(feature, [])
    missing = [ct for ct in required if not check_consent(user_id, ct)]
    return {"allowed": len(missing) == 0, "missing_consents": missing, "required_consents": required}


def get_consent_text(consent_type: str, language: str = "en") -> Dict:
    policy = CONSENT_POLICIES.get(consent_type)
    if not policy:
        return {}
    return {
        "consent_type": consent_type,
        "title": consent_type.replace("_", " ").title(),
        "description": policy.purpose,
        "data_types": policy.data_types,
        "legal_basis": policy.legal_basis,
        "retention": policy.retention_period,
        "required": policy.required
    }


def bulk_grant_consents(user_id: str, consent_types: List[str]) -> List[ConsentRecord]:
    records = []
    for consent_type in consent_types:
        try:
            record = grant_consent(user_id, consent_type)
            records.append(record)
        except ValueError:
            continue
    return records


def export_consent_history(user_id: str) -> Dict:
    records = get_user_consents(user_id)
    return {
        "user_id": user_id,
        "export_date": datetime.utcnow().isoformat(),
        "total_consents": len(records),
        "active_consents": len([r for r in records if r.granted]),
        "consents": [asdict(r) for r in records]
    }


def delete_all_user_consents(user_id: str) -> int:
    records = _consent_records.get(user_id, [])
    count = len(records)
    if user_id in _consent_records:
        del _consent_records[user_id]
    return count
