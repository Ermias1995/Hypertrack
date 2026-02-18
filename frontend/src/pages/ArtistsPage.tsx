import { useState, useEffect } from 'react'
import { getArtists, createFromUrl, refreshArtist, type Artist } from '../api'
import ArtistCard from '../components/ArtistCard'
import { FaPlus, FaUsers, FaSpinner, FaMusic } from 'react-icons/fa'

export default function ArtistsPage() {
  const [artists, setArtists] = useState<Artist[]>([])
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
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
    setSuccessMessage(null)
    createFromUrl(u)
      .then((res) => {
        setUrl('')
        setSuccessMessage(
          res.current_playlists.length > 0
            ? `${res.artist.name} added — ${res.current_playlists.length} playlist${res.current_playlists.length !== 1 ? 's' : ''} found`
            : `${res.artist.name} added`
        )
        load()
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to add'))
      .finally(() => setAdding(false))
  }

  function handleRefresh(a: Artist) {
    setRefreshingId(a.id)
    setError(null)
    setSuccessMessage(null)
    refreshArtist(a.id)
      .then((res) => {
        const g = res.changes.gained.length
        const l = res.changes.lost.length
        if (g > 0 || l > 0) {
          setSuccessMessage(`${a.name}: +${g} gained, −${l} lost`)
        } else {
          setSuccessMessage(`${a.name} refreshed — no changes`)
        }
        load()
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Refresh failed'))
      .finally(() => setRefreshingId(null))
  }

  const totalPlaylists = artists.reduce(
    (sum, a) => sum + (a.last_playlist_count ?? 0),
    0
  )

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Dashboard header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
          Dashboard
        </h1>
        <p className="mt-1 text-slate-600 dark:text-slate-400">
          Track playlist placements for your artists. Add a profile URL to discover playlists and see gains and losses over time.
        </p>
      </div>

      {/* Stats bar */}
      <div className="mb-6 flex flex-wrap items-center gap-6">
        <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
          <FaUsers className="w-5 h-5" />
          <span className="text-lg font-semibold">
            <span className="text-slate-900 dark:text-white">{artists.length}</span> Artist{artists.length !== 1 ? 's' : ''}
          </span>
        </div>
        {artists.length > 0 && (
          <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
            <FaMusic className="w-5 h-5" />
            <span className="text-lg font-semibold">
              <span className="text-slate-900 dark:text-white">{totalPlaylists}</span> total playlist placement{totalPlaylists !== 1 ? 's' : ''}
            </span>
          </div>
        )}
      </div>

      {/* Add Artist form */}
      <div className="bg-white/90 dark:bg-transparent rounded-2xl shadow-lg dark:shadow-none p-6 mb-8 border border-slate-200/80 dark:border-slate-800">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">
          Add New Artist
        </h2>
        <form onSubmit={handleAdd} className="flex gap-3">
          <input
            type="url"
            placeholder="Enter SoundCloud or Spotify artist URL..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={adding}
            className="flex-1 px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700/80 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transition-shadow"
          />
          <button
            type="submit"
            disabled={adding || !url.trim()}
            className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-xl shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {adding ? (
              <>
                <FaSpinner className="animate-spin" />
                <span>Adding...</span>
              </>
            ) : (
              <>
                <FaPlus />
                <span>Add Artist</span>
              </>
            )}
          </button>
        </form>
        {error && (
          <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}
        {successMessage && (
          <div className="mt-4 p-3 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg">
            <p className="text-sm text-emerald-800 dark:text-emerald-200">{successMessage}</p>
          </div>
        )}
      </div>

      {/* Artists grid */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="flex items-center gap-3 text-slate-600 dark:text-slate-400">
            <FaSpinner className="animate-spin w-6 h-6" />
            <span className="text-lg">Loading artists...</span>
          </div>
        </div>
      ) : artists.length === 0 ? (
        <div className="bg-white/90 dark:bg-transparent rounded-2xl shadow-lg dark:shadow-none p-12 md:p-16 border border-slate-200/80 dark:border-slate-800 text-center">
          <FaUsers className="w-20 h-20 mx-auto mb-6 text-slate-300 dark:text-slate-600" />
          <h3 className="text-2xl font-semibold text-slate-900 dark:text-white mb-2">
            No artists yet
          </h3>
          <p className="text-slate-600 dark:text-slate-400 max-w-md mx-auto mb-6">
            Add your first artist with a SoundCloud or Spotify profile URL above. We’ll discover playlists they appear on and track gains and losses over time.
          </p>
          <p className="text-sm text-slate-500 dark:text-slate-500">
            Example: https://open.spotify.com/artist/... or https://soundcloud.com/artist-name
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {artists.map((artist) => (
            <ArtistCard
              key={artist.id}
              artist={artist}
              onRefresh={handleRefresh}
              isRefreshing={refreshingId === artist.id}
            />
          ))}
        </div>
      )}
    </div>
  )
}
