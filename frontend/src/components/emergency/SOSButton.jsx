import { useCallback, useEffect, useRef, useState } from 'react'
import sosLocationData from '../../data/sosLocations.json'
import { findNearestAllCategories } from './geoapifyNearby'
import { triggerSOSAlert } from '../../api'

const HELPLINES = [
  { label: 'Police', number: '100', tone: 'secondary' },
  { label: "Women's Helpline", number: '181', tone: 'secondary' },
  { label: 'NCW Helpline', number: '7827170170', tone: 'secondary' },
]

const SEARCH_CATEGORIES = [
  { key: 'police', label: 'Police Stations', keyword: 'police station', type: 'police' },
  { key: 'osc', label: 'One Stop Centres', keyword: 'One Stop Centre', type: '' },
  { key: 'shelter', label: "Women's Shelters", keyword: "Women's Shelter", type: '' },
  { key: 'legal', label: 'Legal Aid Offices', keyword: 'Legal Aid Office', type: '' },
]

const MOVEMENT_THRESHOLD_METERS = 500

const GOOGLE_API_KEY = import.meta.env.VITE_GOOGLE_API_KEY

// ─── DEV TESTING ONLY ───────────────────────────────────────────────────────
// Set to null to use real GPS. Set to coordinates to force a mock location.
// Change to null when done testing.
const DEV_MOCK_LOCATION = {
  lat: 22.5114,
  lng: 88.4133,
  accuracy: 10,
  updatedAt: 'now (mock: MSIT)',
}
// ────────────────────────────────────────────────────────────────────────────

let googleMapsScriptPromise = null
function loadGoogleMapsScript() {
  if (googleMapsScriptPromise) return googleMapsScriptPromise
  if (!GOOGLE_API_KEY) {
    return Promise.reject(new Error('Missing Google API key'))
  }

  googleMapsScriptPromise = new Promise((resolve, reject) => {
    if (typeof window === 'undefined') {
      reject(new Error('Window is not available'))
      return
    }

    if (window.google?.maps) {
      resolve(window.google)
      return
    }

    const script = document.createElement('script')
    script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_API_KEY}&libraries=places,geometry`
    script.async = true
    script.defer = true
    script.onload = () => {
      if (window.google?.maps) {
        resolve(window.google)
      } else {
        reject(new Error('Google Maps failed to load'))
      }
    }
    script.onerror = () => reject(new Error('Google Maps script failed to load'))
    document.head.appendChild(script)
  })

  return googleMapsScriptPromise
}

function distanceMeters(from, to) {
  // Small helper still needed for movement-threshold check (not nearest-place logic)
  const earthRadiusKm = 6371
  const toRad = (deg) => (deg * Math.PI) / 180
  const dLat = toRad(to.lat - from.lat)
  const dLng = toRad(to.lng - from.lng)
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(from.lat)) * Math.cos(toRad(to.lat)) * Math.sin(dLng / 2) ** 2
  return earthRadiusKm * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)) * 1000
}

function getCategoryForKey(key) {
  switch (key) {
    case 'police':
      return 'Police'
    case 'osc':
      return 'One Stop Centre'
    case 'shelter':
      return "Women's Shelter"
    case 'legal':
      return 'Legal Aid Office'
    default:
      return 'Emergency service'
  }
}

function readSavedLocation() {
  try {
    const saved = JSON.parse(localStorage.getItem('sakhibot_last_location'))
    if (Number.isFinite(saved?.lat) && Number.isFinite(saved?.lng)) {
      return saved
    }
  } catch {
    return null
  }
  return null
}

function createGoogleMapsSearchUrl(coords, destination) {
  return `https://www.google.com/maps/dir/?api=1&origin=${coords.lat},${coords.lng}&destination=${encodeURIComponent(
    destination
  )}&travelmode=driving`
}

export default function SOSButton({ pageMode = false, onBack, forceOpen = false, onForceClose }) {
  const [open, setOpen] = useState(false)
  const [coords, setCoords] = useState(null)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const [tracking, setTracking] = useState(false)
  const [nearbyMatches, setNearbyMatches] = useState({})
  const [closestKey, setClosestKey] = useState('police')
  const [selectedPlace, setSelectedPlace] = useState(null)
  const [routeInfo, setRouteInfo] = useState(null)
  const [mapError, setMapError] = useState('')
  const [alertSent, setAlertSent] = useState(false)
  const [sosSending, setSosSending] = useState(false)
  const [sosSuccess, setSosSuccess] = useState(false)

  const watchIdRef = useRef(null)
  const lastSearchCoordsRef = useRef(null)
  const mapContainerRef = useRef(null)
  const mapRef = useRef(null)
  const markersRef = useRef([])
  const infoWindowRef = useRef(null)
  const directionsRendererRef = useRef(null)

  const updateLocation = useCallback(position => {
    const nextCoords = {
      lat: position.coords.latitude,
      lng: position.coords.longitude,
      accuracy: Math.round(position.coords.accuracy || 0),
      updatedAt: new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      }),
    }

    localStorage.setItem('sakhibot_last_location', JSON.stringify(nextCoords))
    setCoords(nextCoords)
  }, [])

  const hasMovedFarEnough = useCallback((from, to) => {
    if (!from || !to) return true
    return distanceMeters(from, to) >= MOVEMENT_THRESHOLD_METERS
  }, [])

  const ensureMap = useCallback(async () => {
    if (mapRef.current || !mapContainerRef.current) return

    try {
      await loadGoogleMapsScript()
      const google = window.google
      mapRef.current = new google.maps.Map(mapContainerRef.current, {
        center: { lat: coords?.lat || 20.5937, lng: coords?.lng || 78.9629 },
        zoom: 13,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false,
      })
      infoWindowRef.current = new google.maps.InfoWindow()
      directionsRendererRef.current = new google.maps.DirectionsRenderer({
        suppressMarkers: false,
        preserveViewport: true,
      })
      directionsRendererRef.current.setMap(mapRef.current)
    } catch {
      setMapError('Google Map failed to load. Fallback data will still be available.')
    }
  }, [coords])

  function clearMarkers() {
    markersRef.current.forEach(marker => marker.setMap(null))
    markersRef.current = []
  }

  const showMarkers = useCallback(places => {
    clearMarkers()
    if (!mapRef.current || !window.google) return
    const google = window.google
    const bounds = new google.maps.LatLngBounds()

    if (coords) {
      bounds.extend(coords)
      new google.maps.Marker({
        position: coords,
        map: mapRef.current,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 7,
          fillColor: '#0f766e',
          fillOpacity: 1,
          strokeColor: '#ffffff',
          strokeWeight: 2,
        },
        title: 'You are here',
      })
    }

    places.forEach(place => {
      const marker = new google.maps.Marker({
        position: place.location,
        map: mapRef.current,
        title: place.name,
      })

      marker.addListener('click', () => {
        setSelectedPlace(place)
        if (infoWindowRef.current) {
          infoWindowRef.current.setContent(`
            <div style="max-width:220px; font-size:13px; line-height:1.4;">
              <strong>${place.name}</strong><br/>
              <span>${place.address || getCategoryForKey(place.category)}</span><br/>
              <span>${place.distance.toFixed(1)} km away</span>
            </div>
          `)
          infoWindowRef.current.open(mapRef.current, marker)
        }
      })

      markersRef.current.push(marker)
      bounds.extend(place.location)
    })

    if (!bounds.isEmpty()) {
      mapRef.current.fitBounds(bounds, 80)
    }
  }, [coords])

  async function computeRoute(destination) {
    if (!coords || !window.google || !mapRef.current) return null
    setRouteInfo(null)

    try {
      const google = window.google
      const directionsService = new google.maps.DirectionsService()
      const response = await directionsService.route({
        origin: coords,
        destination,
        travelMode: google.maps.TravelMode.DRIVING,
      })

      directionsRendererRef.current?.setDirections(response)
      const leg = response.routes?.[0]?.legs?.[0]
      if (leg) {
        const info = {
          distanceText: leg.distance?.text || '',
          durationText: leg.duration?.text || '',
        }
        setRouteInfo(info)
        return info
      }
    } catch {
      setError('Could not load the route on the map. Opening Google Maps instead.')
    }

    return null
  }

  function openGoogleMapsDirections(place) {
    if (!coords || !place) return '#'
    const destination = `${place.location.lat},${place.location.lng}`
    return createGoogleMapsSearchUrl(coords, destination)
  }

  const refreshNearby = useCallback(async (force = false) => {
    if (!coords) return
    if (!force && lastSearchCoordsRef.current && !hasMovedFarEnough(coords, lastSearchCoordsRef.current)) {
      return
    }

    lastSearchCoordsRef.current = coords
    setMapError('')

    console.log('[SOS] Searching nearby with coords:', coords.lat, coords.lng)

    // findNearestAllCategories handles both Geoapify (with correct coordinate
    // order and client-side re-sort) and the local JSON fallback automatically.
    let categoryResults = {}
    try {
      categoryResults = await findNearestAllCategories(
        coords.lat,
        coords.lng,
        sosLocationData.locations
      )
      console.log('[SOS] Nearest police:', categoryResults.police?.results?.[0]?.name, '—', categoryResults.police?.results?.[0]?.distance?.toFixed(2), 'km')
    } catch (err) {
      console.warn('findNearestAllCategories failed:', err.message)
    }

    // Flatten to the same shape the rest of the component expects:
    // nearbyMatches[key] = the single best result for that category
    const results = {}
    for (const [key, { results: list, source }] of Object.entries(categoryResults)) {
      if (list.length > 0) {
        results[key] = { ...list[0], source }
      }
    }

    if (!Object.keys(results).length) {
      setMapError('No nearby emergency support found. Showing stored locations.')
    }

    setNearbyMatches(results)
    // Always highlight Police first in an SOS — only fall back to another
    // category if no police result was found at all.
    if (results.police) {
      setClosestKey('police')
    } else {
      const closest = Object.entries(results)
        .sort(([, a], [, b]) => a.distance - b.distance)[0]
      setClosestKey(closest?.[0] || 'police')
    }

    // Initialise the visual Google Map (markers only — no Places lookup)
    await ensureMap()
    const nearbyPlaces = Object.values(results)
    if (mapRef.current && nearbyPlaces.length) {
      showMarkers(nearbyPlaces)
    }
  }, [coords, ensureMap, hasMovedFarEnough, showMarkers])

  const startTracking = useCallback(() => {
    // ── DEV MOCK OVERRIDE ──────────────────────────────────────────────────
    if (DEV_MOCK_LOCATION) {
      console.log('[SOS] Using DEV mock location (Ekbalpur):', DEV_MOCK_LOCATION)
      lastSearchCoordsRef.current = null   // force refreshNearby to re-run
      localStorage.removeItem('sakhibot_last_location') // clear stale GPS cache
      setError('')
      setTracking(false)
      setCoords({ ...DEV_MOCK_LOCATION })  // new object reference to trigger useEffect
      return
    }
    // ───────────────────────────────────────────────────────────────────────

    if (!navigator.geolocation) {
      setError('Location is not supported on this device.')
      return
    }

    setError('')
    setTracking(true)

    const savedLocation = readSavedLocation()
    if (savedLocation) {
      setCoords(savedLocation)
    }

    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current)
    }

    navigator.geolocation.getCurrentPosition(
      position => {
        updateLocation(position)
        setTracking(false)
      },
      () => {
        if (!savedLocation) {
          setError(
            'Unable to access location. Please allow location permission and use HTTPS or localhost.'
          )
        }
        setTracking(false)
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    )

    watchIdRef.current = navigator.geolocation.watchPosition(
      position => {
        const nextCoords = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy: Math.round(position.coords.accuracy || 0),
          updatedAt: new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          }),
        }
        localStorage.setItem('sakhibot_last_location', JSON.stringify(nextCoords))
        setCoords(prev => {
          if (!prev || hasMovedFarEnough(prev, nextCoords)) {
            return nextCoords
          }
          return prev
        })
        setTracking(false)
      },
      () => {
        if (!savedLocation) {
          setError(
            'Unable to access location. Please allow location permission and use HTTPS or localhost.'
          )
        }
        setTracking(false)
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    )
  }, [hasMovedFarEnough, updateLocation])

  const stopTracking = useCallback(() => {
    if (watchIdRef.current !== null && navigator.geolocation) {
      navigator.geolocation.clearWatch(watchIdRef.current)
      watchIdRef.current = null
    }
    setTracking(false)
  }, [])

  const closeModal = useCallback(() => {
    setOpen(false)
    stopTracking()
    setAlertSent(false)
    setSosSuccess(false)
    onForceClose?.()
  }, [onForceClose, stopTracking])

  const handleBack = useCallback(() => {
    stopTracking()
    setAlertSent(false)
    setSosSuccess(false)
    onBack?.()
  }, [onBack, stopTracking])

  useEffect(() => {
    if (!pageMode) return

    const init = async () => {
      setAlertSent(false)
      setSosSuccess(false)
      await startTracking()
    }

    void init()

    window.history.pushState({ sakhibotView: 'sos-page' }, '')

    function handlePopState() {
      stopTracking()
      onBack?.()
    }

    window.addEventListener('popstate', handlePopState)

    return () => {
      window.removeEventListener('popstate', handlePopState)
      if (watchIdRef.current !== null && navigator.geolocation) {
        navigator.geolocation.clearWatch(watchIdRef.current)
      }
    }
  }, [pageMode, onBack, startTracking, stopTracking])

  useEffect(() => {
    if (!(open || pageMode)) return
    if (!coords || alertSent || sosSending) return

    console.log('[SOS] Coords available, triggering SOS alert...', coords)

    const sendSOS = async () => {
      setSosSending(true)
      setError('')
      try {
        const result = await triggerSOSAlert({ latitude: coords.lat, longitude: coords.lng })
        console.log('[SOS] Alert sent successfully:', result)
        setSosSuccess(true)
        setAlertSent(true)
      } catch (err) {
        console.error('[SOS] Alert failed:', err.response?.data || err.message)
        setError(err.response?.data?.detail || 'Failed to send SOS alerts to your contacts.')
      } finally {
        setSosSending(false)
      }
    }

    sendSOS()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, pageMode, coords, alertSent])

  useEffect(() => {
    if (pageMode) return

    const init = async () => {
      if (forceOpen) {
        setAlertSent(false)
        setSosSuccess(false)
        setOpen(true)
        await startTracking()
      } else {
        setOpen(false)
      }
    }

    void init()
  }, [forceOpen, pageMode, startTracking])

  useEffect(() => {
    if (pageMode || forceOpen || !open) return

    window.history.pushState({ sakhibotView: 'sos-modal' }, '')

    function handlePopState() {
      stopTracking()
      setOpen(false)
    }

    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [open, pageMode, forceOpen, stopTracking])

  useEffect(() => {
    if (!coords) return
    let active = true

    async function loadNearby() {
      await refreshNearby()
      if (!active) return
    }

    void loadNearby()
    return () => {
      active = false
    }
  }, [coords, refreshNearby])

  async function handleNavigate(place) {
    if (!place) return
    setSelectedPlace(place)
    const route = await computeRoute(place.location)
    if (!route) {
      window.open(openGoogleMapsDirections(place), '_blank')
    }
  }

  const locationUrl = coords
    ? `https://www.google.com/maps?q=${coords.lat},${coords.lng}`
    : ''

  const locationText = coords
    ? `I need help. My current location is ${locationUrl}`
    : 'I need help. Please contact me immediately.'

  const copyLocation = async () => {
    try {
      await navigator.clipboard.writeText(locationText)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 2000)
    } catch {
      setError('Could not copy location. You can open the map link instead.')
    }
  }

  const shareLocation = async () => {
    if (!navigator.share) {
      await copyLocation()
      return
    }

    try {
      await navigator.share({
        title: 'Emergency location',
        text: locationText,
        url: locationUrl || undefined,
      })
    } catch {
      // User cancelled the native share sheet.
    }
  }

  const supportUrl = place => {
    if (!coords) return '#'
    return openGoogleMapsDirections(place)
  }

  function renderPanelBody() {
    const placeList = SEARCH_CATEGORIES.map(search => ({
      ...search,
      match: nearbyMatches[search.key],
    }))

    return (
      <div className="space-y-5 p-5">
        {sosSending && (
          <div className="rounded-xl bg-amber-50 border border-amber-200 px-4 py-3 text-sm font-medium text-amber-800 animate-pulse">
            Sending location alert to emergency contacts...
          </div>
        )}
        {sosSuccess && (
          <div className="rounded-xl bg-green-50 border border-green-200 px-4 py-3 text-sm font-medium text-green-800">
            Emergency alert sent to all your saved contacts!
          </div>
        )}

        <div className="space-y-3">
          <a
            href="tel:112"
            className="block rounded-2xl bg-red-600 px-5 py-5 text-center text-white shadow-sm hover:bg-red-700"
          >
            <span className="block text-2xl font-black">Call 112</span>
            <span className="mt-1 block text-sm font-semibold text-red-100">
              National emergency response
            </span>
          </a>

          <div className="rounded-2xl border border-gray-200 bg-white p-4">
            <div className="grid gap-3 lg:grid-cols-[1.2fr_0.8fr]">
              <div>
                <p className="text-sm font-semibold text-gray-900">Nearest police station</p>
                {nearbyMatches.police ? (
                  <div className="mt-2">
                    <p className="text-sm font-bold text-red-600">{nearbyMatches.police.name}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{nearbyMatches.police.address}</p>
                    <p className="text-[11px] text-gray-400 mt-1">({nearbyMatches.police.distance.toFixed(1)} km away)</p>
                  </div>
                ) : (
                  <p className="mt-1 text-sm text-gray-500">Searching nearby police stations...</p>
                )}
              </div>
              <a
                href={supportUrl(nearbyMatches.police)}
                target="_blank"
                rel="noreferrer"
                className="inline-flex h-fit items-center justify-center rounded-2xl bg-red-50 px-4 py-3 text-sm font-semibold text-red-700 hover:bg-red-100"
              >
                Open directions
              </a>
            </div>
          </div>
        </div>

        {/* <div className="rounded-3xl overflow-hidden border border-gray-200 bg-gray-100">
          <div ref={mapContainerRef} className="h-64 w-full bg-gray-100" />
          {mapError && (
            <div className="p-4 text-xs text-red-600">{mapError}</div>
          )}
        </div> */}

        <div className="rounded-2xl border border-gray-200 bg-gray-50 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold text-gray-900">Live location</h3>
              <p className="mt-1 text-xs leading-5 text-gray-500">
                Share this with a trusted contact or emergency responder.
              </p>
            </div>
            <button
              type="button"
              onClick={() => refreshNearby(true)}
              disabled={tracking}
              className="shrink-0 rounded-xl bg-white px-3 py-2 text-xs font-bold text-red-600 shadow-sm ring-1 ring-red-100 disabled:cursor-wait disabled:text-gray-400"
            >
              {tracking ? 'Locating' : 'Refresh'}
            </button>
          </div>

          {coords ? (
            <div className="mt-4 space-y-3">
              <div className="rounded-xl bg-white p-3 text-xs text-gray-600 ring-1 ring-gray-100">
                <p>Latitude: <span className="font-semibold">{coords.lat.toFixed(6)}</span></p>
                <p>Longitude: <span className="font-semibold">{coords.lng.toFixed(6)}</span></p>
                <p>Accuracy: about {coords.accuracy} meters</p>
                <p>Updated: {coords.updatedAt}</p>
              </div>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                <a
                  href={locationUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-xl bg-gray-900 px-3 py-2.5 text-center text-xs font-bold text-white hover:bg-black"
                >
                  Open map
                </a>
                <button
                  type="button"
                  onClick={copyLocation}
                  className="rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-xs font-bold text-gray-700 hover:bg-gray-100"
                >
                  {copied ? 'Copied' : 'Copy'}
                </button>
                <button
                  type="button"
                  onClick={shareLocation}
                  className="rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-xs font-bold text-gray-700 hover:bg-gray-100"
                >
                  Share
                </button>
              </div>
              <a
                href={`https://api.whatsapp.com/send?text=${encodeURIComponent(locationText)}`}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-center rounded-xl bg-[#25D366] px-4 py-3 text-sm font-bold text-white hover:bg-[#1ebe5d]"
              >
                Share on WhatsApp
              </a>
            </div>
          ) : (
            <div className="mt-4 rounded-xl bg-white p-3 text-xs text-gray-500 ring-1 ring-gray-100">
              {tracking ? 'Getting your location...' : 'Location has not been captured yet.'}
            </div>
          )}

          {error && (
            <p className="mt-3 rounded-xl bg-red-50 px-3 py-2 text-xs font-medium text-red-700">
              {error}
            </p>
          )}
        </div>

        <div>
          <h3 className="text-sm font-bold text-gray-900">Nearby emergency support</h3>
          <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
            {placeList.map(place => {
              const isClosest = place.key === closestKey
              const match = place.match
              return (
                <button
                  key={place.key}
                  type="button"
                  onClick={() => match && handleNavigate(match)}
                  className={
                    isClosest
                      ? 'text-left rounded-xl border border-red-200 bg-red-600 px-4 py-4 text-sm font-bold text-white shadow-sm transition-colors duration-150 hover:bg-red-700'
                      : 'text-left rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-4 text-sm font-semibold text-emerald-700 shadow-sm transition-colors duration-150 hover:bg-emerald-100'
                  }
                >
                  <div className="flex items-center justify-between gap-3">
                    <span>{place.label}</span>
                    {match ? (
                      <span className={isClosest ? 'text-[11px] font-semibold text-white/80' : 'text-[11px] font-semibold text-emerald-700'}>
                        {match.distance.toFixed(1)} km
                      </span>
                    ) : null}
                  </div>
                  <p className={isClosest ? 'mt-1 text-xs text-white/80' : 'mt-1 text-xs text-emerald-700'}>
                    {match ? (match.source === 'local' ? 'Verified from saved data' : 'Google Places result') : 'Tap to search in Google Maps'}
                  </p>
                </button>
              )
            })}
          </div>
        </div>

        {selectedPlace && routeInfo && (
          <div className="rounded-2xl border border-gray-200 bg-white p-4 text-sm text-gray-700">
            <p className="font-semibold">Route to {selectedPlace.name}</p>
            <p className="mt-2">Distance: {routeInfo.distanceText}</p>
            <p>Estimated time: {routeInfo.durationText}</p>
            <a
              href={openGoogleMapsDirections(selectedPlace)}
              target="_blank"
              rel="noreferrer"
              className="mt-3 inline-flex rounded-xl bg-gray-900 px-4 py-2 text-xs font-semibold text-white hover:bg-black"
            >
              Open in Google Maps
            </a>
          </div>
        )}

        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
          {HELPLINES.map(item => (
            <a
              key={item.number}
              href={`tel:${item.number}`}
              className="rounded-xl border border-red-100 bg-white px-3 py-3 text-center font-bold text-red-700 hover:bg-red-50"
            >
              <span className="block text-base">{item.number}</span>
              <span className="mt-1 block text-[11px] font-semibold">{item.label}</span>
            </a>
          ))}
        </div>

        <p className="text-center text-xs leading-5 text-gray-400">
          If you are in immediate danger, call 112 or 100 first.
        </p>
      </div>
    )
  }

  useEffect(() => {
    if (!coords) return

    const init = async () => {
      await ensureMap()
    }

    void init()
  }, [coords, ensureMap])

  useEffect(() => {
    if (!coords) return
    if (open || pageMode) {
      const init = async () => {
        await refreshNearby(true)
      }

      void init()
    }
  }, [open, pageMode, coords, refreshNearby])

  if (pageMode) {
    return (
      <div className="mx-auto w-full max-w-lg px-4 sm:px-6 py-4">
        <div className="rounded-3xl bg-white shadow-xl border border-red-100 overflow-hidden">
          <div className="border-b border-red-100 bg-red-600 px-5 py-5 text-white">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-red-100">
                  Emergency mode
                </p>
                <h2 className="mt-1 text-2xl font-bold">Get help now</h2>
              </div>
              <button
                type="button"
                onClick={handleBack}
                className="shrink-0 rounded-full bg-white/15 px-3 py-1.5 text-sm font-semibold hover:bg-white/25"
                aria-label="Go back"
              >
                ← Back
              </button>
            </div>
          </div>
          {renderPanelBody()}
        </div>
      </div>
    )
  }

  return (
    <>
      <button
        type="button"
        onClick={() => {
          setAlertSent(false)
          setSosSuccess(false)
          setOpen(true)
          startTracking()
        }}
        className="fixed bottom-5 right-5 z-40 flex h-16 w-16 items-center justify-center rounded-full bg-red-600 text-sm font-black text-white shadow-2xl shadow-red-300 ring-4 ring-red-100 transition hover:bg-red-700 focus:outline-none focus:ring-4 focus:ring-red-300 sm:h-20 sm:w-20 sm:text-base"
        aria-label="Open SOS emergency help"
      >
        SOS
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-end bg-black/60 p-0 sm:items-center sm:justify-center sm:p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="sos-title"
        >
          <div className="max-h-[92vh] w-full overflow-y-auto rounded-t-3xl bg-white shadow-2xl sm:max-w-lg sm:rounded-3xl">
            <div className="border-b border-red-100 bg-red-600 px-5 py-4 text-white">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-red-100">
                    Emergency mode
                  </p>
                  <h2 id="sos-title" className="mt-1 text-xl font-bold">Get help now</h2>
                </div>
                <button
                  type="button"
                  onClick={closeModal}
                  className="rounded-full bg-white/15 px-3 py-1.5 text-sm font-semibold hover:bg-white/25"
                  aria-label="Close SOS panel"
                >
                  Close
                </button>
              </div>
            </div>
            {renderPanelBody()}
          </div>
        </div>
      )}
    </>
  )
}