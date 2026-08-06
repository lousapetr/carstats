import type { Currency } from '../types'

export const CURRENCY_CODES = [
  'CZK',
  'EUR',
  'PLN',
  'HUF',
  'GBP',
  'CHF',
  'SEK',
  'NOK',
  'DKK',
  'RON',
] as const satisfies readonly Currency[]

export const CURRENCIES: Currency[] = [...CURRENCY_CODES]

export const CURRENCY_LABELS: Record<Currency, string> = {
  CZK: 'CZK (Kč)',
  EUR: 'EUR (€)',
  PLN: 'PLN (zł)',
  HUF: 'HUF (Ft)',
  GBP: 'GBP (£)',
  CHF: 'CHF',
  SEK: 'SEK (kr)',
  NOK: 'NOK (kr)',
  DKK: 'DKK (kr)',
  RON: 'RON (lei)',
}

export function formatCzk(value: number): string {
  return `${value.toLocaleString('cs-CZ', { maximumFractionDigits: 0 })} Kč`
}
