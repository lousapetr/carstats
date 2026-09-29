import { useState } from 'react'
import { useAuth } from './AuthContext'

const LOGIN_ERRORS: Record<string, string> = {
  oauth: 'Přihlášení se nepodařilo dokončit. Zkuste to prosím znovu.',
  'no-email': 'Google nevrátil e-mailovou adresu.',
  unverified: 'Google účet nemá potvrzenou e-mailovou adresu.',
  'not-allowed': 'Tento účet nemá přístup.',
}

// /auth/callback redirects here with ?error=<code> when sign-in fails. The
// parameter is dropped from the URL right away so a reload doesn't replay it.
function takeLoginError(): string | null {
  const code = new URLSearchParams(window.location.search).get('error')
  if (!code) return null
  window.history.replaceState(null, '', window.location.pathname)
  return LOGIN_ERRORS[code] ?? LOGIN_ERRORS.oauth
}

export function LoginScreen() {
  const { login } = useAuth()
  const [error] = useState(takeLoginError)

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 dark:bg-gray-900">
      <div className="w-full max-w-sm rounded-xl border border-gray-200 bg-white p-8 text-center shadow-sm dark:border-gray-800 dark:bg-gray-950">
        <h1 className="mb-2 text-xl font-semibold text-gray-900 dark:text-gray-100">CarStats</h1>
        <p className="mb-6 text-sm text-gray-500 dark:text-gray-400">
          Přihlaste se pro zápis tankování, servisu a zobrazení přehledu.
        </p>
        {error && (
          <p
            role="alert"
            className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300"
          >
            {error}
          </p>
        )}
        <button
          onClick={login}
          className="w-full rounded-lg bg-gray-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-gray-700 dark:bg-white dark:text-gray-900 dark:hover:bg-gray-200"
        >
          Přihlásit se přes Google
        </button>
      </div>
    </div>
  )
}
