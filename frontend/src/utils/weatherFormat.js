// Display helpers for the weather page. Times from the weather API are
// LOCAL TO THE SELECTED LOCATION ("2026-10-19T14:00", no offset), so they are
// formatted by parsing the string, never through `new Date()` -- that would
// silently shift them into the viewer's own timezone.

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const COMPASS = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']

const LOCAL_RE = /^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}))?/

export function parseLocal(iso) {
  const m = LOCAL_RE.exec(iso || '')
  if (!m) return null
  const [, y, mo, d, h, mi] = m
  // Date.UTC just to get the weekday of a calendar date; no timezone involved.
  const wd = new Date(Date.UTC(+y, +mo - 1, +d)).getUTCDay()
  return { year: +y, month: +mo, day: +d, hour: h == null ? null : +h, minute: mi == null ? null : +mi, weekday: wd }
}

export function formatHour(iso) {
  const p = parseLocal(iso)
  if (!p || p.hour == null) return '—'
  const h12 = p.hour % 12 === 0 ? 12 : p.hour % 12
  return `${h12} ${p.hour < 12 ? 'AM' : 'PM'}`
}

export function formatClock(iso) {
  const p = parseLocal(iso)
  if (!p || p.hour == null) return '—'
  return `${String(p.hour).padStart(2, '0')}:${String(p.minute).padStart(2, '0')}`
}

export function formatDayShort(iso) {
  const p = parseLocal(iso)
  return p ? WEEKDAYS[p.weekday] : '—'
}

export function formatDayLong(iso) {
  const p = parseLocal(iso)
  return p ? `${WEEKDAYS[p.weekday]} ${p.day} ${MONTHS[p.month - 1]}` : '—'
}

/**
 * "Updated" time shown in the LOCATION's own clock: fetched_at is a UTC
 * instant; utcOffsetSeconds comes from the provider for that location.
 */
export function formatUpdatedAt(fetchedAtIso, utcOffsetSeconds) {
  const t = Date.parse(fetchedAtIso || '')
  if (!Number.isFinite(t)) return null
  const shifted = new Date(t + (Number.isFinite(utcOffsetSeconds) ? utcOffsetSeconds : 0) * 1000)
  const hh = String(shifted.getUTCHours()).padStart(2, '0')
  const mm = String(shifted.getUTCMinutes()).padStart(2, '0')
  return `${shifted.getUTCDate()} ${MONTHS[shifted.getUTCMonth()]}, ${hh}:${mm}`
}

// 125 -> {unit:'minutes', value:2}; keeps the wording in i18n (see callers).
export function ageParts(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return null
  if (seconds < 90) return { unit: 'seconds', value: Math.max(0, Math.round(seconds)) }
  if (seconds < 90 * 60) return { unit: 'minutes', value: Math.round(seconds / 60) }
  return { unit: 'hours', value: Math.round(seconds / 3600) }
}

export function compassDirection(deg) {
  if (!Number.isFinite(deg)) return null
  return COMPASS[Math.round(((deg % 360) + 360) % 360 / 22.5) % 16]
}

export function roundOrDash(n, digits = 0) {
  if (n == null || !Number.isFinite(n)) return '—'
  return n.toFixed(digits)
}

// "Bilaspur, Bilaspur, Chhattisgarh" -> short two-line display parts.
export function locationLines(loc) {
  if (!loc) return { title: '', subtitle: '' }
  const title = loc.name || loc.label || ''
  const rest = [loc.admin2, loc.admin1, loc.country].filter((p, i, a) => p && p !== title && a.indexOf(p) === i)
  return { title, subtitle: rest.join(', ') }
}
