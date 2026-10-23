import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api/client'

// Keep recent results per selected location/crop. Live data is never silently
// replaced by seeded demo weather: if both providers fail, the UI gets an error.
export const CLIENT_CACHE_TTL_MS = 5 * 60 * 1000
const cache = new Map()
const inflight = new Map()
const ATTRIBUTION = {
  provider: 'Open-Meteo',
  url: 'https://open-meteo.com/',
  license: 'CC BY 4.0',
  current_note: 'Current conditions are model-based for the surrounding grid cell.',
}
const conditionForCode = (code) => {
  const n = Number(code)
  if (n === 0) return 'Clear sky'
  if (n === 1) return 'Mainly clear'
  if (n === 2) return 'Partly cloudy'
  if (n === 3) return 'Overcast'
  if ([45, 48].includes(n)) return 'Fog'
  if ([51, 53, 55].includes(n)) return 'Drizzle'
  if ([56, 57].includes(n)) return 'Freezing drizzle'
  if ([61, 63, 65].includes(n)) return 'Rain'
  if ([66, 67].includes(n)) return 'Freezing rain'
  if ([71, 73, 75, 77, 85, 86].includes(n)) return 'Snow'
  if ([80, 81, 82].includes(n)) return 'Rain showers'
  if ([95, 96, 99].includes(n)) return 'Thunderstorm'
  return 'Unknown'
}

export function weatherCacheKey(loc, crop, stage) {
  if (!loc) return null
  return [loc.latitude.toFixed(2), loc.longitude.toFixed(2), crop || '', stage || ''].join('|')
}

export function clearWeatherClientCache() {
  cache.clear()
  inflight.clear()
}

async function fetchDirectLiveWeather(loc, signal) {
  const params = new URLSearchParams({
    latitude: String(loc.latitude),
    longitude: String(loc.longitude),
    current: 'temperature_2m,apparent_temperature,relative_humidity_2m,is_day,precipitation,weather_code,cloud_cover,pressure_msl,wind_speed_10m,wind_direction_10m,wind_gusts_10m',
    hourly: 'temperature_2m,apparent_temperature,relative_humidity_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m,wind_gusts_10m',
    daily: 'weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,wind_speed_10m_max,wind_gusts_10m_max,sunrise,sunset',
    temperature_unit: 'celsius',
    wind_speed_unit: 'kmh',
    precipitation_unit: 'mm',
    timezone: 'auto',
    forecast_days: '7',
  })
  const response = await fetch('https://api.open-meteo.com/v1/forecast?' + params.toString(), { signal })
  if (!response.ok) throw new Error('Live weather provider returned HTTP ' + response.status)
  const raw = await response.json()
  if (!raw.current || !raw.daily || !Array.isArray(raw.daily.time) || !raw.daily.time.length) {
    throw new Error('Live weather provider returned incomplete data')
  }
  const c = raw.current
  const d = raw.daily
  const fetchedAt = new Date().toISOString()
  const forecast = d.time.map((date, i) => ({
    date,
    weather_code: Number(d.weather_code?.[i] ?? -1),
    condition: conditionForCode(d.weather_code?.[i]),
    temp_min: d.temperature_2m_min?.[i] ?? null,
    temp_max: d.temperature_2m_max?.[i] ?? null,
    rainfall_probability: d.precipitation_probability_max?.[i] ?? null,
    rainfall_mm: d.precipitation_sum?.[i] ?? null,
    wind_speed_kmh: d.wind_speed_10m_max?.[i] ?? null,
    wind_gusts_kmh: d.wind_gusts_10m_max?.[i] ?? null,
    sunrise: d.sunrise?.[i] ?? null,
    sunset: d.sunset?.[i] ?? null,
    humidity: null,
  }))
  const h = raw.hourly || {}
  const currentTime = String(c.time || '')
  const currentHour = currentTime.slice(0, 13)
  const hourly = (h.time || []).map((time, i) => ({
    time,
    phase: time.slice(0, 13) < currentHour ? 'past' : time.slice(0, 13) === currentHour ? 'current' : 'future',
    temperature: h.temperature_2m?.[i] ?? null,
    apparent_temperature: h.apparent_temperature?.[i] ?? null,
    humidity: h.relative_humidity_2m?.[i] ?? null,
    rain_probability: h.precipitation_probability?.[i] ?? null,
    rainfall_mm: h.precipitation?.[i] ?? null,
    weather_code: h.weather_code?.[i] ?? null,
    condition: conditionForCode(h.weather_code?.[i]),
    wind_speed_kmh: h.wind_speed_10m?.[i] ?? null,
    wind_gusts_kmh: h.wind_gusts_10m?.[i] ?? null,
  })).filter((row) => row.time >= currentHour && row.time.slice(0, 13) <= addHours(currentHour, 48))
  return {
    status: 'LIVE',
    source: 'Open-Meteo',
    location: { name: loc.name || loc.label, latitude: raw.latitude, longitude: raw.longitude },
    units: { temperature: '°C', wind: 'km/h', precipitation: 'mm', pressure: 'hPa', humidity: '%' },
    attribution: ATTRIBUTION,
    cache: { state: 'live', fetched_at: fetchedAt, age_seconds: 0 },
    fetched_at: fetchedAt,
    utc_offset_seconds: raw.utc_offset_seconds ?? 0,
    timezone: raw.timezone || 'auto',
    current: {
      observed_at: c.time,
      temperature: c.temperature_2m,
      apparent_temperature: c.apparent_temperature ?? null,
      humidity: c.relative_humidity_2m ?? null,
      precipitation_mm: c.precipitation ?? 0,
      rain_mm: c.rain ?? null,
      weather_code: Number(c.weather_code),
      condition: conditionForCode(c.weather_code),
      wind_speed_kmh: c.wind_speed_10m,
      wind_direction_deg: c.wind_direction_10m ?? null,
      wind_gusts_kmh: c.wind_gusts_10m ?? null,
      cloud_cover_pct: c.cloud_cover ?? null,
      pressure_hpa: c.pressure_msl ?? null,
      is_day: c.is_day == null ? null : Boolean(c.is_day),
    },
    hourly,
    forecast,
    // Advisory is intentionally omitted: never calculate farming advice from
    // seeded demo weather when the live provider fallback is being used.
    advisory: null,
  }
}

function addHours(isoHour, count) {
  const date = new Date(isoHour + ':00:00Z')
  date.setUTCHours(date.getUTCHours() + count)
  return date.toISOString().slice(0, 13)
}

async function fetchShared(loc, crop, stage, key, signal) {
  if (inflight.has(key)) return inflight.get(key)
  const p = (async () => {
    let backendError
    try {
      const data = await api.getWeatherByLocation(loc.latitude, loc.longitude, loc.name || loc.label, {
        advisory: true, crop, growthStage: stage, signal,
      })
      if (data?.status !== 'DEMO') {
        cache.set(key, { at: Date.now(), data })
        return data
      }
      // Backend is reachable but only has demo weather. Try the live provider
      // directly before displaying anything; demo numbers are not real weather.
    } catch (error) {
      if (error?.name === 'AbortError' || signal?.aborted) throw error
      backendError = error
    }
    try {
      const live = await fetchDirectLiveWeather(loc, signal)
      cache.set(key, { at: Date.now(), data: live })
      return live
    } catch (error) {
      if (error?.name === 'AbortError' || signal?.aborted) throw error
      throw new Error('Live weather is temporarily unavailable. Please try again. ' + (backendError ? '' : ''))
    }
  })().finally(() => { if (inflight.get(key) === p) inflight.delete(key) })
  inflight.set(key, p)
  if (signal) signal.addEventListener('abort', () => { if (inflight.get(key) === p) inflight.delete(key) }, { once: true })
  return p
}

export function useWeatherData(location, { crop = '', stage = '' } = {}) {
  const [state, setState] = useState({ status: 'idle', data: null, error: null })
  const reqId = useRef(0)
  const abortRef = useRef(null)

  const load = useCallback((force) => {
    if (!location) { setState({ status: 'idle', data: null, error: null }); return }
    const key = weatherCacheKey(location, crop, stage)
    const hit = cache.get(key)
    if (!force && hit && Date.now() - hit.at < CLIENT_CACHE_TTL_MS) {
      setState({ status: 'success', data: hit.data, error: null, fromClientCache: true, key })
      return
    }
    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller
    const id = ++reqId.current
    setState((s) => ({ status: 'loading', data: hit ? hit.data : (s.key === key ? s.data : null), error: null, key }))
    fetchShared(location, crop, stage, key, controller.signal)
      .then((data) => { if (id === reqId.current) setState({ status: 'success', data, error: null, key }) })
      .catch((err) => {
        if (id !== reqId.current || (err && err.name === 'AbortError')) return
        setState((s) => ({ status: 'error', data: s.key === key ? s.data : null, error: err.message || 'Request failed', key }))
      })
  }, [location && location.latitude, location && location.longitude, location && (location.name || location.label), crop, stage])

  useEffect(() => {
    load(false)
    return () => { if (abortRef.current) abortRef.current.abort() }
  }, [load])

  const refresh = useCallback(() => load(true), [load])
  return { ...state, refresh }
}
