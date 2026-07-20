/**
 * geoapifyNearby.js
 *
 * Fixes the "returns a farther station instead of the nearest" bug.
 *
 * ROOT CAUSES THIS ADDRESSES:
 *
 * 1. Coordinate order swap — Geoapify's `geometry.coordinates` is GeoJSON
 *    order: [longitude, latitude]. If you destructure that as [lat, lng]
 *    anywhere, every distance calculation is wrong. This file always reads
 *    `properties.lat` / `properties.lon` instead, which are unambiguous.
 *
 * 2. `bias=proximity` is a ranking hint, not a guarantee. Geoapify blends
 *    proximity with relevance/popularity signals, so the array order it
 *    returns is NOT reliably nearest-first. Fix: always compute Haversine
 *    distance yourself and re-sort client-side — for BOTH the Geoapify
 *    results and the local fallback dataset, using one shared function.
 */

const GEOAPIFY_CATEGORIES = {
  police: 'service.police',
  osc: 'service.social_facility', // Indian OSCs aren't a native Geoapify/OSM
  shelter: 'service.social_facility', // category — see caveat below
  legal: 'office.lawyer',
}

// Which source to trust FIRST for each category. Police/legal are well
// covered by Geoapify's underlying OSM data — OSC/shelter mostly aren't,
// so for those two, your own curated dataset is more accurate than
// whatever Geoapify's "social_facility" category happens to return.
const PRIMARY_SOURCE = {
  police: 'local',
  legal: 'geoapify',
  osc: 'local',
  shelter: 'local',
}

// Earth radius in km
const EARTH_RADIUS_KM = 6371

/**
 * Standard Haversine formula.
 * All callers — Geoapify results AND local dataset — go through this single
 * function so distance calculations are always consistent.
 *
 * @param {number} lat1
 * @param {number} lng1
 * @param {number} lat2
 * @param {number} lng2
 * @returns {number} Distance in kilometres
 */
export function haversineKm(lat1, lng1, lat2, lng2) {
  const toRad = (deg) => (deg * Math.PI) / 180
  const dLat = toRad(lat2 - lat1)
  const dLng = toRad(lng2 - lng1)
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return EARTH_RADIUS_KM * c
}

/**
 * Fetches places from Geoapify for one category, returns them ALREADY
 * normalized to {location: {lat, lng}, distance, ...} and STRICTLY re-sorted
 * by real Haversine distance — ignoring whatever order Geoapify sent them in.
 *
 * @param {string} category       - One of: 'police' | 'osc' | 'shelter' | 'legal'
 * @param {number} userLat
 * @param {number} userLng
 * @param {number} [radiusMeters=15000]
 * @returns {Promise<Array>}
 */
export async function fetchNearestFromGeoapify(
  category,
  userLat,
  userLng,
  radiusMeters = 15000
) {
  const apiKey = import.meta.env.VITE_GEOAPIFY_API_KEY
  if (!apiKey) {
    throw new Error('Missing VITE_GEOAPIFY_API_KEY environment variable')
  }

  const geoapifyCategory = GEOAPIFY_CATEGORIES[category]
  if (!geoapifyCategory) {
    throw new Error(`Unknown category: ${category}`)
  }

  const url = new URL('https://api.geoapify.com/v2/places')
  // Geoapify filter/bias params use lng,lat order (GeoJSON convention)
  url.searchParams.set('categories', geoapifyCategory)
  url.searchParams.set('filter', `circle:${userLng},${userLat},${radiusMeters}`)
  url.searchParams.set('bias', `proximity:${userLng},${userLat}`)
  url.searchParams.set('limit', '20') // pull more than 1 — we re-sort ourselves
  url.searchParams.set('apiKey', apiKey)

  const resp = await fetch(url.toString())
  if (!resp.ok) {
    throw new Error(`Geoapify request failed: ${resp.status}`)
  }
  const data = await resp.json()

  const normalized = (data.features || [])
    .map((f) => {
      // Always use properties.lat / properties.lon — never geometry.coordinates
      // because geometry uses GeoJSON [lng, lat] order which is easy to swap.
      const lat = f.properties.lat
      const lng = f.properties.lon
      if (typeof lat !== 'number' || typeof lng !== 'number') return null

      return {
        id: f.properties.place_id,
        name: f.properties.name || f.properties.address_line1,
        address: f.properties.formatted,
        location: { lat, lng },
        category,
        source: 'geoapify',
      }
    })
    .filter(Boolean)
    .map((place) => ({
      ...place,
      distance: haversineKm(userLat, userLng, place.location.lat, place.location.lng),
    }))

  // THE FIX: don't trust Geoapify's array order. Always re-sort by real distance.
  normalized.sort((a, b) => a.distance - b.distance)
  return normalized
}

/**
 * Re-sorts your local fallback dataset the same way as Geoapify results,
 * for consistency. Input entries must have numeric `lat` and `lng` fields.
 *
 * @param {Array}  entries   - Raw rows from sosLocations.json (category already filtered)
 * @param {number} userLat
 * @param {number} userLng
 * @returns {Array}
 */
export function sortLocalByDistance(entries, userLat, userLng) {
  return entries
    .filter((e) => typeof e.lat === 'number' && typeof e.lng === 'number')
    .map((e) => ({
      id: e.id,
      name: e.name,
      address: e.address,
      phone: e.phone || '',
      district: e.district || '',
      state: e.state || '',
      category: e.category,
      source: e.source || 'local',
      location: { lat: e.lat, lng: e.lng },
      distance: haversineKm(userLat, userLng, e.lat, e.lng),
    }))
    .sort((a, b) => a.distance - b.distance)
}

/**
 * Internal helper — filters + sorts the local dataset for one category.
 *
 * @param {string} category
 * @param {number} userLat
 * @param {number} userLng
 * @param {Array}  localDataset
 * @returns {Array}
 */
function localResults(category, userLat, userLng, localDataset) {
  const matches = localDataset.filter((e) => e.category === category)
  return sortLocalByDistance(matches, userLat, userLng)
}

/**
 * Full nearest-lookup for one category. Tries whichever source
 * PRIMARY_SOURCE says to trust first for that category, and only falls
 * back to the other source if the primary one fails or returns nothing.
 *
 * @param {string} category
 * @param {number} userLat
 * @param {number} userLng
 * @param {Array}  localDataset  - Full sosLocations.json `.locations` array
 * @returns {Promise<{results: Array, source: string}>}
 */
export async function findNearest(category, userLat, userLng, localDataset) {
  const primary = PRIMARY_SOURCE[category] || 'geoapify'

  if (primary === 'local') {
    const results = localResults(category, userLat, userLng, localDataset)
    if (results.length > 0) return { results, source: 'local' }

    // Local had nothing usable — only now try Geoapify as a backup.
    try {
      const geoResults = await fetchNearestFromGeoapify(category, userLat, userLng)
      if (geoResults.length > 0) return { results: geoResults, source: 'geoapify-fallback' }
    } catch (err) {
      console.warn(`Geoapify fallback failed for ${category}:`, err.message)
    }
    return { results: [], source: 'none' }
  }

  // primary === 'geoapify'
  try {
    const results = await fetchNearestFromGeoapify(category, userLat, userLng)
    if (results.length > 0) return { results, source: 'geoapify' }
  } catch (err) {
    console.warn(`Geoapify failed for ${category}:`, err.message)
  }

  const results = localResults(category, userLat, userLng, localDataset)
  return { results, source: results.length > 0 ? 'local-fallback' : 'none' }
}

/**
 * Convenience: run all four categories at once, matching your 4-card UI.
 * Returns an object keyed by category name, each value being the result
 * of `findNearest` for that category.
 *
 * @param {number} userLat
 * @param {number} userLng
 * @param {Array}  localDataset
 * @returns {Promise<Object>}  e.g. { police: {results, source}, osc: {...}, ... }
 */
export async function findNearestAllCategories(userLat, userLng, localDataset) {
  const categories = ['police', 'osc', 'shelter', 'legal']
  const entries = await Promise.all(
    categories.map(async (cat) => [
      cat,
      await findNearest(cat, userLat, userLng, localDataset),
    ])
  )
  return Object.fromEntries(entries)
}
