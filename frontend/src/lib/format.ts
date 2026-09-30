import type { Currency } from '../types'

const LOCALE = 'cs-CZ'

const wholeNumber = new Intl.NumberFormat(LOCALE, { maximumFractionDigits: 0 })
const twoDecimals = new Intl.NumberFormat(LOCALE, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})
// Pump prices are often quoted to a tenth of a cent (1,659 EUR/l).
const unitPrice = new Intl.NumberFormat(LOCALE, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 3,
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

/** A per-litre price in the currency it was logged in, e.g. `1,659 EUR/l`. */
export function formatMoneyPerLiter(amount: number, currency: Currency): string {
  return `${unitPrice.format(amount)} ${currency}/l`
}

export function formatPricePerLiter(value: number): string {
  return `${unitPrice.format(value)} Kč/l`
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
