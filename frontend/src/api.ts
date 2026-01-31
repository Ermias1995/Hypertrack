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
