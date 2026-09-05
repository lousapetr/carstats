/** Formats a `yyyy-mm-dd` date string as `dd.mm.yyyy`, the Czech convention used throughout the UI. */
export function formatDate(isoDate: string): string {
  const [year, month, day] = isoDate.split('-')
  return `${day}.${month}.${year}`
}
