# 🚨 Emergency Response Features

## Overview

SakhiBot has been enhanced with life-saving emergency response capabilities, transforming it from an information tool into a comprehensive women's safety platform integrated with India's legal and emergency systems.

---

## 🎯 Implemented Features

### Phase 2: Location & Connectivity ✅

#### 📍 GPS Location Services
- **Real-time location tracking** with accuracy monitoring
- **Reverse geocoding** - converts GPS to human-readable address
- **District/State detection** for jurisdiction-aware responses
- **Nearby police station finder** with contact information
- **Distance calculations** using Haversine formula
- **Location share links** - trackable URLs for guardians

**API Endpoints:**
```
POST /api/emergency/location/share      # Start location sharing
POST /api/emergency/location/update     # Update live location
GET  /api/emergency/location/track/{id} # Track shared location
POST /api/emergency/location/cancel/{id}# Stop sharing
GET  /api/emergency/location/active/{user_id} # Active shares
```

#### 🗺️ Geofencing (Ready for implementation)
- Location share with customizable duration (default 1 hour)
- Emergency shares auto-extend to 2 hours
- Automatic expiration management
- Real-time location updates

---

### Phase 3: Guardian Network ✅

#### 👥 Trusted Contacts System
- Add multiple guardians with **priority levels**
- **Verification system** via SMS confirmation
- **Relationship tracking** (family, friend, neighbor, colleague)
- **Quick setup** for onboarding (add multiple guardians at once)

**Features:**
- Primary/Secondary/Tertiary priority ordering
- Email + phone for each guardian
- Verification status tracking
- Easy add/remove/update

**API Endpoints:**
```
POST   /api/emergency/guardians/add          # Add single guardian
POST   /api/emergency/guardians/quick-setup  # Bulk add during onboarding
GET    /api/emergency/guardians/{user_id}    # List all guardians
POST   /api/emergency/guardians/verify/{id}  # Verify contact
DELETE /api/emergency/guardians/{user_id}/{id} # Remove guardian
```

#### 📧 Multi-Channel Alert System
- **SMS alerts** - immediate text messages
- **WhatsApp messages** - rich formatted alerts
- **Voice calls** - automated emergency calls
- **Email** - detailed incident reports

**Channel Configuration:**
- Configurable priority order
- Enable/disable specific channels
- Fallback cascade (if SMS fails, try WhatsApp, then call)
- Delivery status tracking

**Alert Content Includes:**
- Emergency message
- GPS location with Google Maps link
- Live location tracking URL
- Timestamp and severity level
- Nearby police station info

**API Endpoints:**
```
POST /api/emergency/sos                    # Trigger emergency SOS
GET  /api/emergency/sos/status/{alert_id}  # Check alert delivery
GET  /api/emergency/alerts/{user_id}       # Alert history
POST /api/emergency/preferences            # Set channel preferences
GET  /api/emergency/preferences/{user_id}  # Get preferences
```

---

## 🛡️ Privacy & Legal Compliance

### Consent Management System ✅

Fully compliant with Indian data protection laws:
- **IT Act 2000 Section 43A** - Sensitive data protection
- **DPDP Act 2023** - Digital Personal Data Protection
- **Aadhaar Act** - Identity protection

#### Consent Types:

1. **Emergency Location** (Implied during SOS)
   - GPS coordinates shared during emergency only
   - Not stored after incident resolved
   - Auto-granted when SOS button pressed

2. **Guardian Alerts** (Explicit opt-in)
   - Send alerts to trusted contacts
   - Must be explicitly enabled by user

3. **Police Sharing** (Explicit + Verification)
   - Auto-notify police during critical emergencies
   - Requires user confirmation and understanding

4. **Evidence Recording** (Implicit during emergency)
   - Audio/video recording capability
   - Encrypted storage for 90 days

5. **Government Integration** (Opt-in)
   - Anonymous data sharing with NCW/Women's Commissions
   - For policy improvement and research

6. **Analytics** (Optional)
   - App improvement using anonymized data
   - Can be disabled anytime

**API Endpoints:**
```
GET    /api/consent/policies                    # List all consent types
POST   /api/consent/grant                       # Grant consent
POST   /api/consent/grant-bulk                  # Bulk grant (onboarding)
POST   /api/consent/revoke                      # Revoke consent
GET    /api/consent/check/{user_id}/{type}      # Check specific consent
GET    /api/consent/check-feature/{user_id}/{feature} # Check feature access
GET    /api/consent/list/{user_id}              # List all user consents
GET    /api/consent/export/{user_id}            # Export consent history
DELETE /api/consent/delete-all/{user_id}        # Right to erasure
```

---

## 🚀 SOS Flow

### User Triggers Emergency

```
User presses SOS button
         ↓
Frontend captures GPS location
         ↓
POST /api/emergency/sos
{
  "user_id": "user123",
  "latitude": 28.7041,
  "longitude": 77.1025,
  "accuracy": 10.0,
  "message": "I need help NOW!"
}
```

### Backend Processing

```
1. Create LocationData with reverse geocoding
   - Convert GPS to address
   - Find nearest police station
   
2. Create live location share
   - Generate tracking link
   - Set 2-hour duration
   
3. Send alerts to all verified guardians
   - SMS with location + tracking link
   - WhatsApp with formatted message
   - Fallback to voice call if needed
   
4. Find nearby police stations
   - Within 5km radius
   - Return contact info
   
5. Return emergency numbers
   - 181 (Women's Helpline)
   - 100 (Police)
   - 112 (National Emergency)
```

### Response to Frontend

```json
{
  "status": "alert_sent",
  "alert_id": "a1b2c3d4",
  "guardians_notified": 3,
  "delivery_status": {
    "guardian_1": {"channel": "sms", "status": "sent"},
    "guardian_2": {"channel": "whatsapp", "status": "sent"},
    "guardian_3": {"channel": "call", "status": "initiated"}
  },
  "share_link": "https://sakhibot.app/track/xyz123",
  "location": {
    "latitude": 28.7041,
    "longitude": 77.1025,
    "address": "Connaught Place, New Delhi",
    "district": "New Delhi",
    "state": "Delhi",
    "nearest_station": "Connaught Place Police Station"
  },
  "nearby_police": [
    {
      "name": "Connaught Place Police Station",
      "phone": "100",
      "distance_km": 0.8
    }
  ],
  "emergency_numbers": [
    {"name": "Women's Helpline", "number": "181"},
    {"name": "Police", "number": "100"},
    {"name": "National Emergency", "number": "112"}
  ]
}
```

---

## 📱 Frontend Integration Examples

### 1. Setup Guardian Network (Onboarding)

```javascript
// Quick setup during onboarding
const setupGuardians = async () => {
  const response = await fetch('/api/emergency/guardians/quick-setup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: currentUser.id,
      guardians: [
        {
          name: "Mom",
          phone: "+919876543210",
          email: "mom@example.com",
          relation: "family",
          priority: 1
        },
        {
          name: "Best Friend",
          phone: "+919876543211",
          relation: "friend",
          priority: 2
        },
        {
          name: "Neighbor Aunty",
          phone: "+919876543212",
          relation: "neighbor",
          priority: 3
        }
      ]
    })
  });
  
  const result = await response.json();
  console.log(`Added ${result.guardians_added} guardians`);
};
```

### 2. SOS Button with Location

```javascript
// Emergency SOS trigger
const triggerSOS = async () => {
  // Get user's location
  navigator.geolocation.getCurrentPosition(async (position) => {
    const response = await fetch('/api/emergency/sos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: currentUser.id,
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        message: "Emergency! I need help immediately!"
      })
    });
    
    const result = await response.json();
    
    // Show success message
    alert(`Alert sent to ${result.guardians_notified} guardians`);
    
    // Open tracking link in new tab for user to share
    window.open(result.share_link, '_blank');
    
    // Display nearby police
    showNearbyPolice(result.nearby_police);
  });
};
```

### 3. Live Location Sharing (Non-Emergency)

```javascript
// Share location with guardians (e.g., when traveling alone)
const shareLocation = async (durationMinutes = 60) => {
  navigator.geolocation.getCurrentPosition(async (position) => {
    const response = await fetch('/api/emergency/location/share', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: currentUser.id,
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        duration_minutes: durationMinutes,
        guardian_ids: [] // empty = all guardians
      })
    });
    
    const result = await response.json();
    
    // Start interval to update location every minute
    const shareId = result.share_id;
    const updateInterval = setInterval(() => {
      updateLocationShare(shareId);
    }, 60000); // 60 seconds
    
    // Store interval ID to clear later
    window.locationUpdateInterval = updateInterval;
  });
};

// Update location for active share
const updateLocationShare = (shareId) => {
  navigator.geolocation.getCurrentPosition(async (position) => {
    await fetch('/api/emergency/location/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        share_id: shareId,
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy
      })
    });
  });
};
```

### 4. Consent Management

```javascript
// Grant consents during onboarding
const grantInitialConsents = async () => {
  await fetch('/api/consent/grant-bulk', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: currentUser.id,
      consent_types: [
        'emergency_location',
        'guardian_alerts',
        'analytics'
      ]
    })
  });
};

// Check if feature is allowed
const checkFeatureAccess = async (feature) => {
  const response = await fetch(
    `/api/consent/check-feature/${currentUser.id}/${feature}`
  );
  const result = await response.json();
  
  if (!result.allowed) {
    // Show consent request UI
    showConsentRequest(result.missing_consents);
  }
};
```

---

## 🔒 Security Considerations

### Implemented:
1. **No persistent storage** of sensitive location data
2. **Time-limited shares** with auto-expiration
3. **User-controlled** guardian network
4. **Explicit consent** required for data sharing
5. **Delivery status tracking** for accountability

### To Implement in Production:
1. **Encryption at rest** for stored data
2. **HTTPS only** for all API calls
3. **Rate limiting** to prevent abuse
4. **API authentication** (JWT tokens)
5. **Database instead of in-memory** storage
6. **Redis for session management**
7. **Audit logging** for all emergency actions

---

## 🔌 Third-Party Integrations Needed

### SMS/WhatsApp/Calls:
- **Twilio** (international)
- **TextLocal** (India-specific SMS)
- **Exotel** (India voice calls)
- **Meta WhatsApp Business API**

### Maps/Geocoding:
- **Google Maps API** (geocoding + police stations)
- **MapMyIndia** (India-specific alternative)
- **OpenStreetMap Nominatim** (free alternative)

### Police Integration:
- State Police APIs (where available)
- E-FIR systems
- Women's Police Station databases

### Government:
- **NCW API** (National Commission for Women)
- **State Women's Commission APIs**
- **Shakti/Nirbhaya app integration**

---

## 📊 Database Schema (Production)

### Users Table
```sql
CREATE TABLE users (
  user_id VARCHAR(255) PRIMARY KEY,
  phone VARCHAR(20) UNIQUE,
  email VARCHAR(255),
  created_at TIMESTAMP,
  last_active TIMESTAMP
);
```

### Guardians Table
```sql
CREATE TABLE guardians (
  guardian_id VARCHAR(255) PRIMARY KEY,
  user_id VARCHAR(255) REFERENCES users(user_id),
  name VARCHAR(255),
  phone VARCHAR(20),
  email VARCHAR(255),
  relation VARCHAR(50),
  priority INT,
  verified BOOLEAN DEFAULT FALSE,
  added_at TIMESTAMP,
  INDEX(user_id)
);
```

### Location Shares Table
```sql
CREATE TABLE location_shares (
  share_id VARCHAR(255) PRIMARY KEY,
  user_id VARCHAR(255) REFERENCES users(user_id),
  latitude FLOAT,
  longitude FLOAT,
  accuracy FLOAT,
  address TEXT,
  district VARCHAR(255),
  state VARCHAR(255),
  is_emergency BOOLEAN,
  status VARCHAR(20),
  created_at TIMESTAMP,
  expires_at TIMESTAMP,
  INDEX(user_id),
  INDEX(expires_at)
);
```

### Alerts Table
```sql
CREATE TABLE emergency_alerts (
  alert_id VARCHAR(255) PRIMARY KEY,
  user_id VARCHAR(255) REFERENCES users(user_id),
  message TEXT,
  severity VARCHAR(20),
  location_data JSON,
  share_link VARCHAR(500),
  delivery_status JSON,
  created_at TIMESTAMP,
  INDEX(user_id),
  INDEX(created_at)
);
```

### Consents Table
```sql
CREATE TABLE consents (
  consent_id VARCHAR(255) PRIMARY KEY,
  user_id VARCHAR(255) REFERENCES users(user_id),
  consent_type VARCHAR(50),
  granted BOOLEAN,
  purpose TEXT,
  data_types JSON,
  granted_at TIMESTAMP,
  revoked_at TIMESTAMP,
  expires_at TIMESTAMP,
  INDEX(user_id),
  INDEX(consent_type)
);
```

---

## 🧪 Testing

### Test SOS Flow:
```bash
# 1. Setup guardians
curl -X POST http://localhost:8000/api/emergency/guardians/quick-setup \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "guardians": [
      {"name": "Guardian 1", "phone": "+919999999999", "relation": "family", "priority": 1}
    ]
  }'

# 2. Trigger SOS
curl -X POST http://localhost:8000/api/emergency/sos \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "latitude": 28.7041,
    "longitude": 77.1025,
    "accuracy": 10,
    "message": "Test emergency"
  }'

# 3. Check alert status
curl http://localhost:8000/api/emergency/sos/status/{alert_id}
```

---

## 📈 Next Steps (Future Phases)

### Phase 4: Evidence Collection
- Secure audio/video recording
- Encrypted cloud storage
- Blockchain timestamping for legal validity

### Phase 5: Government Integration
- State police API connections
- NCW data sharing (with consent)
- E-FIR auto-filing

### Phase 6: Post-Emergency Support
- Legal case tracking
- Shelter assistance
- Employment program connections
- Counseling resources

---

## 📞 Support

For technical support or questions:
- **Emergency Issues**: Priority support for safety-critical bugs
- **Feature Requests**: Submit via GitHub issues
- **Integration Help**: Documentation + API examples provided

---

**Built with care for women's safety in India** 🇮🇳
