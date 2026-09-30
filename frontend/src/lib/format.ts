import type { Currency } from '../types'

const LOCALE = 'cs-CZ'

const wholeNumber = new Intl.NumberFormat(LOCALE, { maximumFractionDigits: 0 })
const twoDecimals = new Intl.NumberFormat(LOCALE, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})
const upToTwoDecimals = new Intl.NumberFormat(LOCALE, { maximumFractionDigits: 2 })
const consumption = new Intl.NumberFormat(LOCALE, {
  minimumFractionDigits: 1,
  maximumFractionDigits: 2,
})

/** Plain number without a unit, for chart axis ticks. */
export function formatNumber(value: number): string {
  return upToTwoDecimals.format(value)
}

export function formatCzk(value: number): string {
  return `${wholeNumber.format(value)} Kč`
}

/** An amount in the currency it was logged in, e.g. `12,50 EUR`. */
export function formatMoney(amount: number, currency: Currency): string {
  return `${twoDecimals.format(amount)} ${currency}`
}

export function formatPricePerLiter(value: number): string {
  return `${twoDecimals.format(value)} Kč/l`
}

export function formatKm(value: number): string {
  return `${wholeNumber.format(value)} km`
}

export function formatLiters(value: number): string {
  return `${upToTwoDecimals.format(value)} l`
}

export function formatConsumption(value: number | null): string {
  return value !== null ? `${consumption.format(value)} l/100 km` : '—'
}

export function formatCostPerKm(value: number | null): string {
  return value !== null ? `${twoDecimals.format(value)} Kč/km` : '—'
}
