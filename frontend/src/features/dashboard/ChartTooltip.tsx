export interface ChartTooltipItem {
  label?: string
  value: string
  color?: string
}

/**
 * Recharts' default tooltip content pads and lines things out generously
 * (10px box padding, 4px above/below each item, plus its own label line even
 * when that would just repeat an item's name) - replacing it here keeps the
 * dashboard's small charts from showing a tooltip taller than the chart itself.
 */
export function ChartTooltip({
  active,
  title,
  items,
}: {
  active?: boolean
  title?: string
  items: ChartTooltipItem[]
}) {
  if (!active || items.length === 0) return null

  return (
    <div className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs leading-tight text-gray-900 shadow-sm dark:border-gray-800 dark:bg-gray-950 dark:text-gray-100">
      {title && <div className="font-medium">{title}</div>}
      {items.map((item, i) => (
        <div key={i} style={item.color ? { color: item.color } : undefined}>
          {item.label ? `${item.label}: ` : ''}
          {item.value}
        </div>
      ))}
    </div>
  )
}
