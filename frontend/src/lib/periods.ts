import type { Period, PeriodInfo } from '../types'

export const DEFAULT_PERIOD: Period = 'all'

const PERIOD_RE = /^(all|ytd|12m|year:[1-9]\d{3})$/

/** The period from a URL parameter, falling back to the default for anything malformed. */
export function parsePeriod(value: string | null): Period {
  return value !== null && PERIOD_RE.test(value) ? (value as Period) : DEFAULT_PERIOD
}

export function yearPeriod(year: number): Period {
  return `year:${year}`
}

export function periodLabel(period: Period): string {
  if (period === 'all') return 'Celá historie'
  if (period === 'ytd') return 'Letos'
  if (period === '12m') return 'Posledních 12 měsíců'
  return period.slice('year:'.length)
}

/** What the period is compared against, phrased to follow "vs." — or null for `all`. */
export function previousPeriodLabel(info: PeriodInfo): string | null {
  if (info.previous_start === null) return null
  if (info.key === '12m') return 'předchozích 12 m'
  return info.previous_start.slice(0, 4)
}
