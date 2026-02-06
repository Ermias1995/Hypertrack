import { Link } from 'react-router-dom'
import Logo from './Logo'
import ProviderToggle from './ProviderToggle'
import ThemeToggle from './ThemeToggle'
import { useAuth } from '../contexts/AuthContext'

export default function Header() {
  const { user, token, logout } = useAuth()

  return (
    <header className="bg-white/95 dark:bg-transparent dark:backdrop-blur-none shadow-sm border-b border-slate-200 dark:border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between gap-4">
          <Logo className="hover:opacity-80 transition-opacity shrink-0" />
          <div className="flex items-center gap-3">
            {token && user ? (
              <>
                <span className="text-sm text-slate-600 dark:text-slate-400 truncate max-w-[180px]" title={user.email}>
                  {user.email}
                </span>
                <button
                  type="button"
                  onClick={logout}
                  className="text-sm text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-sm text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400">
                  Log in
                </Link>
                <Link to="/signup" className="text-sm text-emerald-600 dark:text-emerald-400 hover:underline font-medium">
                  Sign up
                </Link>
              </>
            )}
            <ProviderToggle />
            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  )
}
