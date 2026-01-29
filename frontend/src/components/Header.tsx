import Logo from './Logo'
import ProviderToggle from './ProviderToggle'
import ThemeToggle from './ThemeToggle'

export default function Header() {
  return (
    <header className="bg-white dark:bg-slate-800 shadow-sm border-b border-slate-200 dark:border-slate-700 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between gap-4">
          <Logo className="hover:opacity-80 transition-opacity shrink-0" />
          <div className="flex items-center gap-3">
            <ProviderToggle />
            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  )
}
