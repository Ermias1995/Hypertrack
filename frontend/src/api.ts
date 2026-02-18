/**
 * API client for the Hypertrack backend.
 * Uses VITE_API_URL and VITE_API_KEY from .env
 */

const getBaseUrl = () => import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
const getApiKey = () => import.meta.env.VITE_API_KEY || 'your-secret'

// --- Types (match backend schemas) ---

export interface Artist {
  id: number
  spotify_artist_id: string
  name: string
  spotify_url: string
  image_url: string | null
  /** Dashboard summary (from list endpoint) */
  last_snapshot_at?: string | null
  last_playlist_count?: number | null
  last_gained_count?: number | null
  last_lost_count?: number | null
}

export interface PlaylistSummary {
  id: number
  name: string
  playlist_type: string
  tracks_count: number
  total_tracks?: number | null
}

export interface SnapshotWithChanges {
  id: number
  artist_id: number
  snapshot_time: string
  total_playlists_found: number
  playlists_checked_count: number
  discovery_method_used: string | null
  gained_count: number
  lost_count: number
}

export interface ArtistQueryResponse {
  artist: Artist
  snapshot: { id: number; snapshot_time: string; total_playlists_found: number }
  changes: { gained: PlaylistSummary[]; lost: PlaylistSummary[] }
  current_playlists: PlaylistSummary[]
}

// --- Generic fetch helper ---

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${getBaseUrl()}/api${path}`
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'x-api-key': getApiKey(),
    ...(options.headers as object),
  }
  const token = getStoredToken()
  if (token) {
    ;(headers as Record<string, string>)['Authorization'] = `Bearer ${token}`
  }
  const res = await fetch(url, { ...options, headers })
  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))).detail || res.statusText
    throw new Error(err)
  }
  return res.json() as Promise<T>
}

// --- API functions ---

export function getArtists(): Promise<Artist[]> {
  return api<Artist[]>('/artists')
}

export function createFromUrl(url: string): Promise<ArtistQueryResponse> {
  return api<ArtistQueryResponse>('/artists/from-url', {
    method: 'POST',
    body: JSON.stringify({ url: url.trim() }),
  })
}

export function getArtist(id: number): Promise<Artist> {
  return api<Artist>(`/artists/${id}`)
}

export function getArtistPlaylists(id: number): Promise<PlaylistSummary[]> {
  return api<PlaylistSummary[]>(`/artists/${id}/playlists`)
}

export function getArtistHistory(id: number): Promise<SnapshotWithChanges[]> {
  return api<SnapshotWithChanges[]>(`/artists/${id}/history`)
}

export function refreshArtist(id: number): Promise<ArtistQueryResponse> {
  return api<ArtistQueryResponse>(`/artists/${id}/refresh`, { method: 'POST' })
}

// --- Config (music provider) ---

export type MusicProvider = 'spotify' | 'soundcloud'

export interface Config {
  provider: MusicProvider
}

export function getConfig(): Promise<Config> {
  return api<Config>('/config')
}

export function setConfig(provider: MusicProvider): Promise<Config> {
  return api<Config>('/config', {
    method: 'PATCH',
    body: JSON.stringify({ provider }),
  })
}

// --- Auth (no API key; uses Bearer token for /me) ---

const AUTH_TOKEN_KEY = 'hypertrack-auth-token'

export function getStoredToken(): string | null {
  return localStorage.getItem(AUTH_TOKEN_KEY)
}

export function setStoredToken(token: string | null): void {
  if (token) localStorage.setItem(AUTH_TOKEN_KEY, token)
  else localStorage.removeItem(AUTH_TOKEN_KEY)
}

export interface User {
  id: number
  email: string
  is_admin: boolean
  created_at: string
}

export interface AuthToken {
  access_token: string
  token_type: string
  user?: User
}

const AUTH_TIMEOUT_MS = 30000

async function authFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const base = getBaseUrl()
  const url = `${base}/api${path}`
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...(options.headers as object),
  }
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), AUTH_TIMEOUT_MS)
  try {
    const res = await fetch(url, { ...options, headers, signal: controller.signal })
    clearTimeout(timeoutId)
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      const detail = body.detail ?? res.statusText
      const msg = typeof detail === 'string' ? detail : JSON.stringify(detail)
      if (res.status === 404) {
        throw new Error(
          `Auth endpoint not found (404). Backend may need redeploy. Base URL: ${base}`
        )
      }
      throw new Error(msg)
    }
    return res.json() as Promise<T>
  } catch (err) {
    clearTimeout(timeoutId)
    if (err instanceof Error) {
      if (err.name === 'AbortError') {
        const base = getBaseUrl()
        const isLocal = /^https?:\/\/(localhost|127\.0\.0\.1)/.test(base)
        throw new Error(
          isLocal
            ? 'Request timed out. Make sure the backend is running (e.g. uvicorn app.main:app --reload from the backend folder).'
            : 'Request timed out. The server may be slow or unreachable.'
        )
      }
      throw err
    }
    throw err
  }
}

export function signup(email: string, password: string): Promise<AuthToken & { user?: User }> {
  return authFetch<AuthToken & { user?: User }>('/auth/signup', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function login(email: string, password: string): Promise<AuthToken & { user?: User }> {
  return authFetch<AuthToken & { user?: User }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export async function getMe(): Promise<User> {
  const token = getStoredToken()
  if (!token) return Promise.reject(new Error('Not logged in'))
  const url = `${getBaseUrl()}/api/auth/me`
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), AUTH_TIMEOUT_MS)
  try {
    const res = await fetch(url, {
      headers: {
        'Accept': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      signal: controller.signal,
    })
    clearTimeout(timeoutId)
    if (!res.ok) {
      const err = (await res.json().catch(() => ({}))).detail || res.statusText
      throw new Error(typeof err === 'string' ? err : JSON.stringify(err))
    }
    return res.json() as Promise<User>
  } catch (err) {
    clearTimeout(timeoutId)
    if (err instanceof Error && err.name === 'AbortError') {
      const base = getBaseUrl()
      const isLocal = /^https?:\/\/(localhost|127\.0\.0\.1)/.test(base)
      throw new Error(
        isLocal
          ? 'Request timed out. Make sure the backend is running (e.g. uvicorn app.main:app --reload from the backend folder).'
          : 'Request timed out. The server may be slow or unreachable.'
      )
    }
    throw err
  }
}
