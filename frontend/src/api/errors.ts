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

/** The toast text for a failed mutation. 400 and 422 carry a Czech message
 *  from the backend; everything else gets a generic one, since the backend's
 *  other `detail`s (404s, 500s) are English or absent. */
export function mutationErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'Nepodařilo se spojit se serverem. Zkontrolujte připojení a zkuste to znovu.'
  }
  if (error.status === 400 || error.status === 422) return error.message
  if (error.status === 401) return 'Přihlášení vypršelo. Přihlaste se prosím znovu.'
  if (error.status === 404) return 'Záznam už neexistuje. Obnovte prosím stránku.'
  if (error.status === 413) return 'Soubor je příliš velký.'
  return 'Na serveru došlo k chybě. Zkuste to prosím znovu.'
}
