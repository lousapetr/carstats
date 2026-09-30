import { useQuery, useQueryClient } from '@tanstack/react-query'
import { createContext, useContext, type ReactNode } from 'react'
import { authApi } from '../api/auth'
import { ApiError } from '../api/client'

interface AuthContextValue {
  email: string | null
  isPending: boolean
  // /auth/me failed for a reason other than 401 (a 5xx, the network) — shown
  // as an error rather than the login screen, since the session may be fine.
  isError: boolean
  retry: () => void
  login: () => void
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()

  const { data, isPending, isError, refetch } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      try {
        return await authApi.me()
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) return null
        throw err
      }
    },
    // Signed-out is detected by any /api call's 401 (see App.tsx), so there is
    // no need to re-ask on every window focus.
    staleTime: Infinity,
  })

  const login = () => {
    window.location.href = '/auth/login'
  }

  const logout = async () => {
    await authApi.logout()
    await queryClient.invalidateQueries({ queryKey: ['auth', 'me'] })
  }

  return (
    <AuthContext.Provider
      value={{
        email: data?.email ?? null,
        isPending,
        isError: isError && data === undefined,
        retry: () => void refetch(),
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
