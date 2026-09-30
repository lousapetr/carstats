/** Formats a `yyyy-mm-dd` date string as `dd.mm.yyyy`, the Czech convention used throughout the UI. */
export function formatDate(isoDate: string): string {
  const [year, month, day] = isoDate.split('-')
  return `${day}.${month}.${year}`
}

/** Compact `m/yy` form of a `yyyy-mm-dd` date, for chart axis ticks where the full date won't fit. */
export function formatShortDate(isoDate: string): string {
  const [year, month] = isoDate.split('-')
  return `${Number(month)}/${year.slice(2)}`
}

/** Today as `yyyy-mm-dd` in the browser's local time zone, not UTC. */
export function todayIso(): string {
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}
