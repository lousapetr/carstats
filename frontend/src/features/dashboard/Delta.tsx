/** A change against the previous period, where lower is better (cost,
 *  consumption). Direction is carried by the arrow and a spoken word, not
 *  only by colour.
 */
export function Delta({
  value,
  formatMagnitude,
  vs,
}: {
  value: number | null
  formatMagnitude: (magnitude: number) => string
  vs: string | null
}) {
  if (value === null || vs === null) return null

  const magnitude = formatMagnitude(Math.abs(value))
  if (magnitude === formatMagnitude(0)) {
    return <span>beze změny vs. {vs}</span>
  }

  const up = value > 0
  return (
    <span
      className={
        up ? 'text-red-700 dark:text-red-400' : 'text-green-700 dark:text-green-400'
      }
    >
      <span aria-hidden="true">{up ? '▲' : '▼'}</span>
      <span className="sr-only">{up ? 'nárůst o' : 'pokles o'}</span>{' '}
      {magnitude} vs. {vs}
    </span>
  )
}
