import { useQuery, useQueryClient } from '@tanstack/react-query'
import { createContext, useContext, type ReactNode } from 'react'
import { authApi } from '../api/auth'
import { ApiError } from '../api/client'

interface AuthContextValue {
  email: string | null
  isLoading: boolean
  login: () => void
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      try {
        return await authApi.me()
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) return null
        throw err
      }
    },
    retry: false,
  })

  const login = () => {
    window.location.href = '/auth/login'
  }

  const logout = async () => {
    await authApi.logout()
    await queryClient.invalidateQueries({ queryKey: ['auth', 'me'] })
  }

  return (
    <AuthContext.Provider value={{ email: data?.email ?? null, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
