import { ApiError } from './client'

export function isUnauthorized(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401
}

/** Retry a failed read once, but only when a retry could help: a network
 *  error or a 5xx. A 4xx will fail the same way again. */
export function shouldRetryQuery(failureCount: number, error: unknown): boolean {
  if (failureCount >= 1) return false
  return !(error instanceof ApiError) || error.status >= 500
}

/** The toast text for a failed mutation. A specific message beats a generic
 *  one even when it is in English: the Czech status messages below win where
 *  they exist, then the backend's own `detail` (Czech for 400/422, often
 *  English otherwise), and only a response with no detail at all gets the
 *  generic Czech fallback. */
export function mutationErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'Nepodařilo se spojit se serverem. Zkontrolujte připojení a zkuste to znovu.'
  }
  if (error.status === 401) return 'Přihlášení vypršelo. Přihlaste se prosím znovu.'
  if (error.status === 404) return 'Záznam už neexistuje. Obnovte prosím stránku.'
  if (error.status === 413) return 'Soubor je příliš velký.'
  return error.detail ?? 'Na serveru došlo k chybě. Zkuste to prosím znovu.'
}
