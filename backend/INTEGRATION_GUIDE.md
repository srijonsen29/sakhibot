# 🔌 Third-Party Integration Guide

## Overview

This guide explains how to integrate real SMS, WhatsApp, calling services, and geocoding APIs to make the emergency features production-ready.

---

## 📱 SMS Integration

### Option 1: Twilio (Recommended)

**Setup:**
```bash
pip install twilio
```

**Configuration:**
```python
# Add to .env
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

**Implementation:**
```python
# core/sms_service.py
from twilio.rest import Client
import os

client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)

def send_sms(to: str, body: str):
    """Send SMS via Twilio"""
    message = client.messages.create(
        body=body,
        from_=os.getenv('TWILIO_PHONE_NUMBER'),
        to=to
    )
    return {"sid": message.sid, "status": message.status}
```

**Update guardian_network.py:**
```python
# In _send_to_guardian function, replace mock:
if channel_type == "sms":
    from core.sms_service import send_sms
    result = send_sms(guardian.phone, formatted_msg)
    status["attempts"].append({
        "channel": "sms",
        "status": result["status"],
        "sid": result["sid"]
    })
```

### Option 2: TextLocal (India-specific)

**Setup:**
```bash
pip install requests
```

**Configuration:**
```python
# Add to .env
TEXTLOCAL_API_KEY=your_api_key
TEXTLOCAL_SENDER=SAKHIB  # 6-char sender ID
```

**Implementation:**
```python
# core/textlocal_service.py
import requests
import os

def send_sms_india(to: str, message: str):
    """Send SMS via TextLocal (India)"""
    url = "https://api.textlocal.in/send/"
    
    data = {
        'apikey': os.getenv('TEXTLOCAL_API_KEY'),
        'numbers': to,
        'message': message,
        'sender': os.getenv('TEXTLOCAL_SENDER')
    }
    
    response = requests.post(url, data=data)
    return response.json()
```

**Pricing:** ~₹0.20-0.50 per SMS in India

---

## 📞 Voice Call Integration

### Twilio Voice

**Implementation:**
```python
# core/voice_service.py
from twilio.rest import Client
import os

client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)

def make_emergency_call(to: str, message: str):
    """
    Make automated voice call with TwiML message
    """
    # TwiML URL that reads the message
    twiml_url = f"https://your-domain.com/twiml/emergency?message={message}"
    
    call = client.calls.create(
        url=twiml_url,
        to=to,
        from_=os.getenv('TWILIO_PHONE_NUMBER')
    )
    
    return {"sid": call.sid, "status": call.status}
```

**TwiML Endpoint:**
```python
# Add to main.py
from twilio.twiml.voice_response import VoiceResponse

@app.get("/twiml/emergency")
async def emergency_twiml(message: str):
    """Generate TwiML for emergency voice call"""
    response = VoiceResponse()
    
    # Say message 3 times for urgency
    for _ in range(3):
        response.say(
            message,
            voice='alice',
            language='en-IN'
        )
        response.pause(length=1)
    
    return Response(
        content=str(response),
        media_type="application/xml"
    )
```

### Exotel (India-specific alternative)

**Setup:**
```bash
pip install requests
```

**Implementation:**
```python
# core/exotel_service.py
import requests
import os
from requests.auth import HTTPBasicAuth

def make_call_exotel(to: str):
    """Make call via Exotel"""
    url = f"https://api.exotel.com/v1/Accounts/{os.getenv('EXOTEL_SID')}/Calls/connect.json"
    
    auth = HTTPBasicAuth(
        os.getenv('EXOTEL_API_KEY'),
        os.getenv('EXOTEL_API_TOKEN')
    )
    
    data = {
        'From': os.getenv('EXOTEL_NUMBER'),
        'To': to,
        'CallerId': os.getenv('EXOTEL_CALLER_ID'),
        'Url': 'https://your-domain.com/exotel/emergency.xml'
    }
    
    response = requests.post(url, auth=auth, data=data)
    return response.json()
```

---

## 💬 WhatsApp Integration

### Twilio WhatsApp API

**Setup:**
```python
# Same Twilio client as SMS
```

**Implementation:**
```python
# core/whatsapp_service.py
from twilio.rest import Client
import os

client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)

def send_whatsapp(to: str, body: str):
    """Send WhatsApp message via Twilio"""
    # Add 'whatsapp:' prefix
    to_whatsapp = f"whatsapp:{to}"
    from_whatsapp = f"whatsapp:{os.getenv('TWILIO_WHATSAPP_NUMBER')}"
    
    message = client.messages.create(
        body=body,
        from_=from_whatsapp,
        to=to_whatsapp
    )
    
    return {"sid": message.sid, "status": message.status}
```

**WhatsApp Template (for emergency):**
```
🚨 *EMERGENCY ALERT*

{{user_name}} needs help!

📍 Location: {{address}}
🔗 Track: {{tracking_link}}

⏰ {{timestamp}}
```

### Meta WhatsApp Business API

For higher volume and official business account:

**Setup:**
1. Create Meta Business account
2. Get WhatsApp Business API access
3. Configure webhook for delivery status

**Implementation:**
```python
# core/meta_whatsapp.py
import requests
import os

def send_whatsapp_meta(to: str, template_name: str, params: dict):
    """Send WhatsApp via Meta Business API"""
    url = f"https://graph.facebook.com/v18.0/{os.getenv('WHATSAPP_PHONE_ID')}/messages"
    
    headers = {
        "Authorization": f"Bearer {os.getenv('WHATSAPP_ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": v}
                        for v in params.values()
                    ]
                }
            ]
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()
```

---

## 🗺️ Geocoding Integration

### Option 1: Google Maps API (Best accuracy)

**Setup:**
```bash
pip install googlemaps
```

**Configuration:**
```python
# Add to .env
GOOGLE_MAPS_API_KEY=your_api_key
```

**Implementation:**
```python
# Update core/gps_location.py
import googlemaps
import os

gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))

def reverse_geocode(latitude: float, longitude: float) -> Dict:
    """
    Convert GPS to address using Google Maps
    """
    try:
        result = gmaps.reverse_geocode((latitude, longitude))
        
        if not result:
            return {
                "address": f"Location: {latitude:.4f}, {longitude:.4f}",
                "district": "Unknown",
                "state": "Unknown",
                "nearest_station": "Call 100 for police"
            }
        
        address_components = result[0]['address_components']
        formatted_address = result[0]['formatted_address']
        
        # Extract district and state
        district = None
        state = None
        
        for component in address_components:
            types = component['types']
            if 'administrative_area_level_2' in types:
                district = component['long_name']
            elif 'administrative_area_level_1' in types:
                state = component['long_name']
        
        return {
            "address": formatted_address,
            "district": district or "Unknown",
            "state": state or "Unknown",
            "nearest_station": find_nearest_police_station(latitude, longitude)
        }
        
    except Exception as e:
        print(f"Geocoding error: {e}")
        return {
            "address": f"Location: {latitude:.4f}, {longitude:.4f}",
            "district": "Unknown",
            "state": "Unknown",
            "nearest_station": "Call 100"
        }

def find_nearest_police_station(lat: float, lon: float) -> str:
    """Find nearest police station using Google Places"""
    try:
        result = gmaps.places_nearby(
            location=(lat, lon),
            radius=5000,  # 5km radius
            keyword="police station"
        )
        
        if result['results']:
            nearest = result['results'][0]
            return nearest['name']
        
        return "Nearest Police Station (call 100)"
        
    except Exception as e:
        return "Call 100 for police"
```

**Find nearby police stations:**
```python
def find_nearby_police_stations(lat: float, lon: float, radius_km: float = 5.0) -> List[Dict]:
    """Get list of nearby police stations"""
    try:
        result = gmaps.places_nearby(
            location=(lat, lon),
            radius=int(radius_km * 1000),  # convert to meters
            keyword="police station"
        )
        
        stations = []
        for place in result['results'][:5]:  # top 5
            # Get place details for phone number
            details = gmaps.place(place['place_id'])
            
            # Calculate distance
            place_lat = place['geometry']['location']['lat']
            place_lon = place['geometry']['location']['lng']
            distance = calculate_distance(lat, lon, place_lat, place_lon)
            
            stations.append({
                "name": place['name'],
                "phone": details['result'].get('formatted_phone_number', '100'),
                "address": place.get('vicinity', ''),
                "distance_km": round(distance, 2)
            })
        
        return sorted(stations, key=lambda x: x['distance_km'])
        
    except Exception as e:
        return [{
            "name": "Local Police Station",
            "phone": "100",
            "distance_km": 0,
            "address": "Call 100 for location"
        }]
```

**Pricing:** 
- Geocoding: $5 per 1000 requests
- Places API: $17 per 1000 requests
- Free tier: $200/month credit

### Option 2: MapMyIndia (India-specific)

**Setup:**
```bash
pip install requests
```

**Configuration:**
```python
# Add to .env
MAPMYINDIA_API_KEY=your_api_key
```

**Implementation:**
```python
# Alternative for India-specific needs
import requests

def reverse_geocode_india(latitude: float, longitude: float) -> Dict:
    """
    Reverse geocode using MapMyIndia (more accurate for India)
    """
    url = "https://apis.mapmyindia.com/advancedmaps/v1/{api_key}/rev_geocode"
    
    params = {
        "lat": latitude,
        "lng": longitude
    }
    
    response = requests.get(
        url.format(api_key=os.getenv('MAPMYINDIA_API_KEY')),
        params=params
    )
    
    data = response.json()
    
    # Parse MapMyIndia response
    # (structure varies, check API docs)
    
    return {
        "address": data.get('formatted_address'),
        "district": data.get('district'),
        "state": data.get('state')
    }
```

### Option 3: OpenStreetMap Nominatim (Free)

**Implementation:**
```python
# core/nominatim.py
import requests

def reverse_geocode_osm(latitude: float, longitude: float) -> Dict:
    """
    Free geocoding via OpenStreetMap Nominatim
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    
    params = {
        "lat": latitude,
        "lon": longitude,
        "format": "json",
        "addressdetails": 1
    }
    
    headers = {
        "User-Agent": "SakhiBot/1.0"  # Required by Nominatim
    }
    
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    
    address = data.get('display_name', '')
    address_parts = data.get('address', {})
    
    return {
        "address": address,
        "district": address_parts.get('state_district', 'Unknown'),
        "state": address_parts.get('state', 'Unknown'),
        "nearest_station": "Call 100 for police"
    }
```

**Limitations:**
- Must include User-Agent header
- Rate limited to 1 request/second
- Less accurate for police stations

---

## 🔐 Environment Variables Summary

Create `.env` file:

```bash
# SMS Services
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WHATSAPP_NUMBER=+1234567890

# OR India-specific
TEXTLOCAL_API_KEY=your_api_key
TEXTLOCAL_SENDER=SAKHIB

# Voice Calls (optional)
EXOTEL_SID=your_sid
EXOTEL_API_KEY=your_key
EXOTEL_API_TOKEN=your_token
EXOTEL_NUMBER=your_number

# WhatsApp Business API (optional)
WHATSAPP_PHONE_ID=your_phone_id
WHATSAPP_ACCESS_TOKEN=your_token

# Geocoding
GOOGLE_MAPS_API_KEY=your_api_key
# OR
MAPMYINDIA_API_KEY=your_api_key

# Existing
GROQ_API_KEY=your_groq_key
```

---

## 📦 Update Requirements

Add to `requirements.txt`:

```
# Emergency features
twilio==8.10.0
googlemaps==4.10.0
geopy==2.4.1

# Optional: faster async HTTP
httpx==0.25.2
aiohttp==3.9.1
```

---

## 🧪 Testing Integrations

### Test SMS:
```python
# test_integrations.py
from core.sms_service import send_sms

# Send test SMS
result = send_sms(
    to="+919999999999",
    body="Test emergency alert from SakhiBot"
)

print(f"SMS sent: {result}")
```

### Test Geocoding:
```python
from core.gps_location import reverse_geocode

# Test Delhi coordinates
result = reverse_geocode(28.7041, 77.1025)
print(f"Address: {result['address']}")
print(f"District: {result['district']}")
print(f"State: {result['state']}")
```

### Test Full SOS Flow:
```bash
# Run with real APIs
curl -X POST http://localhost:8000/api/emergency/sos \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "latitude": 28.7041,
    "longitude": 77.1025,
    "message": "Real emergency test"
  }'
```

---

## 💰 Cost Estimation

### Monthly costs for 1000 active users:

**SMS (assuming 2 emergencies/user/month):**
- Twilio: 2000 SMS × $0.0079 = ~$16/month
- TextLocal (India): 2000 SMS × ₹0.25 = ₹500/month (~$6)

**Voice Calls (1 call/emergency):**
- Twilio: 1000 calls × $0.013/min = ~$13/month
- Exotel: 1000 calls × ₹0.30/min = ₹300/month (~$4)

**WhatsApp (optional):**
- Meta Business API: Free for first 1000 conversations/month
- Then $0.004-0.04 per conversation

**Geocoding:**
- Google Maps: Free tier ($200 credit/month)
- OpenStreetMap: Free (with usage limits)

**Total estimated cost:** $30-50/month for 1000 users

---

## 🚀 Deployment Checklist

- [ ] Set up Twilio/TextLocal account
- [ ] Configure phone numbers and sender IDs
- [ ] Enable WhatsApp Business API (if using)
- [ ] Get Google Maps API key with Geocoding + Places enabled
- [ ] Add all credentials to `.env`
- [ ] Test each integration individually
- [ ] Test full SOS flow end-to-end
- [ ] Set up monitoring for API failures
- [ ] Configure error alerts (email/Slack)
- [ ] Set up rate limiting
- [ ] Enable API usage tracking

---

## 📞 Support Resources

- **Twilio Docs**: https://www.twilio.com/docs
- **TextLocal Docs**: https://www.textlocal.in/developers
- **Google Maps API**: https://developers.google.com/maps/documentation
- **Exotel Docs**: https://developer.exotel.com

---

**Next:** See `EMERGENCY_FEATURES.md` for complete feature documentation
