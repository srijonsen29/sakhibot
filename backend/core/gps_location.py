"""
GPS Location Services for Emergency Response
Handles geolocation, address resolution, and location sharing.
"""
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class LocationData:
    """User location data structure"""
    latitude: float
    longitude: float
    accuracy: float
    timestamp: str
    address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    nearest_station: Optional[str] = None
    station_distance: Optional[float] = None


@dataclass
class LocationShare:
    """Live location sharing session"""
    share_id: str
    user_id: str
    location: LocationData
    recipients: List[str]
    expires_at: str
    is_emergency: bool
    status: str
    created_at: str


_active_shares: Dict[str, LocationShare] = {}


def generate_share_id(user_id: str, timestamp: str) -> str:
    raw = f"{user_id}:{timestamp}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def create_location_share(
    user_id: str,
    location: LocationData,
    recipients: List[str],
    duration_minutes: int = 60,
    is_emergency: bool = False
) -> LocationShare:
    now = datetime.utcnow()
    expires = now + timedelta(minutes=duration_minutes)
    timestamp = now.isoformat()
    
    share = LocationShare(
        share_id=generate_share_id(user_id, timestamp),
        user_id=user_id,
        location=location,
        recipients=recipients,
        expires_at=expires.isoformat(),
        is_emergency=is_emergency,
        status='active',
        created_at=timestamp
    )
    
    _active_shares[share.share_id] = share
    return share


def update_location_share(share_id: str, new_location: LocationData) -> Optional[LocationShare]:
    share = _active_shares.get(share_id)
    if not share or share.status != 'active':
        return None
    if datetime.fromisoformat(share.expires_at) < datetime.utcnow():
        share.status = 'expired'
        return None
    share.location = new_location
    return share


def get_active_share(share_id: str) -> Optional[LocationShare]:
    share = _active_shares.get(share_id)
    if not share or share.status != 'active':
        return None
    if datetime.fromisoformat(share.expires_at) < datetime.utcnow():
        share.status = 'expired'
        return None
    return share


def cancel_location_share(share_id: str) -> bool:
    share = _active_shares.get(share_id)
    if not share:
        return False
    share.status = 'cancelled'
    return True


def get_user_active_shares(user_id: str) -> List[LocationShare]:
    now = datetime.utcnow()
    active = []
    for share in _active_shares.values():
        if share.user_id == user_id and share.status == 'active':
            if datetime.fromisoformat(share.expires_at) >= now:
                active.append(share)
            else:
                share.status = 'expired'
    return active


def reverse_geocode(latitude: float, longitude: float) -> Dict[str, Optional[str]]:
    """Mock geocoding - replace with Google Maps API in production"""
    if 28.4 <= latitude <= 28.9 and 76.8 <= longitude <= 77.4:
        return {"address": f"Near {latitude:.4f}, {longitude:.4f}, Delhi",
                "district": "New Delhi", "state": "Delhi",
                "nearest_station": "Connaught Place Police Station"}
    elif 19.0 <= latitude <= 19.3 and 72.8 <= longitude <= 73.0:
        return {"address": f"Near {latitude:.4f}, {longitude:.4f}, Mumbai",
                "district": "Mumbai", "state": "Maharashtra",
                "nearest_station": "Colaba Police Station"}
    elif 12.9 <= latitude <= 13.1 and 77.5 <= longitude <= 77.7:
        return {"address": f"Near {latitude:.4f}, {longitude:.4f}, Bangalore",
                "district": "Bangalore Urban", "state": "Karnataka",
                "nearest_station": "Koramangala Police Station"}
    else:
        return {"address": f"Location: {latitude:.4f}, {longitude:.4f}",
                "district": "Unknown", "state": "Unknown",
                "nearest_station": "Nearest Police Station (call 100)"}


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import radians, sin, cos, sqrt, atan2
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


def find_nearby_police_stations(latitude: float, longitude: float, radius_km: float = 5.0) -> List[Dict]:
    """Mock police stations - replace with actual API"""
    return [
        {"name": "Local Police Station", "phone": "100", "distance_km": 1.2, "address": "Near your location"},
        {"name": "Women's Police Station", "phone": "100", "distance_km": 2.5, "address": "City Center"}
    ]


def create_location_from_coords(latitude: float, longitude: float, accuracy: float = 10.0) -> LocationData:
    geocoded = reverse_geocode(latitude, longitude)
    return LocationData(
        latitude=latitude, longitude=longitude, accuracy=accuracy,
        timestamp=datetime.utcnow().isoformat(),
        address=geocoded["address"], district=geocoded["district"],
        state=geocoded["state"], nearest_station=geocoded["nearest_station"]
    )


def format_location_for_sms(location: LocationData) -> str:
    return (f"EMERGENCY LOCATION\n{location.address or 'Unknown address'}\n"
            f"GPS: {location.latitude:.5f}, {location.longitude:.5f}\n"
            f"Accuracy: {location.accuracy:.0f}m\nTime: {location.timestamp}\n"
            f"Google Maps: https://maps.google.com/?q={location.latitude},{location.longitude}")


def generate_location_share_link(share_id: str) -> str:
    return f"https://sakhibot.app/track/{share_id}"
