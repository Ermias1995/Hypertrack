import { Link } from 'react-router-dom'
import { FaExternalLinkAlt, FaSync, FaMusic, FaUser } from 'react-icons/fa'
import type { Artist } from '../api'

interface ArtistCardProps {
  artist: Artist
  onRefresh: (artist: Artist) => void
  isRefreshing: boolean
}

export default function ArtistCard({ artist, onRefresh, isRefreshing }: ArtistCardProps) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 p-6 border border-slate-200 dark:border-slate-700">
      <div className="flex items-start gap-4 mb-4">
        {/* Artist Image */}
        <div className="flex-shrink-0">
          {artist.image_url ? (
            <img
              src={artist.image_url}
              alt={artist.name}
              className="w-16 h-16 rounded-full object-cover border-2 border-slate-200 dark:border-slate-700"
              onError={(e) => {
                // Fallback to icon if image fails to load
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

        {/* Artist Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <Link
              to={`/artist/${artist.id}`}
              className="text-xl font-semibold text-slate-900 dark:text-white hover:text-primary-600 dark:hover:text-primary-400 transition-colors block truncate"
            >
              {artist.name}
            </Link>
            <button
              onClick={() => onRefresh(artist)}
              disabled={isRefreshing}
              className="p-2 text-slate-600 dark:text-slate-400 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
              title="Refresh playlists"
            >
              <FaSync className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>
      
      <div className="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
        <a
          href={artist.spotify_url}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1.5 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
        >
          <FaExternalLinkAlt className="text-xs" />
          <span>View Profile</span>
        </a>
        <div className="flex items-center gap-1.5">
          <FaMusic className="text-xs" />
          <span>Tracked</span>
        </div>
      </div>
    </div>
  )
}
