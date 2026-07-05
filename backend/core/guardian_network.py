"""
Guardian Network - Trusted contacts and emergency alerts
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib


@dataclass
class Guardian:
    guardian_id: str
    name: str
    phone: str
    email: Optional[str] = None
    relation: str = "friend"
    priority: int = 1
    verified: bool = False
    added_at: str = ""


@dataclass
class AlertChannel:
    channel_type: str
    enabled: bool
    priority: int


@dataclass
class EmergencyAlert:
    alert_id: str
    user_id: str
    message: str
    location_data: Optional[Dict] = None
    share_link: Optional[str] = None
    severity: str = "high"
    sent_to: List[str] = None
    delivery_status: Dict = None
    created_at: str = ""
    
    def __post_init__(self):
        if self.sent_to is None:
            self.sent_to = []
        if self.delivery_status is None:
            self.delivery_status = {}


_guardians: Dict[str, List[Guardian]] = {}
_alerts: Dict[str, EmergencyAlert] = {}
_user_preferences: Dict[str, Dict] = {}


def generate_guardian_id(user_id: str, phone: str) -> str:
    return hashlib.sha256(f"{user_id}:{phone}".encode()).hexdigest()[:12]


def generate_alert_id(user_id: str) -> str:
    timestamp = datetime.utcnow().isoformat()
    return hashlib.sha256(f"{user_id}:{timestamp}".encode()).hexdigest()[:16]


def add_guardian(user_id: str, name: str, phone: str, email: Optional[str] = None,
                relation: str = "friend", priority: int = 1) -> Guardian:
    guardian = Guardian(
        guardian_id=generate_guardian_id(user_id, phone),
        name=name, phone=phone, email=email, relation=relation,
        priority=priority, verified=False, added_at=datetime.utcnow().isoformat()
    )
    if user_id not in _guardians:
        _guardians[user_id] = []
    _guardians[user_id].append(guardian)
    _guardians[user_id].sort(key=lambda g: g.priority)
    return guardian


def get_guardians(user_id: str, verified_only: bool = False) -> List[Guardian]:
    guardians = _guardians.get(user_id, [])
    if verified_only:
        return [g for g in guardians if g.verified]
    return guardians


def verify_guardian(user_id: str, guardian_id: str) -> bool:
    for guardian in _guardians.get(user_id, []):
        if guardian.guardian_id == guardian_id:
            guardian.verified = True
            return True
    return False


def remove_guardian(user_id: str, guardian_id: str) -> bool:
    guardians = _guardians.get(user_id, [])
    for i, guardian in enumerate(guardians):
        if guardian.guardian_id == guardian_id:
            guardians.pop(i)
            return True
    return False


def set_alert_preferences(user_id: str, channels: List[AlertChannel],
                         auto_alert_on_sos: bool = True, include_location: bool = True) -> Dict:
    prefs = {
        "channels": [asdict(c) for c in channels],
        "auto_alert_on_sos": auto_alert_on_sos,
        "include_location": include_location,
        "updated_at": datetime.utcnow().isoformat()
    }
    _user_preferences[user_id] = prefs
    return prefs


def get_alert_preferences(user_id: str) -> Dict:
    return _user_preferences.get(user_id, {
        "channels": [
            {"channel_type": "sms", "enabled": True, "priority": 1},
            {"channel_type": "call", "enabled": True, "priority": 2},
            {"channel_type": "whatsapp", "enabled": False, "priority": 3},
        ],
        "auto_alert_on_sos": True,
        "include_location": True
    })


def send_emergency_alert(user_id: str, message: str, severity: str = "high",
                        location_data: Optional[Dict] = None, share_link: Optional[str] = None,
                        specific_guardians: Optional[List[str]] = None) -> EmergencyAlert:
    all_guardians = get_guardians(user_id, verified_only=True)
    if specific_guardians:
        guardians = [g for g in all_guardians if g.guardian_id in specific_guardians]
    else:
        guardians = all_guardians
    if not guardians:
        guardians = get_guardians(user_id, verified_only=False)
    
    alert = EmergencyAlert(
        alert_id=generate_alert_id(user_id), user_id=user_id, message=message,
        location_data=location_data, share_link=share_link, severity=severity,
        sent_to=[g.guardian_id for g in guardians], delivery_status={},
        created_at=datetime.utcnow().isoformat()
    )
    
    prefs = get_alert_preferences(user_id)
    channels = sorted(prefs["channels"], key=lambda c: c["priority"])
    
    for guardian in guardians:
        status = _send_to_guardian(guardian, alert, channels)
        alert.delivery_status[guardian.guardian_id] = status
    
    _alerts[alert.alert_id] = alert
    return alert


def _send_to_guardian(guardian: Guardian, alert: EmergencyAlert, channels: List[Dict]) -> Dict:
    """Mock send - replace with actual SMS/WhatsApp/Call APIs"""
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
        
        if channel_type == "sms":
            formatted_msg = _format_sms_alert(alert)
            status["attempts"].append({"channel": "sms", "status": "sent (mock)", "message": formatted_msg[:50] + "..."})
            status["delivered"] = True
            break
        elif channel_type == "whatsapp":
            formatted_msg = _format_whatsapp_alert(alert)
            status["attempts"].append({"channel": "whatsapp", "status": "sent (mock)", "message": formatted_msg[:50] + "..."})
            status["delivered"] = True
            break
        elif channel_type == "call":
            status["attempts"].append({"channel": "call", "status": "initiated (mock)"})
            status["delivered"] = True
            break
    
    return status


def _format_sms_alert(alert: EmergencyAlert) -> str:
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
    msg += f"⏰ {alert.created_at}\n⚠️ Severity: {alert.severity.upper()}"
    return msg


def get_alert_status(alert_id: str) -> Optional[EmergencyAlert]:
    return _alerts.get(alert_id)


def get_user_alerts(user_id: str, limit: int = 10) -> List[EmergencyAlert]:
    user_alerts = [alert for alert in _alerts.values() if alert.user_id == user_id]
    user_alerts.sort(key=lambda a: a.created_at, reverse=True)
    return user_alerts[:limit]


def quick_setup_guardian_network(user_id: str, guardians_data: List[Dict]) -> List[Guardian]:
    created = []
    for data in guardians_data:
        guardian = add_guardian(
            user_id=user_id, name=data["name"], phone=data["phone"],
            email=data.get("email"), relation=data.get("relation", "friend"),
            priority=data.get("priority", len(created) + 1)
        )
        created.append(guardian)
    return created
