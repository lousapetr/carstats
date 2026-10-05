import type { Period, PeriodInfo } from '../types'
import { formatDate } from './dates'

export const DEFAULT_PERIOD: Period = 'all'

const PERIOD_RE = /^(all|ytd|12m|year:[1-9]\d{3}|range:\d{4}-\d{2}-\d{2}\.\.\d{4}-\d{2}-\d{2})$/

/** The period from a URL parameter, falling back to the default for anything
 *  malformed — including a range that ends before it starts. */
export function parsePeriod(value: string | null): Period {
  if (value === null || !PERIOD_RE.test(value)) return DEFAULT_PERIOD
  const range = rangeBounds(value as Period)
  if (range && range.from > range.to) return DEFAULT_PERIOD
  return value as Period
}

export function yearPeriod(year: number): Period {
  return `year:${year}`
}

/** A custom range from two `yyyy-mm-dd` dates, both inclusive. */
export function rangePeriod(from: string, to: string): Period {
  return `range:${from}..${to}`
}

export function rangeBounds(period: Period): { from: string; to: string } | null {
  if (!period.startsWith('range:')) return null
  const [from, to] = period.slice('range:'.length).split('..')
  return { from, to }
}

export function periodLabel(period: Period): string {
  if (period === 'all') return 'Vše'
  if (period === 'ytd') return 'Letos'
  if (period === '12m') return 'Posledních 12 měsíců'
  const range = rangeBounds(period)
  if (range) return `${formatDate(range.from)} – ${formatDate(range.to)}`
  return period.slice('year:'.length)
}

function daysBetween(from: string, to: string): number {
  return Math.round((Date.parse(to) - Date.parse(from)) / 86_400_000) + 1
}

/** What the period is compared against, phrased to follow "vs." — or null for `all`. */
export function previousPeriodLabel(info: PeriodInfo): string | null {
  if (info.previous_start === null || info.previous_end === null) return null
  if (info.key === '12m') return 'předchozích 12 m'
  if (info.key.startsWith('range:')) {
    const days = daysBetween(info.previous_start, info.previous_end)
    if (days === 1) return 'předchozí den'
    if (days <= 4) return `předchozí ${days} dny`
    return `předchozích ${days} dní`
  }
  return info.previous_start.slice(0, 4)
}
