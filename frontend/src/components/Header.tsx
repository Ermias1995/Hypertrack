import Logo from './Logo'
import ThemeToggle from './ThemeToggle'

export default function Header() {
  return (
    <header className="bg-white dark:bg-slate-800 shadow-sm border-b border-slate-200 dark:border-slate-700 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <Logo className="hover:opacity-80 transition-opacity" />
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
