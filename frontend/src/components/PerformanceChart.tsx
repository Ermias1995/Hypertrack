import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { SnapshotWithChanges } from '../api'

interface PerformanceChartProps {
  history: SnapshotWithChanges[]
}

function formatAxisDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  } catch {
    return iso
  }
}

export default function PerformanceChart({ history }: PerformanceChartProps) {
  const data = [...history]
    .sort(
      (a, b) =>
        new Date(a.snapshot_time).getTime() - new Date(b.snapshot_time).getTime()
    )
    .map((snap) => ({
      time: snap.snapshot_time,
      dateLabel: formatAxisDate(snap.snapshot_time),
      playlists: snap.total_playlists_found,
      gained: snap.gained_count,
      lost: snap.lost_count,
    }))

  if (data.length === 0) {
    return (
      <div className="h-80 flex items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 text-sm">
        No snapshot data yet. Click Refresh to create snapshots.
      </div>
    )
  }

  const minY = Math.max(0, Math.min(...data.map((d) => d.playlists)) - 1)
  const maxY = Math.max(...data.map((d) => d.playlists)) + 1

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
        Historical Performance
      </h3>
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="fillPlaylists" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="0%"
                  stopColor="rgb(34 197 94)"
                  stopOpacity={0.4}
                />
                <stop
                  offset="100%"
                  stopColor="rgb(34 197 94)"
                  stopOpacity={0.05}
                />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgb(148 163 184 / 0.3)"
              vertical={false}
            />
            <XAxis
              dataKey="dateLabel"
              tick={{ fill: 'rgb(148 163 184)', fontSize: 12 }}
              angle={-35}
              textAnchor="end"
              height={60}
            />
            <YAxis
              domain={[minY, maxY]}
              tick={{ fill: 'rgb(148 163 184)', fontSize: 12 }}
              width={40}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgb(30 41 59)',
                border: '1px solid rgb(71 85 105)',
                borderRadius: '8px',
              }}
              labelStyle={{ color: 'rgb(203 213 225)' }}
              content={({ active, payload, label }) => {
                if (!active || !payload?.length || !label) return null
                const p = payload[0]?.payload
                return (
                  <div className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-sm shadow-lg">
                    <p className="font-medium text-slate-200 mb-1">{label}</p>
                    <p className="text-emerald-400">Playlists: {p?.playlists ?? 0}</p>
                    {(p?.gained ?? 0) > 0 && (
                      <p className="text-emerald-300">Gained: +{p?.gained}</p>
                    )}
                    {(p?.lost ?? 0) > 0 && (
                      <p className="text-red-400">Lost: −{p?.lost}</p>
                    )}
                  </div>
                )
              }}
            />
            <Legend
              wrapperStyle={{ paddingTop: 8 }}
              formatter={() => 'Playlists'}
              iconType="circle"
              iconSize={8}
              iconStyle={{ fill: 'rgb(34 197 94)' }}
            />
            <Area
              type="monotone"
              dataKey="playlists"
              name="playlists"
              stroke="rgb(34 197 94)"
              strokeWidth={2}
              fill="url(#fillPlaylists)"
              dot={{ fill: 'rgb(34 197 94)', strokeWidth: 0, r: 4 }}
              activeDot={{ r: 5, stroke: 'rgb(34 197 94)', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
