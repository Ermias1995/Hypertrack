import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { getMe, login as apiLogin, setStoredToken, signup as apiSignup, type User } from '../api'

interface AuthContextValue {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  signup: (email: string, password: string) => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('hypertrack-auth-token'))
  const [loading, setLoading] = useState(true)

  const loadUser = useCallback(async () => {
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const u = await getMe()
      setUser(u)
    } catch {
      setStoredToken(null)
      setToken(null)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    loadUser()
  }, [loadUser])

  const login = useCallback(async (email: string, password: string) => {
    const res = await apiLogin(email, password)
    setStoredToken(res.access_token)
    setToken(res.access_token)
    const u = await getMe()
    setUser(u)
  }, [])

  const logout = useCallback(() => {
    setStoredToken(null)
    setToken(null)
    setUser(null)
  }, [])

  const signup = useCallback(async (email: string, password: string) => {
    await apiSignup(email, password)
    await login(email, password)
  }, [login])

  const value: AuthContextValue = { user, token, loading, login, logout, signup }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
