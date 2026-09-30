import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { isUnauthorized, mutationErrorMessage, shouldRetryQuery } from './api/errors'
import { AuthProvider, useAuth } from './auth/AuthContext'
import { LoginScreen } from './auth/LoginScreen'
import { ConfirmDialogHost } from './components/ui/ConfirmDialogHost'
import { ErrorState } from './components/ui/ErrorState'
import { ToastHost } from './components/ui/ToastHost'
import { DashboardPage } from './features/dashboard/DashboardPage'
import { FuelLogPage } from './features/fuel/FuelLogPage'
import { MaintenanceLogPage } from './features/maintenance/MaintenanceLogPage'
import { RemindersPage } from './features/reminders/RemindersPage'
import { SettingsPage } from './features/settings/SettingsPage'
import { AppShell } from './layout/AppShell'
import { emitErrorToast } from './lib/toastBus'

// A 401 mid-session means the cookie expired or the address was dropped from
// the allowlist; clearing the cached user sends AuthGate back to the login screen.
function signOutOnUnauthorized(error: unknown) {
  if (isUnauthorized(error)) queryClient.setQueryData(['auth', 'me'], null)
}

// Failed reads render an inline ErrorState with a retry button on their own
// page; failed writes toast, since the form they came from is still on screen.
const queryClient: QueryClient = new QueryClient({
  defaultOptions: { queries: { retry: shouldRetryQuery, staleTime: 30_000 } },
  queryCache: new QueryCache({ onError: signOutOnUnauthorized }),
  mutationCache: new MutationCache({
    onError: (error) => {
      emitErrorToast(mutationErrorMessage(error))
      signOutOnUnauthorized(error)
    },
  }),
})

function AuthGate() {
  const { email, isPending, isError, retry } = useAuth()

  if (isPending) {
    return (
      <div className="flex min-h-screen items-center justify-center text-gray-400">
        Načítám…
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <ErrorState message="Nepodařilo se ověřit přihlášení." onRetry={retry} />
      </div>
    )
  }

  if (!email) {
    return <LoginScreen />
  }

  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/fuel" element={<FuelLogPage />} />
          <Route path="/maintenance" element={<MaintenanceLogPage />} />
          <Route path="/reminders" element={<RemindersPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastHost />
      <ConfirmDialogHost />
      <AuthProvider>
        <AuthGate />
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
