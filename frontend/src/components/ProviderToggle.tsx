import { useEffect, useState } from 'react'
import { getConfig, setConfig, type MusicProvider } from '../api'

const PROVIDERS: { value: MusicProvider; label: string }[] = [
  { value: 'spotify', label: 'Spotify' },
  { value: 'soundcloud', label: 'SoundCloud' },
]

export default function ProviderToggle() {
  const [provider, setProvider] = useState<MusicProvider | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getConfig()
      .then((c) => {
        setProvider(c.provider === 'spotify' || c.provider === 'soundcloud' ? c.provider : null)
        setError(null)
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
      .finally(() => setLoading(false))
  }, [])

  const handleSelect = (value: MusicProvider) => {
    if (value === provider) return
    setLoading(true)
    setError(null)
    setConfig(value)
      .then((c) => {
        setProvider(c.provider)
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to switch'))
      .finally(() => setLoading(false))
  }

  if (loading && provider === null) {
    return (
      <div className="h-9 w-48 rounded-lg bg-slate-100 dark:bg-slate-700 animate-pulse" aria-hidden />
    )
  }

  return (
    <div className="flex items-center gap-1">
      <div
        className="inline-flex rounded-lg bg-slate-100 dark:bg-slate-700 p-0.5"
        role="tablist"
        aria-label="Music provider"
      >
        {PROVIDERS.map(({ value, label }) => (
          <button
            key={value}
            type="button"
            role="tab"
            aria-selected={provider === value}
            onClick={() => handleSelect(value)}
            disabled={loading}
            className={`
              rounded-md px-3 py-1.5 text-sm font-medium transition-colors
              ${provider === value
                ? 'bg-white dark:bg-slate-600 text-slate-900 dark:text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
          >
            {label}
          </button>
        ))}
      </div>
      {error && (
        <span className="text-xs text-red-500 dark:text-red-400 max-w-32 truncate" title={error}>
          {error}
        </span>
      )}
    </div>
  )
}
