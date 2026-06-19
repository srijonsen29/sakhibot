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
    accuracy: float          # in meters
    timestamp: str
    address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    nearest_station: Optional[str] = None
    station_distance: Optional[float] = None  # in km


@dataclass
class LocationShare:
    """Live location sharing session"""
    share_id: str
    user_id: str
    location: LocationData
    recipients: List[str]    # guardian phone numbers
    expires_at: str
    is_emergency: bool
    status: str              # 'active', 'expired', 'cancelled'
    created_at: str


# ── in-memory store (replace with Redis/DB in production) ────────────────────
_active_shares: Dict[str, LocationShare] = {}


def generate_share_id(user_id: str, timestamp: str) -> str:
    """Generate unique share ID for tracking"""
    raw = f"{user_id}:{timestamp}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def create_location_share(
    user_id: str,
    location: LocationData,
    recipients: List[str],
    duration_minutes: int = 60,
    is_emergency: bool = False
) -> LocationShare:
    """
    Create a new location sharing session.
    
    Args:
        user_id: User identifier (phone/email)
        location: Current location data
        recipients: List of guardian phone numbers
        duration_minutes: How long to share (default 1 hour)
        is_emergency: If this is an SOS share
        
    Returns:
        LocationShare object with tracking ID
    """
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
    """Update location for an active share"""
    share = _active_shares.get(share_id)
    if not share:
        return None
        
    if share.status != 'active':
        return None
        
    # check if expired
    if datetime.fromisoformat(share.expires_at) < datetime.utcnow():
        share.status = 'expired'
        return None
        
    share.location = new_location
    return share


def get_active_share(share_id: str) -> Optional[LocationShare]:
    """Get active location share by ID"""
    share = _active_shares.get(share_id)
    if not share or share.status != 'active':
        return None
        
    # auto-expire check
    if datetime.fromisoformat(share.expires_at) < datetime.utcnow():
        share.status = 'expired'
        return None
        
    return share


def cancel_location_share(share_id: str) -> bool:
    """Cancel an active location share"""
    share = _active_shares.get(share_id)
    if not share:
        return False
        
    share.status = 'cancelled'
    return True


def get_user_active_shares(user_id: str) -> List[LocationShare]:
    """Get all active shares for a user"""
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
    """
    Convert GPS coordinates to address (mock implementation).
    
    In production, integrate with:
    - Google Maps Geocoding API
    - OpenStreetMap Nominatim
    - MapMyIndia API (India-specific)
    
    Returns:
        Dict with address, district, state
    """
    # Mock implementation - returns based on rough India coordinates
    # Replace with actual API calls in production
    
    # Example coordinate ranges for major cities (very rough)
    if 28.4 <= latitude <= 28.9 and 76.8 <= longitude <= 77.4:
        return {
            "address": f"Near {latitude:.4f}, {longitude:.4f}, Delhi",
            "district": "New Delhi",
            "state": "Delhi",
            "nearest_station": "Connaught Place Police Station"
        }
    elif 19.0 <= latitude <= 19.3 and 72.8 <= longitude <= 73.0:
        return {
            "address": f"Near {latitude:.4f}, {longitude:.4f}, Mumbai",
            "district": "Mumbai",
            "state": "Maharashtra",
            "nearest_station": "Colaba Police Station"
        }
    elif 12.9 <= latitude <= 13.1 and 77.5 <= longitude <= 77.7:
        return {
            "address": f"Near {latitude:.4f}, {longitude:.4f}, Bangalore",
            "district": "Bangalore Urban",
            "state": "Karnataka",
            "nearest_station": "Koramangala Police Station"
        }
    else:
        return {
            "address": f"Location: {latitude:.4f}, {longitude:.4f}",
            "district": "Unknown",
            "state": "Unknown",
            "nearest_station": "Nearest Police Station (call 100)"
        }


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two GPS points in kilometers.
    Uses Haversine formula.
    """
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Earth radius in km
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c


def find_nearby_police_stations(
    latitude: float,
    longitude: float,
    radius_km: float = 5.0
) -> List[Dict]:
    """
    Find police stations near location (mock implementation).
    
    In production, integrate with:
    - State police department APIs
    - Google Places API
    - Government open data portals
    
    Returns:
        List of nearby police stations with contact info
    """
    # Mock data - replace with actual API
    mock_stations = [
        {
            "name": "Local Police Station",
            "phone": "100",
            "distance_km": 1.2,
            "address": "Near your location"
        },
        {
            "name": "Women's Police Station",
            "phone": "100",
            "distance_km": 2.5,
            "address": "City Center"
        }
    ]
    
    return mock_stations


def create_location_from_coords(
    latitude: float,
    longitude: float,
    accuracy: float = 10.0
) -> LocationData:
    """
    Create LocationData object from coordinates with geocoding.
    
    Args:
        latitude: GPS latitude
        longitude: GPS longitude
        accuracy: GPS accuracy in meters
        
    Returns:
        LocationData with resolved address
    """
    geocoded = reverse_geocode(latitude, longitude)
    
    return LocationData(
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy,
        timestamp=datetime.utcnow().isoformat(),
        address=geocoded["address"],
        district=geocoded["district"],
        state=geocoded["state"],
        nearest_station=geocoded["nearest_station"]
    )


def format_location_for_sms(location: LocationData) -> str:
    """
    Format location data for SMS alert.
    Keeps it concise for SMS character limits.
    """
    return (
        f"EMERGENCY LOCATION\n"
        f"{location.address or 'Unknown address'}\n"
        f"GPS: {location.latitude:.5f}, {location.longitude:.5f}\n"
        f"Accuracy: {location.accuracy:.0f}m\n"
        f"Time: {location.timestamp}\n"
        f"Google Maps: https://maps.google.com/?q={location.latitude},{location.longitude}"
    )


def generate_location_share_link(share_id: str) -> str:
    """
    Generate shareable link for live location tracking.
    
    In production, this would point to your web app's tracking page.
    """
    # Replace with your actual domain
    return f"https://sakhibot.app/track/{share_id}"
