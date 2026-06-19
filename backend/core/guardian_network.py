"""
Guardian Network - Trusted contacts and emergency alerts
Manages guardian contacts and multi-channel alert system.
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import hashlib


@dataclass
class Guardian:
    """Trusted contact information"""
    guardian_id: str
    name: str
    phone: str
    email: Optional[str] = None
    relation: str = "friend"  # friend, family, neighbor, colleague
    priority: int = 1         # 1=primary, 2=secondary, 3=tertiary
    verified: bool = False
    added_at: str = ""
    
    
@dataclass
class AlertChannel:
    """Alert delivery channel configuration"""
    channel_type: str  # 'sms', 'whatsapp', 'call', 'email'
    enabled: bool
    priority: int      # order to try channels


@dataclass
class EmergencyAlert:
    """Emergency alert sent to guardians"""
    alert_id: str
    user_id: str
    message: str
    location_data: Optional[Dict] = None
    share_link: Optional[str] = None
    severity: str = "high"
    sent_to: List[str] = None       # guardian IDs
    delivery_status: Dict = None    # guardian_id -> status
    created_at: str = ""
    
    def __post_init__(self):
        if self.sent_to is None:
            self.sent_to = []
        if self.delivery_status is None:
            self.delivery_status = {}


# ── in-memory stores (replace with database in production) ───────────────────
_guardians: Dict[str, List[Guardian]] = {}        # user_id -> List[Guardian]
_alerts: Dict[str, EmergencyAlert] = {}           # alert_id -> Alert
_user_preferences: Dict[str, Dict] = {}           # user_id -> alert preferences


def generate_guardian_id(user_id: str, phone: str) -> str:
    """Generate unique guardian ID"""
    raw = f"{user_id}:{phone}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def generate_alert_id(user_id: str) -> str:
    """Generate unique alert ID"""
    timestamp = datetime.utcnow().isoformat()
    raw = f"{user_id}:{timestamp}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ── Guardian Management ──────────────────────────────────────────────────────

def add_guardian(
    user_id: str,
    name: str,
    phone: str,
    email: Optional[str] = None,
    relation: str = "friend",
    priority: int = 1
) -> Guardian:
    """
    Add a trusted contact to user's guardian network.
    
    Args:
        user_id: User identifier
        name: Guardian's name
        phone: Guardian's phone number (for alerts)
        email: Optional email
        relation: Relationship type
        priority: Alert priority (1=first to notify)
        
    Returns:
        Guardian object
    """
    guardian = Guardian(
        guardian_id=generate_guardian_id(user_id, phone),
        name=name,
        phone=phone,
        email=email,
        relation=relation,
        priority=priority,
        verified=False,
        added_at=datetime.utcnow().isoformat()
    )
    
    if user_id not in _guardians:
        _guardians[user_id] = []
        
    _guardians[user_id].append(guardian)
    _guardians[user_id].sort(key=lambda g: g.priority)  # keep sorted by priority
    
    return guardian


def get_guardians(user_id: str, verified_only: bool = False) -> List[Guardian]:
    """Get user's guardian list"""
    guardians = _guardians.get(user_id, [])
    
    if verified_only:
        return [g for g in guardians if g.verified]
        
    return guardians


def verify_guardian(user_id: str, guardian_id: str) -> bool:
    """Mark guardian as verified (after they confirm via SMS/email)"""
    guardians = _guardians.get(user_id, [])
    
    for guardian in guardians:
        if guardian.guardian_id == guardian_id:
            guardian.verified = True
            return True
            
    return False


def remove_guardian(user_id: str, guardian_id: str) -> bool:
    """Remove a guardian from network"""
    guardians = _guardians.get(user_id, [])
    
    for i, guardian in enumerate(guardians):
        if guardian.guardian_id == guardian_id:
            guardians.pop(i)
            return True
            
    return False


def update_guardian_priority(user_id: str, guardian_id: str, new_priority: int) -> bool:
    """Change guardian's notification priority"""
    guardians = _guardians.get(user_id, [])
    
    for guardian in guardians:
        if guardian.guardian_id == guardian_id:
            guardian.priority = new_priority
            _guardians[user_id].sort(key=lambda g: g.priority)
            return True
            
    return False


# ── Alert Management ─────────────────────────────────────────────────────────

def set_alert_preferences(
    user_id: str,
    channels: List[AlertChannel],
    auto_alert_on_sos: bool = True,
    include_location: bool = True
) -> Dict:
    """
    Configure user's alert preferences.
    
    Args:
        user_id: User identifier
        channels: Ordered list of alert channels to use
        auto_alert_on_sos: Automatically alert guardians on SOS button
        include_location: Share GPS location with alerts
        
    Returns:
        Updated preferences dict
    """
    prefs = {
        "channels": [asdict(c) for c in channels],
        "auto_alert_on_sos": auto_alert_on_sos,
        "include_location": include_location,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    _user_preferences[user_id] = prefs
    return prefs


def get_alert_preferences(user_id: str) -> Dict:
    """Get user's alert preferences"""
    return _user_preferences.get(user_id, {
        "channels": [
            {"channel_type": "sms", "enabled": True, "priority": 1},
            {"channel_type": "call", "enabled": True, "priority": 2},
            {"channel_type": "whatsapp", "enabled": False, "priority": 3},
        ],
        "auto_alert_on_sos": True,
        "include_location": True
    })


def send_emergency_alert(
    user_id: str,
    message: str,
    severity: str = "high",
    location_data: Optional[Dict] = None,
    share_link: Optional[str] = None,
    specific_guardians: Optional[List[str]] = None
) -> EmergencyAlert:
    """
    Send emergency alert to guardian network.
    
    Args:
        user_id: User in emergency
        message: Alert message
        severity: 'critical', 'high', 'medium'
        location_data: GPS location dict
        share_link: Live location tracking link
        specific_guardians: Optional list of guardian IDs to alert (None = all)
        
    Returns:
        EmergencyAlert object with delivery status
    """
    # get guardians to notify
    all_guardians = get_guardians(user_id, verified_only=True)
    
    if specific_guardians:
        guardians = [g for g in all_guardians if g.guardian_id in specific_guardians]
    else:
        guardians = all_guardians
        
    if not guardians:
        # fallback - use unverified guardians if no verified ones exist
        guardians = get_guardians(user_id, verified_only=False)
        
    # create alert
    alert = EmergencyAlert(
        alert_id=generate_alert_id(user_id),
        user_id=user_id,
        message=message,
        location_data=location_data,
        share_link=share_link,
        severity=severity,
        sent_to=[g.guardian_id for g in guardians],
        delivery_status={},
        created_at=datetime.utcnow().isoformat()
    )
    
    # get user's channel preferences
    prefs = get_alert_preferences(user_id)
    channels = sorted(prefs["channels"], key=lambda c: c["priority"])
    
    # simulate sending (replace with actual SMS/WhatsApp/Call APIs)
    for guardian in guardians:
        status = _send_to_guardian(guardian, alert, channels)
        alert.delivery_status[guardian.guardian_id] = status
        
    _alerts[alert.alert_id] = alert
    return alert


def _send_to_guardian(
    guardian: Guardian,
    alert: EmergencyAlert,
    channels: List[Dict]
) -> Dict:
    """
    Send alert through available channels (mock implementation).
    
    In production, integrate with:
    - SMS: Twilio, AWS SNS, TextLocal (India)
    - WhatsApp: Twilio WhatsApp API, Meta Business API
    - Calls: Twilio Voice, Exotel (India)
    - Email: SendGrid, AWS SES
    """
    # Mock implementation - logs what would be sent
    status = {
        "guardian_name": guardian.name,
        "guardian_phone": guardian.phone,
        "attempts": [],
        "delivered": False,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    for channel in channels:
        if not channel["enabled"]:
            continue
            
        channel_type = channel["channel_type"]
        
        # Format message based on channel
        if channel_type == "sms":
            formatted_msg = _format_sms_alert(alert)
            # TODO: Integrate actual SMS API
            # sms_service.send(to=guardian.phone, body=formatted_msg)
            status["attempts"].append({
                "channel": "sms",
                "status": "sent (mock)",
                "message": formatted_msg[:50] + "..."
            })
            status["delivered"] = True
            break  # stop after first successful delivery
            
        elif channel_type == "whatsapp":
            formatted_msg = _format_whatsapp_alert(alert)
            # TODO: Integrate WhatsApp API
            status["attempts"].append({
                "channel": "whatsapp",
                "status": "sent (mock)",
                "message": formatted_msg[:50] + "..."
            })
            status["delivered"] = True
            break
            
        elif channel_type == "call":
            # TODO: Integrate voice call API with pre-recorded message
            status["attempts"].append({
                "channel": "call",
                "status": "initiated (mock)"
            })
            status["delivered"] = True
            break
            
        elif channel_type == "email" and guardian.email:
            formatted_msg = _format_email_alert(alert, guardian)
            # TODO: Integrate email service
            status["attempts"].append({
                "channel": "email",
                "status": "sent (mock)",
                "to": guardian.email
            })
            status["delivered"] = True
            break
            
    return status


def _format_sms_alert(alert: EmergencyAlert) -> str:
    """Format alert for SMS (160 char limit awareness)"""
    msg = f"🚨 EMERGENCY ALERT\n{alert.message}\n"
    
    if alert.location_data:
        lat = alert.location_data.get("latitude")
        lon = alert.location_data.get("longitude")
        if lat and lon:
            msg += f"Location: https://maps.google.com/?q={lat},{lon}\n"
            
    if alert.share_link:
        msg += f"Track: {alert.share_link}\n"
        
    msg += f"Time: {alert.created_at}"
    return msg


def _format_whatsapp_alert(alert: EmergencyAlert) -> str:
    """Format alert for WhatsApp (richer formatting)"""
    msg = f"*🚨 EMERGENCY ALERT*\n\n{alert.message}\n\n"
    
    if alert.location_data:
        addr = alert.location_data.get("address", "Unknown")
        lat = alert.location_data.get("latitude")
        lon = alert.location_data.get("longitude")
        msg += f"📍 *Location:* {addr}\n"
        if lat and lon:
            msg += f"Maps: https://maps.google.com/?q={lat},{lon}\n\n"
            
    if alert.share_link:
        msg += f"🔴 *Live Tracking:* {alert.share_link}\n\n"
        
    msg += f"⏰ {alert.created_at}\n"
    msg += f"⚠️ Severity: {alert.severity.upper()}"
    return msg


def _format_email_alert(alert: EmergencyAlert, guardian: Guardian) -> str:
    """Format alert for email"""
    msg = f"""
Dear {guardian.name},

This is an EMERGENCY ALERT from SakhiBot.

{alert.message}

"""
    
    if alert.location_data:
        msg += f"\nLOCATION DETAILS:\n"
        msg += f"Address: {alert.location_data.get('address', 'Unknown')}\n"
        lat = alert.location_data.get("latitude")
        lon = alert.location_data.get("longitude")
        if lat and lon:
            msg += f"GPS: {lat}, {lon}\n"
            msg += f"Google Maps: https://maps.google.com/?q={lat},{lon}\n"
            
    if alert.share_link:
        msg += f"\nLIVE TRACKING: {alert.share_link}\n"
        
    msg += f"\nTime: {alert.created_at}\n"
    msg += f"Severity: {alert.severity.upper()}\n"
    msg += "\nPlease check on them immediately or contact emergency services.\n"
    msg += "\n- SakhiBot Emergency System"
    
    return msg


def get_alert_status(alert_id: str) -> Optional[EmergencyAlert]:
    """Get alert delivery status"""
    return _alerts.get(alert_id)


def get_user_alerts(user_id: str, limit: int = 10) -> List[EmergencyAlert]:
    """Get recent alerts for a user"""
    user_alerts = [
        alert for alert in _alerts.values()
        if alert.user_id == user_id
    ]
    
    # sort by created_at descending
    user_alerts.sort(key=lambda a: a.created_at, reverse=True)
    return user_alerts[:limit]


# ── Quick Setup ──────────────────────────────────────────────────────────────

def quick_setup_guardian_network(
    user_id: str,
    guardians_data: List[Dict]
) -> List[Guardian]:
    """
    Quick setup for guardian network during onboarding.
    
    Args:
        user_id: User identifier
        guardians_data: List of dicts with guardian info
            [{"name": "Mom", "phone": "+91...", "relation": "family", "priority": 1}, ...]
            
    Returns:
        List of created Guardian objects
    """
    created = []
    
    for data in guardians_data:
        guardian = add_guardian(
            user_id=user_id,
            name=data["name"],
            phone=data["phone"],
            email=data.get("email"),
            relation=data.get("relation", "friend"),
            priority=data.get("priority", len(created) + 1)
        )
        created.append(guardian)
        
    return created
