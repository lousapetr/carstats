import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/fuel', label: 'Fuel', icon: '⛽' },
  { to: '/maintenance', label: 'Service', icon: '🔧' },
  { to: '/reminders', label: 'Reminders', icon: '🔔' },
]

export function AppShell({ children }: { children: ReactNode }) {
  const { email, logout } = useAuth()

  return (
    <div className="flex min-h-screen flex-col bg-gray-50 dark:bg-gray-900">
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3 dark:border-gray-800 dark:bg-gray-950">
        <span className="text-base font-semibold text-gray-900 dark:text-gray-100">CarStats</span>
        <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
          <span className="hidden sm:inline">{email}</span>
          <button
            onClick={logout}
            className="underline underline-offset-2 hover:text-gray-900 dark:hover:text-gray-100"
          >
            Sign out
          </button>
        </div>
      </header>

      <nav className="hidden border-b border-gray-200 bg-white px-4 sm:flex dark:border-gray-800 dark:bg-gray-950">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `border-b-2 px-4 py-3 text-sm font-medium ${
                isActive
                  ? 'border-gray-900 text-gray-900 dark:border-white dark:text-white'
                  : 'border-transparent text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-4 pb-20 sm:pb-4">{children}</main>

      <nav className="fixed inset-x-0 bottom-0 flex border-t border-gray-200 bg-white sm:hidden dark:border-gray-800 dark:bg-gray-950">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex flex-1 flex-col items-center gap-0.5 py-2 text-xs ${
                isActive ? 'text-gray-900 dark:text-white' : 'text-gray-400'
              }`
            }
          >
            <span className="text-lg">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
