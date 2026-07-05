import { useEffect, useRef, useState } from 'react'
import sosLocationData from '../data/sosLocations.json'

const HELPLINES = [
  { label: 'Police', number: '100', tone: 'secondary' },
  { label: "Women's Helpline", number: '181', tone: 'secondary' },
  { label: 'NCW Helpline', number: '7827170170', tone: 'secondary' },
]

const SUPPORT_PLACES = [
  {
    key: 'police',
    label: 'Police station directions',
    destination: 'nearest police station',
    searchQuery: 'police station',
  },
  {
    key: 'osc',
    label: 'One Stop Centre women',
    destination: 'nearest One Stop Centre women',
    searchQuery: 'One Stop Centre women',
  },
  {
    key: 'shelter',
    label: 'women shelter home',
    destination: 'nearest women shelter home',
    searchQuery: 'women shelter home',
  },
  {
    key: 'legal',
    label: 'legal aid office',
    destination: 'nearest legal aid office',
    searchQuery: 'legal aid office',
  },
]

const MAX_NEARBY_DISTANCE_KM = 20
const LOOKUP_BOX_DEGREES = 0.08
const POLICE_LOOKUP_RADIUS_METERS = 15000
const LOCAL_DATA_RADIUS_KM = 60

const CATEGORY_BY_KEY = {
  police: 'police',
  osc: 'osc',
  shelter: 'shelter',
  legal: 'legal',
}

function distanceKm(from, to) {
  const earthRadiusKm = 6371
  const toRadians = value => (value * Math.PI) / 180
  const dLat = toRadians(to.lat - from.lat)
  const dLng = toRadians(to.lng - from.lng)
  const lat1 = toRadians(from.lat)
  const lat2 = toRadians(to.lat)

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1) * Math.cos(lat2) *
      Math.sin(dLng / 2) * Math.sin(dLng / 2)

  return earthRadiusKm * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

function overpassCenter(element) {
  if (Number.isFinite(element.lat) && Number.isFinite(element.lon)) {
    return {
      lat: element.lat,
      lng: element.lon,
    }
  }

  if (
    Number.isFinite(element.center?.lat) &&
    Number.isFinite(element.center?.lon)
  ) {
    return {
      lat: element.center.lat,
      lng: element.center.lon,
    }
  }

  return null
}

function readSavedLocation() {
  try {
    const saved = JSON.parse(localStorage.getItem('sakhibot_last_location'))
    if (
      Number.isFinite(saved?.lat) &&
      Number.isFinite(saved?.lng)
    ) {
      return saved
    }
  } catch {
    return null
  }

  return null
}

function findLocalMatch(coords, category) {
  return sosLocationData.locations
    .filter(location => location.category === category)
    .filter(location => Number.isFinite(location.lat) && Number.isFinite(location.lng))
    .map(location => ({
      ...location,
      distance: distanceKm(coords, location),
      source: 'local',
    }))
    .filter(location => location.distance <= LOCAL_DATA_RADIUS_KM)
    .sort((a, b) => a.distance - b.distance)[0]
}

export default function SOSButton() {
  const [open, setOpen] = useState(false)
  const [coords, setCoords] = useState(null)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const [tracking, setTracking] = useState(false)
  const [supportMatches, setSupportMatches] = useState({})
  const [closestSupportKey, setClosestSupportKey] = useState('police')
  const watchIdRef = useRef(null)

  function applyPosition(position) {
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
  }

  function startTracking() {
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
        applyPosition(position)
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
        maximumAge: 10000,
        timeout: 12000,
      }
    )

    watchIdRef.current = navigator.geolocation.watchPosition(
      position => {
        applyPosition(position)
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
        maximumAge: 10000,
        timeout: 15000,
      }
    )
  }

  function stopTracking() {
    if (watchIdRef.current !== null && navigator.geolocation) {
      navigator.geolocation.clearWatch(watchIdRef.current)
      watchIdRef.current = null
    }
    setTracking(false)
  }

  useEffect(() => {
    return () => {
      if (watchIdRef.current !== null && navigator.geolocation) {
        navigator.geolocation.clearWatch(watchIdRef.current)
      }
    }
  }, [])

  useEffect(() => {
    if (!coords) return

    const controller = new AbortController()

    async function findNearestPolice(matches) {
      const query = `
        [out:json][timeout:10];
        (
          node["amenity"="police"](around:${POLICE_LOOKUP_RADIUS_METERS},${coords.lat},${coords.lng});
          way["amenity"="police"](around:${POLICE_LOOKUP_RADIUS_METERS},${coords.lat},${coords.lng});
          relation["amenity"="police"](around:${POLICE_LOOKUP_RADIUS_METERS},${coords.lat},${coords.lng});
        );
        out center tags;
      `

      try {
        const response = await fetch('https://overpass-api.de/api/interpreter', {
          method: 'POST',
          body: query,
          signal: controller.signal,
        })

        if (!response.ok) return

        const data = await response.json()
        const candidates = data.elements
          .map(element => {
            const center = overpassCenter(element)
            if (!center) return null

            return {
              ...center,
              name: element.tags?.name || 'Police station',
            }
          })
          .filter(Boolean)
          .map(result => ({
            ...result,
            distance: distanceKm(coords, result),
          }))
          .filter(result => result.distance <= MAX_NEARBY_DISTANCE_KM)
          .sort((a, b) => a.distance - b.distance)

        if (candidates[0]) {
          matches.police = candidates[0]
        }
      } catch {
        // Use Google Maps fallback when live OSM lookup is unavailable.
      }
    }

    async function findClosestSupport() {
      const viewbox = [
        coords.lng - LOOKUP_BOX_DEGREES,
        coords.lat + LOOKUP_BOX_DEGREES,
        coords.lng + LOOKUP_BOX_DEGREES,
        coords.lat - LOOKUP_BOX_DEGREES,
      ].join(',')

      const matches = {}

      SUPPORT_PLACES.forEach(place => {
        const localMatch = findLocalMatch(coords, CATEGORY_BY_KEY[place.key])
        if (localMatch) {
          matches[place.key] = localMatch
        }
      })

      if (!matches.police) {
        await findNearestPolice(matches)
      }

      await Promise.all(
        SUPPORT_PLACES.filter(place => !matches[place.key]).map(async place => {
          const url = new URL('https://nominatim.openstreetmap.org/search')
          url.searchParams.set('format', 'jsonv2')
          url.searchParams.set('q', place.searchQuery)
          url.searchParams.set('limit', '5')
          url.searchParams.set('bounded', '1')
          url.searchParams.set('countrycodes', 'in')
          url.searchParams.set('viewbox', viewbox)

          try {
            const response = await fetch(url, { signal: controller.signal })
            if (!response.ok) return

            const results = await response.json()
            const candidates = results
              .map(result => ({
                lat: Number(result.lat),
                lng: Number(result.lon),
                name: result.display_name,
              }))
              .filter(result => Number.isFinite(result.lat) && Number.isFinite(result.lng))
              .map(result => ({
                ...result,
                distance: distanceKm(coords, result),
              }))
              .filter(result => result.distance <= MAX_NEARBY_DISTANCE_KM)
              .sort((a, b) => a.distance - b.distance)

            if (candidates[0]) {
              matches[place.key] = candidates[0]
            }
          } catch {
            // Keep the emergency UI usable even if map lookup is unavailable.
          }
        })
      )

      if (controller.signal.aborted) return

      const closest = Object.entries(matches).sort(
        ([, a], [, b]) => a.distance - b.distance
      )[0]

      setSupportMatches(matches)
      setClosestSupportKey(closest?.[0] || 'police')
    }

    findClosestSupport()

    return () => controller.abort()
  }, [coords])

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
    const match = supportMatches[place.key]

    if (coords && match) {
      return `https://www.google.com/maps/dir/?api=1&origin=${coords.lat},${coords.lng}&destination=${match.lat},${match.lng}&travelmode=walking`
    }

    if (coords) {
      return `https://www.google.com/maps/dir/?api=1&origin=${coords.lat},${coords.lng}&destination=${encodeURIComponent(
        `${place.searchQuery} near ${coords.lat},${coords.lng}`
      )}&travelmode=walking`
    }

    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
      `${place.destination} near me`
    )}`
  }

  const policeDirectionsUrl = supportUrl(SUPPORT_PLACES[0])

  return (
    <>
      <button
        type="button"
        onClick={() => {
          setOpen(true)
          startTracking()
        }}
        className="fixed bottom-5 right-5 z-40 flex h-16 w-16 items-center
                   justify-center rounded-full bg-red-600 text-sm font-black
                   text-white shadow-2xl shadow-red-300 ring-4 ring-red-100
                   transition hover:bg-red-700 focus:outline-none
                   focus:ring-4 focus:ring-red-300 sm:h-20 sm:w-20 sm:text-base"
        aria-label="Open SOS emergency help"
      >
        SOS
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-end bg-black/60 p-0
                     sm:items-center sm:justify-center sm:p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="sos-title"
        >
          <div
            className="max-h-[92vh] w-full overflow-y-auto rounded-t-3xl
                       bg-white shadow-2xl sm:max-w-lg sm:rounded-3xl"
          >
            <div className="border-b border-red-100 bg-red-600 px-5 py-4 text-white">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-red-100">
                    Emergency mode
                  </p>
                  <h2 id="sos-title" className="mt-1 text-xl font-bold">
                    Get help now
                  </h2>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    stopTracking()
                    setOpen(false)
                  }}
                  className="rounded-full bg-white/15 px-3 py-1.5 text-sm
                             font-semibold hover:bg-white/25"
                  aria-label="Close SOS panel"
                >
                  Close
                </button>
              </div>
            </div>

            <div className="space-y-5 p-5">
              <div className="space-y-3">
                <a
                  href="tel:112"
                  className="block rounded-2xl bg-red-600 px-5 py-5 text-center
                             text-white shadow-sm hover:bg-red-700"
                >
                  <span className="block text-2xl font-black">Call 112</span>
                  <span className="mt-1 block text-sm font-semibold text-red-100">
                    National emergency response
                  </span>
                </a>

                <a
                  href={policeDirectionsUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="block rounded-2xl border-2 border-red-200 bg-red-50
                             px-5 py-5 text-center text-red-700 hover:bg-red-100"
                >
                  <span className="block text-xl font-black">
                    Nearest police station
                  </span>
                  <span className="mt-1 block text-sm font-semibold">
                    {supportMatches.police
                      ? `${supportMatches.police.distance.toFixed(1)} km away - exact location`
                      : 'Open Google Maps nearby search'}
                  </span>
                </a>
              </div>

              <div className="rounded-2xl border border-gray-200 bg-gray-50 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-bold text-gray-900">
                      Live location
                    </h3>
                    <p className="mt-1 text-xs leading-5 text-gray-500">
                      Share this with a trusted contact or emergency responder.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={startTracking}
                    disabled={tracking}
                    className="shrink-0 rounded-xl bg-white px-3 py-2 text-xs
                               font-bold text-red-600 shadow-sm ring-1
                               ring-red-100 disabled:cursor-wait
                               disabled:text-gray-400"
                  >
                    {tracking ? 'Locating' : 'Refresh'}
                  </button>
                </div>

                {coords ? (
                  <div className="mt-4 space-y-3">
                    <div className="rounded-xl bg-white p-3 text-xs text-gray-600 ring-1 ring-gray-100">
                      <p>
                        Latitude: <span className="font-semibold">{coords.lat.toFixed(6)}</span>
                      </p>
                      <p>
                        Longitude: <span className="font-semibold">{coords.lng.toFixed(6)}</span>
                      </p>
                      <p>
                        Accuracy: about {coords.accuracy} meters
                      </p>
                      <p>Updated: {coords.updatedAt}</p>
                    </div>

                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                      <a
                        href={locationUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="rounded-xl bg-gray-900 px-3 py-2.5 text-center
                                   text-xs font-bold text-white hover:bg-black"
                      >
                        Open map
                      </a>
                      <button
                        type="button"
                        onClick={copyLocation}
                        className="rounded-xl border border-gray-200 bg-white px-3
                                   py-2.5 text-xs font-bold text-gray-700
                                   hover:bg-gray-100"
                      >
                        {copied ? 'Copied' : 'Copy'}
                      </button>
                      <button
                        type="button"
                        onClick={shareLocation}
                        className="rounded-xl border border-gray-200 bg-white px-3
                                   py-2.5 text-xs font-bold text-gray-700
                                   hover:bg-gray-100"
                      >
                        Share
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="mt-4 rounded-xl bg-white p-3 text-xs text-gray-500 ring-1 ring-gray-100">
                    {tracking
                      ? 'Getting your location...'
                      : 'Location has not been captured yet.'}
                  </div>
                )}

                {error && (
                  <p className="mt-3 rounded-xl bg-red-50 px-3 py-2 text-xs font-medium text-red-700">
                    {error}
                  </p>
                )}
              </div>

              <div>
                <h3 className="text-sm font-bold text-gray-900">
                  Nearby emergency support
                </h3>
                <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
                  {SUPPORT_PLACES.map(place => {
                    const isClosest = place.key === closestSupportKey
                    const match = supportMatches[place.key]
                    const hasVerifiedMatch = Boolean(match)

                    return (
                      <a
                        key={place.destination}
                        href={supportUrl(place)}
                        target="_blank"
                        rel="noreferrer"
                        className={
                          isClosest
                            ? 'rounded-xl border border-red-200 bg-red-600 px-3 py-3 text-sm font-bold text-white hover:bg-red-700'
                            : 'rounded-xl border border-emerald-100 bg-emerald-50 px-3 py-3 text-sm font-semibold text-emerald-800 hover:bg-emerald-100'
                        }
                      >
                        <span className="block">{place.label}</span>
                        {hasVerifiedMatch ? (
                          <span
                            className={
                              isClosest
                                ? 'mt-1 block text-[11px] font-semibold text-red-100'
                                : 'mt-1 block text-[11px] font-semibold text-emerald-600'
                            }
                          >
                            {match.distance.toFixed(1)} km away
                            {isClosest ? ' - closest' : ''}
                            {match.source === 'local' ? ' - verified JSON' : ''}
                          </span>
                        ) : (
                          <span
                            className={
                              isClosest
                                ? 'mt-1 block text-[11px] font-semibold text-red-100'
                                : 'mt-1 block text-[11px] font-semibold text-emerald-600'
                            }
                          >
                            Opens nearby map search
                          </span>
                        )}
                      </a>
                    )
                  })}
                </div>
              </div>

              <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                {HELPLINES.map(item => (
                  <a
                    key={item.number}
                    href={`tel:${item.number}`}
                    className="rounded-xl border border-red-100 bg-white px-3
                               py-3 text-center font-bold text-red-700
                               hover:bg-red-50"
                  >
                    <span className="block text-base">{item.number}</span>
                    <span className="mt-1 block text-[11px] font-semibold">
                      {item.label}
                    </span>
                  </a>
                ))}
              </div>

              <p className="text-center text-xs leading-5 text-gray-400">
                If you are in immediate danger, call 112 or 100 first.
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
