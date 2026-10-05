import { formatDate } from '../../lib/dates'
import { formatCzk, formatKm, formatLiters, formatPricePerLiter } from '../../lib/format'
import { SERVICE_TYPE_LABELS } from '../../lib/serviceTypes'
import type { TimelineItem } from '../../types'

const ACTIVITY_LIMIT = 10

function ActivityLabel({ item }: { item: TimelineItem }) {
  const [name, detail] =
    item.kind === 'fuel'
      ? ['Tankování', `${formatLiters(item.liters)} · ${formatPricePerLiter(item.price_per_liter)}`]
      : [SERVICE_TYPE_LABELS[item.service_type], item.description]
  return (
    <>
      <span className="mr-2 font-medium text-gray-900 dark:text-gray-100">{name}</span>
      {detail}
    </>
  )
}

/** The newest entries; on narrow screens the label drops below date and odometer. */
export function ActivityList({ items, empty }: { items: TimelineItem[]; empty: string }) {
  if (items.length === 0) {
    return <p className="text-sm text-gray-500 dark:text-gray-400">{empty}</p>
  }
  return (
    <div className="flex flex-col">
      {items.slice(0, ACTIVITY_LIMIT).map((item, i) => (
        <div
          key={i}
          className={`rounded-md px-2 py-1.5 text-sm ${
            i % 2 === 0 ? 'bg-gray-50 dark:bg-gray-900' : ''
          }`}
        >
          <div className="flex items-start justify-between gap-3">
            <span className="text-gray-700 dark:text-gray-300">
              {formatDate(item.date)} · {formatKm(item.mileage_km)}
              <span className="hidden sm:inline">
                {' · '}
                <ActivityLabel item={item} />
              </span>
            </span>
            <span className="shrink-0 text-gray-500 dark:text-gray-400">
              {formatCzk(item.cost)}
            </span>
          </div>
          <div className="text-gray-700 sm:hidden dark:text-gray-300">
            <ActivityLabel item={item} />
          </div>
        </div>
      ))}
    </div>
  )
}
