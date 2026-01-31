import type { PlaylistSummary } from '../api'

interface PlaylistCardProps {
  playlist: PlaylistSummary
}

function getPlaylistTypeBadgeClass(type: string): string {
  const t = type.toLowerCase()
  if (t === 'editorial') return 'bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200'
  if (t === 'algorithmic') return 'bg-purple-100 dark:bg-purple-900/40 text-purple-800 dark:text-purple-200'
  return 'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200'
}

export default function PlaylistCard({ playlist }: PlaylistCardProps) {
  return (
    <div className="bg-white/90 dark:bg-transparent rounded-2xl shadow-lg dark:shadow-none hover:shadow-xl dark:hover:shadow-none transition-all p-4 border border-slate-200/80 dark:border-slate-800">
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="font-semibold text-slate-900 dark:text-white flex-1 min-w-0 truncate">
          {playlist.name}
        </h3>
        <span
          className={`px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ${getPlaylistTypeBadgeClass(playlist.playlist_type)}`}
        >
          {playlist.playlist_type}
        </span>
      </div>
      <p className="text-sm text-slate-600 dark:text-slate-400">
        {playlist.total_tracks != null
          ? `${playlist.total_tracks} track${playlist.total_tracks !== 1 ? 's' : ''}${playlist.tracks_count > 0 ? ` (${playlist.tracks_count} by artist)` : ''}`
          : `${playlist.tracks_count} track${playlist.tracks_count !== 1 ? 's' : ''} by artist`}
      </p>
    </div>
  )
}
