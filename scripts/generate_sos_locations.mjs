import fs from 'node:fs/promises'
import path from 'node:path'

const root = path.resolve(import.meta.dirname, '..')
const resourcesPath = path.join(root, 'backend', 'data', 'resources.json')
const outputPath = path.join(root, 'frontend', 'src', 'data', 'sosLocations.json')

const MAX_POLICE_PER_CITY = 8
const POLICE_RADIUS_METERS = 18000

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms))

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

function slugify(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      'User-Agent': 'SakhiBot/1.0 local emergency resource builder',
      ...(options.headers || {}),
    },
  })

  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`)
  }

  return response.json()
}

async function geocode(query) {
  const url = new URL('https://nominatim.openstreetmap.org/search')
  url.searchParams.set('format', 'jsonv2')
  url.searchParams.set('limit', '1')
  url.searchParams.set('countrycodes', 'in')
  url.searchParams.set('q', query)

  await sleep(1100)
  const results = await fetchJson(url)
  const result = results[0]

  if (!result) return null

  const lat = Number(result.lat)
  const lng = Number(result.lon)

  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null

  return {
    lat,
    lng,
    displayName: result.display_name,
  }
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

async function policeNear(city) {
  const query = `
    [out:json][timeout:25];
    (
      node["amenity"="police"](around:${POLICE_RADIUS_METERS},${city.lat},${city.lng});
      way["amenity"="police"](around:${POLICE_RADIUS_METERS},${city.lat},${city.lng});
      relation["amenity"="police"](around:${POLICE_RADIUS_METERS},${city.lat},${city.lng});
    );
    out center tags;
  `

  await sleep(500)
  const data = await fetchJson('https://overpass-api.de/api/interpreter', {
    method: 'POST',
    body: query,
  })

  return data.elements
    .map(element => {
      const center = overpassCenter(element)
      if (!center) return null

      return {
        id: `police-${element.type}-${element.id}`,
        category: 'police',
        name: element.tags?.name || `${city.district} Police Station`,
        address: element.tags?.['addr:full'] || element.tags?.['addr:street'] || city.district,
        phone: element.tags?.phone || '100',
        district: city.district,
        state: city.state,
        lat: Number(center.lat.toFixed(6)),
        lng: Number(center.lng.toFixed(6)),
        source: 'openstreetmap-overpass',
        distanceFromCityKm: Number(distanceKm(city, center).toFixed(2)),
      }
    })
    .filter(Boolean)
    .sort((a, b) => a.distanceFromCityKm - b.distanceFromCityKm)
    .slice(0, MAX_POLICE_PER_CITY)
}

function resourceToLocation(entry, category, geo) {
  return {
    id: `${category}-${slugify(entry.name)}`,
    category,
    name: entry.name,
    address: entry.address,
    phone: entry.phone || '',
    district: entry.district || '',
    state: entry.state || '',
    lat: Number(geo.lat.toFixed(6)),
    lng: Number(geo.lng.toFixed(6)),
    source: geo.source || 'openstreetmap-nominatim',
  }
}

async function main() {
  const resources = JSON.parse(await fs.readFile(resourcesPath, 'utf8'))
  const locations = []

  const resourceGroups = [
    ['one_stop_centres', 'osc'],
    ['shelter_homes', 'shelter'],
    ['legal_aid_offices', 'legal'],
  ]

  for (const [groupKey, category] of resourceGroups) {
    for (const entry of resources[groupKey] || []) {
      if (Number.isFinite(entry.lat) && Number.isFinite(entry.lng)) {
        locations.push(resourceToLocation(entry, category, {
          lat: entry.lat,
          lng: entry.lng,
          source: 'project-resources-json',
        }))
        continue
      }

      const query = `${entry.name}, ${entry.address}, ${entry.district}, ${entry.state}, India`
      try {
        const geo = await geocode(query)
        if (geo) {
          locations.push(resourceToLocation(entry, category, geo))
        } else {
          console.warn(`No geocode result: ${query}`)
        }
      } catch (err) {
        console.warn(`Geocode failed: ${query} (${err.message})`)
      }
    }
  }

  const cityMap = new Map()
  for (const groupKey of ['one_stop_centres', 'shelter_homes', 'legal_aid_offices']) {
    for (const entry of resources[groupKey] || []) {
      if (entry.district && entry.state) {
        cityMap.set(`${entry.district}, ${entry.state}`, {
          district: entry.district,
          state: entry.state,
        })
      }
    }
  }

  for (const city of cityMap.values()) {
    try {
      const geo = await geocode(`${city.district}, ${city.state}, India`)
      if (!geo) continue

      const cityWithCoords = {
        ...city,
        lat: geo.lat,
        lng: geo.lng,
      }

      const police = await policeNear(cityWithCoords)
      locations.push(...police)
      console.log(`Police: ${city.district}, ${city.state} -> ${police.length}`)
    } catch (err) {
      console.warn(`Police lookup failed: ${city.district}, ${city.state} (${err.message})`)
    }
  }

  const seen = new Set()
  const uniqueLocations = locations.filter(location => {
    const key = `${location.category}:${location.name}:${location.lat}:${location.lng}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })

  uniqueLocations.sort((a, b) =>
    a.state.localeCompare(b.state) ||
    a.district.localeCompare(b.district) ||
    a.category.localeCompare(b.category) ||
    a.name.localeCompare(b.name)
  )

  const output = {
    country: 'India',
    generatedAt: new Date().toISOString(),
    note: 'Starter emergency-location dataset generated from project resources and OpenStreetMap. Verify entries before production use.',
    locations: uniqueLocations,
  }

  await fs.writeFile(outputPath, `${JSON.stringify(output, null, 2)}\n`)
  console.log(`Wrote ${uniqueLocations.length} locations to ${outputPath}`)
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
