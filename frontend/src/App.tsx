import { MutationCache, QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { ApiError } from './api/client'
import { AuthProvider, useAuth } from './auth/AuthContext'
import { LoginScreen } from './auth/LoginScreen'
import { ToastHost } from './components/ui/ToastHost'
import { DashboardPage } from './features/dashboard/DashboardPage'
import { FuelLogPage } from './features/fuel/FuelLogPage'
import { MaintenanceLogPage } from './features/maintenance/MaintenanceLogPage'
import { RemindersPage } from './features/reminders/RemindersPage'
import { SettingsPage } from './features/settings/SettingsPage'
import { AppShell } from './layout/AppShell'
import { emitErrorToast } from './lib/toastBus'

const queryClient = new QueryClient({
  mutationCache: new MutationCache({
    onError: (error) => {
      if (error instanceof ApiError && error.status === 400) {
        emitErrorToast(error.message)
      }
    },
  }),
})

function AuthGate() {
  const { email, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-gray-400">
        Načítám…
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
      <AuthProvider>
        <AuthGate />
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
