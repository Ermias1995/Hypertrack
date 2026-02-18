import { Link } from 'react-router-dom'
import { FaExternalLinkAlt, FaSync, FaMusic, FaUser, FaClock } from 'react-icons/fa'
import type { Artist } from '../api'

function formatLastChecked(iso: string | null | undefined): string {
  if (!iso) return 'Never'
  try {
    const d = new Date(iso)
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return d.toLocaleDateString(undefined, { dateStyle: 'short' })
  } catch {
    return '—'
  }
}

interface ArtistCardProps {
  artist: Artist
  onRefresh: (artist: Artist) => void
  isRefreshing: boolean
}

export default function ArtistCard({ artist, onRefresh, isRefreshing }: ArtistCardProps) {
  const hasSummary =
    artist.last_playlist_count != null ||
    artist.last_snapshot_at != null ||
    (artist.last_gained_count != null && artist.last_gained_count > 0) ||
    (artist.last_lost_count != null && artist.last_lost_count > 0)

  return (
    <div className="bg-white/90 dark:bg-transparent rounded-2xl shadow-lg dark:shadow-none hover:shadow-xl dark:hover:shadow-none p-6 border border-slate-200/80 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 transition-all duration-300">
      <div className="flex items-start gap-4 mb-4">
        {/* Artist image */}
        <div className="flex-shrink-0">
          {artist.image_url ? (
            <img
              src={artist.image_url}
              alt={artist.name}
              className="w-16 h-16 rounded-full object-cover border-2 border-slate-200 dark:border-slate-700"
              onError={(e) => {
                const target = e.target as HTMLImageElement
                target.style.display = 'none'
                const fallback = target.nextElementSibling as HTMLElement
                if (fallback) fallback.style.display = 'flex'
              }}
            />
          ) : null}
          <div
            className={`w-16 h-16 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center border-2 border-slate-200 dark:border-slate-700 ${artist.image_url ? 'hidden' : ''}`}
          >
            <FaUser className="w-8 h-8 text-slate-400 dark:text-slate-500" />
          </div>
        </div>

        {/* Artist info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <Link
              to={`/artist/${artist.id}`}
              className="text-xl font-semibold text-slate-900 dark:text-white hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors block truncate"
            >
              {artist.name}
            </Link>
            <button
              onClick={() => onRefresh(artist)}
              disabled={isRefreshing}
              className="p-2 text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
              title="Refresh playlists"
            >
              <FaSync className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Summary: playlists, last checked, gained/lost */}
      {hasSummary && (
        <div className="mb-4 space-y-2">
          <div className="flex flex-wrap items-center gap-3 text-sm text-slate-600 dark:text-slate-400">
            {artist.last_playlist_count != null && (
              <span className="flex items-center gap-1.5">
                <FaMusic className="text-xs text-slate-500" />
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  {artist.last_playlist_count}
                </span>
                <span>playlist{artist.last_playlist_count !== 1 ? 's' : ''}</span>
              </span>
            )}
            <span className="flex items-center gap-1.5" title={artist.last_snapshot_at ?? undefined}>
              <FaClock className="text-xs text-slate-500" />
              {formatLastChecked(artist.last_snapshot_at)}
            </span>
          </div>
          {((artist.last_gained_count != null && artist.last_gained_count > 0) ||
            (artist.last_lost_count != null && artist.last_lost_count > 0)) && (
            <div className="flex flex-wrap gap-2">
              {artist.last_gained_count != null && artist.last_gained_count > 0 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-200">
                  +{artist.last_gained_count} gained
                </span>
              )}
              {artist.last_lost_count != null && artist.last_lost_count > 0 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-200">
                  −{artist.last_lost_count} lost
                </span>
              )}
            </div>
          )}
        </div>
      )}

      <div className="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800">
        <a
          href={artist.spotify_url}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1.5 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
        >
          <FaExternalLinkAlt className="text-xs" />
          <span>View profile</span>
        </a>
        <Link
          to={`/artist/${artist.id}`}
          className="flex items-center gap-1.5 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
        >
          <span>View details</span>
        </Link>
      </div>
    </div>
  )
}
