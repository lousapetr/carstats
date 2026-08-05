import { useAuth } from './AuthContext'

export function LoginScreen() {
  const { login } = useAuth()

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 dark:bg-gray-900">
      <div className="w-full max-w-sm rounded-xl border border-gray-200 bg-white p-8 text-center shadow-sm dark:border-gray-800 dark:bg-gray-950">
        <h1 className="mb-2 text-xl font-semibold text-gray-900 dark:text-gray-100">CarStats</h1>
        <p className="mb-6 text-sm text-gray-500 dark:text-gray-400">
          Sign in to log fill-ups, maintenance, and see your dashboard.
        </p>
        <button
          onClick={login}
          className="w-full rounded-lg bg-gray-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-gray-700 dark:bg-white dark:text-gray-900 dark:hover:bg-gray-200"
        >
          Sign in with Google
        </button>
      </div>
    </div>
  )
}
