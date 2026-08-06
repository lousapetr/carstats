import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth/AuthContext'
import { LoginScreen } from './auth/LoginScreen'
import { DashboardPage } from './features/dashboard/DashboardPage'
import { FuelLogPage } from './features/fuel/FuelLogPage'
import { MaintenanceLogPage } from './features/maintenance/MaintenanceLogPage'
import { RemindersPage } from './features/reminders/RemindersPage'
import { SettingsPage } from './features/settings/SettingsPage'
import { AppShell } from './layout/AppShell'

const queryClient = new QueryClient()

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
      <AuthProvider>
        <AuthGate />
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
