import { useState, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  getArtist,
  getArtistPlaylists,
  getArtistHistory,
  refreshArtist,
  type Artist,
  type PlaylistSummary,
  type SnapshotWithChanges,
} from '../api'
import PlaylistCard from '../components/PlaylistCard'
import SnapshotRow from '../components/SnapshotRow'
import PerformanceChart from '../components/PerformanceChart'
import { FaArrowLeft, FaExternalLinkAlt, FaSync, FaUser, FaMusic, FaHistory, FaSpinner, FaChartLine } from 'react-icons/fa'

type Tab = 'playlists' | 'history' | 'performance'

export default function ArtistDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [artist, setArtist] = useState<Artist | null>(null)
  const [playlists, setPlaylists] = useState<PlaylistSummary[]>([])
  const [history, setHistory] = useState<SnapshotWithChanges[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [activeTab, setActiveTab] = useState<Tab>('playlists')

  function load() {
    const numId = id ? parseInt(id, 10) : NaN
    if (!id || isNaN(numId)) {
      setError('Invalid artist ID')
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)

    Promise.all([
      getArtist(numId),
      getArtistPlaylists(numId),
      getArtistHistory(numId),
    ])
      .then(([a, pl, h]) => {
        setArtist(a)
        setPlaylists(pl)
        setHistory(h)
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : 'Failed to load')
        setArtist(null)
        setPlaylists([])
        setHistory([])
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [id])

  function handleRefresh() {
    if (!artist) return
    setRefreshing(true)
    setError(null)
    refreshArtist(artist.id)
      .then(load)
      .catch((e) => setError(e instanceof Error ? e.message : 'Refresh failed'))
      .finally(() => setRefreshing(false))
  }

  function formatLastSnapshot(iso: string | undefined): string {
    if (!iso) return '—'
    try {
      return new Date(iso).toLocaleDateString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
    } catch {
      return iso
    }
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex justify-center">
        <div className="flex items-center gap-3 text-slate-600 dark:text-slate-400">
          <FaSpinner className="animate-spin w-6 h-6" />
          <span>Loading artist...</span>
        </div>
      </div>
    )
  }

  if (error && !artist) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
        <Link to="/" className="text-primary-600 dark:text-primary-400 hover:underline inline-flex items-center gap-2">
          <FaArrowLeft /> Back to artists
        </Link>
      </div>
    )
  }

  if (!artist) {
    return null
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back link */}
      <Link
        to="/"
        className="inline-flex items-center gap-2 text-slate-600 dark:text-slate-400 hover:text-primary-600 dark:hover:text-primary-400 mb-6"
      >
        <FaArrowLeft /> Back to artists
      </Link>

      {/* Artist header */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md p-6 border border-slate-200 dark:border-slate-700 mb-6">
        <div className="flex items-center gap-4">
          <div className="flex-shrink-0">
            {artist.image_url ? (
              <img
                src={artist.image_url}
                alt={artist.name}
                className="w-20 h-20 rounded-full object-cover border-2 border-slate-200 dark:border-slate-700"
                onError={(e) => {
                  const target = e.target as HTMLImageElement
                  target.style.display = 'none'
                  const fallback = target.nextElementSibling as HTMLElement
                  if (fallback) fallback.style.display = 'flex'
                }}
              />
            ) : null}
            <div
              className={`w-20 h-20 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center border-2 border-slate-200 dark:border-slate-700 ${artist.image_url ? 'hidden' : ''}`}
            >
              <FaUser className="w-10 h-10 text-slate-400 dark:text-slate-500" />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white truncate">
              {artist.name}
            </h1>
            <a
              href={artist.spotify_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-primary-600 dark:text-primary-400 hover:underline mt-1"
            >
              <FaExternalLinkAlt /> View profile
            </a>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {refreshing ? <FaSpinner className="animate-spin" /> : <FaSync />}
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
        {error && (
          <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="flex flex-wrap gap-6 mb-6">
        <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
          <FaMusic className="w-5 h-5" />
          <span>
            <span className="font-semibold text-slate-900 dark:text-white">{playlists.length}</span>{' '}
            playlist{playlists.length !== 1 ? 's' : ''} (current)
          </span>
        </div>
        <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
          <FaHistory className="w-5 h-5" />
          <span>Last snapshot: {formatLastSnapshot(history[0]?.snapshot_time)}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-4 flex gap-2 border-b border-slate-200 dark:border-slate-700">
        <button
          onClick={() => setActiveTab('playlists')}
          className={`px-4 py-2 font-medium rounded-t-lg transition-colors ${
            activeTab === 'playlists'
              ? 'bg-white dark:bg-slate-800 text-primary-600 dark:text-primary-400 border border-slate-200 dark:border-slate-700 border-b-transparent -mb-px'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
          }`}
        >
          Current Playlists
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2 font-medium rounded-t-lg transition-colors ${
            activeTab === 'history'
              ? 'bg-white dark:bg-slate-800 text-primary-600 dark:text-primary-400 border border-slate-200 dark:border-slate-700 border-b-transparent -mb-px'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
          }`}
        >
          History
        </button>
        <button
          onClick={() => setActiveTab('performance')}
          className={`px-4 py-2 font-medium rounded-t-lg transition-colors ${
            activeTab === 'performance'
              ? 'bg-white dark:bg-slate-800 text-primary-600 dark:text-primary-400 border border-slate-200 dark:border-slate-700 border-b-transparent -mb-px'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
          }`}
        >
          <FaChartLine className="inline mr-1.5" />
          Performance
        </button>
      </div>

      {/* Tab content */}
      {activeTab === 'playlists' && (
        <div>
          {playlists.length === 0 ? (
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm p-12 border border-slate-200 dark:border-slate-700 text-center">
              <FaMusic className="w-12 h-12 mx-auto mb-4 text-slate-400 dark:text-slate-500" />
              <p className="text-slate-600 dark:text-slate-400">
                No playlists in the latest snapshot. Click Refresh to run discovery.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {playlists.map((pl) => (
                <PlaylistCard key={pl.id} playlist={pl} />
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <div className="space-y-3">
          {history.length === 0 ? (
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm p-12 border border-slate-200 dark:border-slate-700 text-center">
              <FaHistory className="w-12 h-12 mx-auto mb-4 text-slate-400 dark:text-slate-500" />
              <p className="text-slate-600 dark:text-slate-400">
                No snapshot history yet. Click Refresh to create the first snapshot.
              </p>
            </div>
          ) : (
            history.map((snap) => <SnapshotRow key={snap.id} snapshot={snap} />)
          )}
        </div>
      )}

      {activeTab === 'performance' && (
        <PerformanceChart history={history} />
      )}
    </div>
  )
}
