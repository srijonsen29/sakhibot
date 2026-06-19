"""
Emergency Response API Endpoints
Handles SOS triggers, location sharing, and guardian alerts.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

from core.gps_location import (
    LocationData, LocationShare,
    create_location_from_coords,
    create_location_share,
    update_location_share,
    get_active_share,
    cancel_location_share,
    get_user_active_shares,
    find_nearby_police_stations,
    format_location_for_sms,
    generate_location_share_link
)
from core.guardian_network import (
    Guardian, EmergencyAlert,
    add_guardian, get_guardians, verify_guardian, remove_guardian,
    send_emergency_alert, get_alert_status, get_user_alerts,
    set_alert_preferences, get_alert_preferences,
    quick_setup_guardian_network
)


router = APIRouter(prefix="/api/emergency", tags=["emergency"])


# ── Request/Response Models ──────────────────────────────────────────────────

class SOSRequest(BaseModel):
    user_id: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = 10.0
    message: Optional[str] = "I need help NOW!"
    

class LocationShareRequest(BaseModel):
    user_id: str
    latitude: float
    longitude: float
    accuracy: float = 10.0
    guardian_ids: List[str] = []  # specific guardians, empty = all
    duration_minutes: int = 60
    

class LocationUpdateRequest(BaseModel):
    share_id: str
    latitude: float
    longitude: float
    accuracy: float = 10.0
    

class AddGuardianRequest(BaseModel):
    user_id: str
    name: str
    phone: str
    email: Optional[str] = None
    relation: str = "friend"
    priority: int = 1
    

class QuickSetupRequest(BaseModel):
    user_id: str
    guardians: List[Dict]  # [{"name": "...", "phone": "...", ...}]
    

class AlertPreferencesRequest(BaseModel):
    user_id: str
    channels: List[Dict]  # [{"channel_type": "sms", "enabled": true, "priority": 1}]
    auto_alert_on_sos: bool = True
    include_location: bool = True


# ── SOS Endpoints ────────────────────────────────────────────────────────────

@router.post("/sos")
async def trigger_sos(req: SOSRequest):
    """
    Emergency SOS trigger - sends immediate alerts to all guardians.
    
    This is the critical endpoint activated by the SOS button in the app.
    Automatically shares location and alerts guardian network.
    """
    try:
        # Create location data if provided
        location_data = None
        share_link = None
        
        if req.latitude and req.longitude:
            location = create_location_from_coords(
                req.latitude,
                req.longitude,
                req.accuracy
            )
            location_data = {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "address": location.address,
                "district": location.district,
                "state": location.state,
                "nearest_station": location.nearest_station,
                "accuracy": location.accuracy,
                "timestamp": location.timestamp
            }
            
            # Get guardians to share with
            guardians = get_guardians(req.user_id, verified_only=True)
            if not guardians:
                guardians = get_guardians(req.user_id, verified_only=False)
                
            guardian_phones = [g.phone for g in guardians]
            
            # Create live location share
            if guardian_phones:
                share = create_location_share(
                    user_id=req.user_id,
                    location=location,
                    recipients=guardian_phones,
                    duration_minutes=120,  # 2 hours for emergency
                    is_emergency=True
                )
                share_link = generate_location_share_link(share.share_id)
            
        # Send alert to guardian network
        alert = send_emergency_alert(
            user_id=req.user_id,
            message=req.message,
            severity="critical",
            location_data=location_data,
            share_link=share_link
        )
        
        # Find nearby police stations
        police_stations = []
        if req.latitude and req.longitude:
            police_stations = find_nearby_police_stations(
                req.latitude,
                req.longitude,
                radius_km=5.0
            )
        
        return {
            "status": "alert_sent",
            "alert_id": alert.alert_id,
            "guardians_notified": len(alert.sent_to),
            "delivery_status": alert.delivery_status,
            "share_link": share_link,
            "location": location_data,
            "nearby_police": police_stations,
            "emergency_numbers": [
                {"name": "Women's Helpline", "number": "181"},
                {"name": "Police", "number": "100"},
                {"name": "National Emergency", "number": "112"}
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sos/status/{alert_id}")
async def get_sos_status(alert_id: str):
    """Check status of an emergency alert"""
    alert = get_alert_status(alert_id)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    return {
        "alert_id": alert.alert_id,
        "severity": alert.severity,
        "sent_to": alert.sent_to,
        "delivery_status": alert.delivery_status,
        "created_at": alert.created_at,
        "location": alert.location_data,
        "share_link": alert.share_link
    }


# ── Location Sharing Endpoints ───────────────────────────────────────────────

@router.post("/location/share")
async def share_location(req: LocationShareRequest):
    """
    Start sharing live location with guardians.
    Non-emergency location sharing (user-initiated).
    """
    try:
        location = create_location_from_coords(
            req.latitude,
            req.longitude,
            req.accuracy
        )
        
        # Get recipients
        if req.guardian_ids:
            guardians = [g for g in get_guardians(req.user_id) 
                        if g.guardian_id in req.guardian_ids]
        else:
            guardians = get_guardians(req.user_id, verified_only=True)
            
        if not guardians:
            raise HTTPException(
                status_code=400,
                detail="No guardians found. Add guardians first."
            )
            
        recipient_phones = [g.phone for g in guardians]
        
        share = create_location_share(
            user_id=req.user_id,
            location=location,
            recipients=recipient_phones,
            duration_minutes=req.duration_minutes,
            is_emergency=False
        )
        
        share_link = generate_location_share_link(share.share_id)
        
        return {
            "status": "sharing_started",
            "share_id": share.share_id,
            "share_link": share_link,
            "recipients": [g.name for g in guardians],
            "expires_at": share.expires_at,
            "location": {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "address": location.address
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/location/update")
async def update_location(req: LocationUpdateRequest):
    """Update location for an active share"""
    location = create_location_from_coords(
        req.latitude,
        req.longitude,
        req.accuracy
    )
    
    share = update_location_share(req.share_id, location)
    
    if not share:
        raise HTTPException(
            status_code=404,
            detail="Share not found or expired"
        )
        
    return {
        "status": "location_updated",
        "share_id": share.share_id,
        "location": {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "address": location.address,
            "timestamp": location.timestamp
        }
    }


@router.get("/location/track/{share_id}")
async def track_location(share_id: str):
    """Get current location for a share (used by guardians)"""
    share = get_active_share(share_id)
    
    if not share:
        raise HTTPException(
            status_code=404,
            detail="Share not found, expired, or cancelled"
        )
        
    return {
        "share_id": share.share_id,
        "is_emergency": share.is_emergency,
        "location": {
            "latitude": share.location.latitude,
            "longitude": share.location.longitude,
            "address": share.location.address,
            "district": share.location.district,
            "state": share.location.state,
            "accuracy": share.location.accuracy,
            "timestamp": share.location.timestamp
        },
        "expires_at": share.expires_at,
        "status": share.status
    }


@router.post("/location/cancel/{share_id}")
async def cancel_share(share_id: str):
    """Cancel an active location share"""
    success = cancel_location_share(share_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Share not found")
        
    return {"status": "cancelled", "share_id": share_id}


@router.get("/location/active/{user_id}")
async def get_active_shares(user_id: str):
    """Get all active location shares for a user"""
    shares = get_user_active_shares(user_id)
    
    return {
        "user_id": user_id,
        "active_shares": [
            {
                "share_id": s.share_id,
                "is_emergency": s.is_emergency,
                "recipients": s.recipients,
                "expires_at": s.expires_at,
                "share_link": generate_location_share_link(s.share_id)
            }
            for s in shares
        ]
    }


# ── Guardian Network Endpoints ───────────────────────────────────────────────

@router.post("/guardians/add")
async def add_guardian_contact(req: AddGuardianRequest):
    """Add a trusted contact to guardian network"""
    guardian = add_guardian(
        user_id=req.user_id,
        name=req.name,
        phone=req.phone,
        email=req.email,
        relation=req.relation,
        priority=req.priority
    )
    
    return {
        "status": "guardian_added",
        "guardian": {
            "guardian_id": guardian.guardian_id,
            "name": guardian.name,
            "phone": guardian.phone,
            "relation": guardian.relation,
            "priority": guardian.priority,
            "verified": guardian.verified
        }
    }


@router.post("/guardians/quick-setup")
async def quick_setup(req: QuickSetupRequest):
    """Quick setup during onboarding - add multiple guardians"""
    guardians = quick_setup_guardian_network(req.user_id, req.guardians)
    
    return {
        "status": "setup_complete",
        "guardians_added": len(guardians),
        "guardians": [
            {
                "guardian_id": g.guardian_id,
                "name": g.name,
                "phone": g.phone,
                "relation": g.relation,
                "priority": g.priority
            }
            for g in guardians
        ]
    }


@router.get("/guardians/{user_id}")
async def list_guardians(user_id: str, verified_only: bool = False):
    """Get user's guardian list"""
    guardians = get_guardians(user_id, verified_only=verified_only)
    
    return {
        "user_id": user_id,
        "total": len(guardians),
        "guardians": [
            {
                "guardian_id": g.guardian_id,
                "name": g.name,
                "phone": g.phone,
                "email": g.email,
                "relation": g.relation,
                "priority": g.priority,
                "verified": g.verified,
                "added_at": g.added_at
            }
            for g in guardians
        ]
    }


@router.post("/guardians/verify/{user_id}/{guardian_id}")
async def verify_guardian_contact(user_id: str, guardian_id: str):
    """Verify a guardian (after SMS confirmation)"""
    success = verify_guardian(user_id, guardian_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Guardian not found")
        
    return {"status": "verified", "guardian_id": guardian_id}


@router.delete("/guardians/{user_id}/{guardian_id}")
async def delete_guardian(user_id: str, guardian_id: str):
    """Remove a guardian from network"""
    success = remove_guardian(user_id, guardian_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Guardian not found")
        
    return {"status": "removed", "guardian_id": guardian_id}


# ── Alert Preferences ────────────────────────────────────────────────────────

@router.post("/preferences")
async def set_preferences(req: AlertPreferencesRequest):
    """Set alert channel preferences"""
    from core.guardian_network import AlertChannel
    
    channels = [
        AlertChannel(**ch) for ch in req.channels
    ]
    
    prefs = set_alert_preferences(
        user_id=req.user_id,
        channels=channels,
        auto_alert_on_sos=req.auto_alert_on_sos,
        include_location=req.include_location
    )
    
    return {"status": "preferences_updated", "preferences": prefs}


@router.get("/preferences/{user_id}")
async def get_preferences(user_id: str):
    """Get alert preferences"""
    prefs = get_alert_preferences(user_id)
    return {"user_id": user_id, "preferences": prefs}


# ── Alert History ────────────────────────────────────────────────────────────

@router.get("/alerts/{user_id}")
async def get_alerts(user_id: str, limit: int = 10):
    """Get recent emergency alerts for a user"""
    alerts = get_user_alerts(user_id, limit=limit)
    
    return {
        "user_id": user_id,
        "total": len(alerts),
        "alerts": [
            {
                "alert_id": a.alert_id,
                "message": a.message,
                "severity": a.severity,
                "guardians_notified": len(a.sent_to),
                "delivery_status": a.delivery_status,
                "created_at": a.created_at,
                "has_location": a.location_data is not None
            }
            for a in alerts
        ]
    }
