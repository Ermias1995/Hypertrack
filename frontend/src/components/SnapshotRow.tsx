import type { SnapshotWithChanges } from '../api'

interface SnapshotRowProps {
  snapshot: SnapshotWithChanges
}

function formatSnapshotTime(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleDateString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    })
  } catch {
    return iso
  }
}

export default function SnapshotRow({ snapshot }: SnapshotRowProps) {
  return (
    <div className="bg-white/90 dark:bg-transparent rounded-2xl shadow-lg dark:shadow-none p-4 border border-slate-200/80 dark:border-slate-800 flex flex-wrap items-center gap-4">
      <div className="text-sm text-slate-600 dark:text-slate-400">
        {formatSnapshotTime(snapshot.snapshot_time)}
      </div>
      <div className="flex items-center gap-2 text-sm">
        <span className="text-slate-900 dark:text-white font-medium">
          {snapshot.total_playlists_found} playlist{snapshot.total_playlists_found !== 1 ? 's' : ''}
        </span>
      </div>
      {snapshot.gained_count > 0 && (
        <span className="px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-200">
          +{snapshot.gained_count} gained
        </span>
      )}
      {snapshot.lost_count > 0 && (
        <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-200">
          −{snapshot.lost_count} lost
        </span>
      )}
    </div>
  )
}
