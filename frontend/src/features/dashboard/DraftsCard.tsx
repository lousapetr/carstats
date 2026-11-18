import { Link } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { formatDate } from '../../lib/dates'
import { formatKm, formatLiters, formatMoney } from '../../lib/format'
import { SERVICE_TYPE_LABELS } from '../../lib/serviceTypes'
import type { DraftItem } from '../../types'

function summary(item: DraftItem): string {
  const parts =
    item.kind === 'fuel'
      ? [
          item.liters !== null && formatLiters(item.liters),
          item.price_total !== null && formatMoney(item.price_total, item.currency),
        ]
      : [
          item.service_type !== null && SERVICE_TYPE_LABELS[item.service_type],
          item.description,
          item.cost !== null && formatMoney(item.cost, item.currency),
        ]
  return parts.filter(Boolean).join(' · ')
}

export function DraftsCard({ drafts }: { drafts: DraftItem[] }) {
  if (drafts.length === 0) return null
  return (
    <Card className="flex flex-col gap-2">
      <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
        Rozpracované záznamy
      </h2>
      {drafts.map((d) => (
        <Link
          key={`${d.kind}-${d.id}`}
          to={`${d.kind === 'fuel' ? '/fuel' : '/maintenance'}?edit=${d.id}`}
          className="text-sm text-gray-700 hover:underline dark:text-gray-300"
        >
          <span className="font-medium">{d.kind === 'fuel' ? 'Tankování' : 'Servis'}</span>
          {' · '}
          {d.date ? formatDate(d.date) : 'bez data'}
          {' · '}
          {d.mileage_km !== null ? formatKm(d.mileage_km) : '–'}
          {summary(d) && <span className="text-gray-500 dark:text-gray-400"> · {summary(d)}</span>}
        </Link>
      ))}
    </Card>
  )
}
