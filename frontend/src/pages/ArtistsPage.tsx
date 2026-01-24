import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getArtists, createFromUrl, refreshArtist, type Artist } from '../api'

export default function ArtistsPage() {
  const [artists, setArtists] = useState<Artist[]>([])
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [adding, setAdding] = useState(false)
  const [refreshingId, setRefreshingId] = useState<number | null>(null)

  function load() {
    setLoading(true)
    setError(null)
    getArtists()
      .then(setArtists)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    const u = url.trim()
    if (!u) return
    setAdding(true)
    setError(null)
    createFromUrl(u)
      .then(() => {
        setUrl('')
        load()
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to add'))
      .finally(() => setAdding(false))
  }

  function handleRefresh(a: Artist) {
    setRefreshingId(a.id)
    setError(null)
    refreshArtist(a.id)
      .then(load)
      .catch((e) => setError(e instanceof Error ? e.message : 'Refresh failed'))
      .finally(() => setRefreshingId(null))
  }

  return (
    <div className="artists-page">
      <h1>Artist Playlist Tracker</h1>

      <form onSubmit={handleAdd} className="add-form">
        <input
          type="url"
          placeholder="Artist URL (SoundCloud or Spotify)"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={adding}
          className="url-input"
        />
        <button type="submit" disabled={adding || !url.trim()}>
          {adding ? 'Adding…' : 'Add artist'}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {loading ? (
        <p>Loading artists…</p>
      ) : artists.length === 0 ? (
        <p>No artists yet. Add one with a SoundCloud or Spotify profile URL above.</p>
      ) : (
        <ul className="artist-list">
          {artists.map((a) => (
            <li key={a.id} className="artist-row">
              <Link to={`/artist/${a.id}`} className="artist-name">
                {a.name}
              </Link>
              <a href={a.spotify_url} target="_blank" rel="noreferrer" className="profile-link">
                Profile
              </a>
              <button
                type="button"
                onClick={() => handleRefresh(a)}
                disabled={refreshingId === a.id}
              >
                {refreshingId === a.id ? 'Refreshing…' : 'Refresh'}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
