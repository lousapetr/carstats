import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '../../api/dashboard'
import { Card } from '../../components/ui/Card'
import { StatTile } from '../../components/ui/StatTile'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { formatCzk } from '../../lib/currencies'
import { CostBreakdownChart } from './CostBreakdownChart'
import { ConsumptionTrendChart, FuelPriceTrendChart } from './FuelTrendChart'

export function DashboardPage() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: dashboardApi.summary,
  })

  const { data: fuelTrend } = useQuery({
    queryKey: ['dashboard', 'fuel-trend'],
    queryFn: dashboardApi.fuelTrend,
  })

  const { data: costBreakdown } = useQuery({
    queryKey: ['dashboard', 'cost-breakdown'],
    queryFn: dashboardApi.costBreakdown,
  })

  if (summaryLoading || !summary) {
    return <p className="text-sm text-gray-500">Načítám…</p>
  }

  const carLabel =
    summary.car.name || [summary.car.year, summary.car.make, summary.car.model]
      .filter(Boolean)
      .join(' ')

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {carLabel || 'Vaše auto'}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {summary.car.current_mileage_km.toLocaleString()} km
        </p>
      </div>

      {summary.upcoming_reminders.some((r) => r.status !== 'ok') && (
        <Card className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Vyžaduje pozornost
          </h2>
          {summary.upcoming_reminders
            .filter((r) => r.status !== 'ok')
            .map((r) => (
              <div key={r.id} className="flex items-center justify-between text-sm">
                <span className="text-gray-700 dark:text-gray-300">{r.title}</span>
                <StatusBadge status={r.status} />
              </div>
            ))}
        </Card>
      )}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile label="Celkové náklady" value={formatCzk(summary.total_cost)} />
        <StatTile label="Náklady na palivo" value={formatCzk(summary.total_fuel_cost)} />
        <StatTile label="Náklady na servis" value={formatCzk(summary.total_maintenance_cost)} />
        <StatTile
          label="Průměrná spotřeba"
          value={
            summary.avg_consumption_l_per_100km !== null
              ? `${summary.avg_consumption_l_per_100km} l/100 km`
              : '—'
          }
        />
        <StatTile label="Náklady letos" value={formatCzk(summary.total_cost_this_year)} />
        <StatTile label="Náklady vloni" value={formatCzk(summary.total_cost_last_year)} />
        <StatTile
          label="Náklady na km"
          value={summary.cost_per_km !== null ? `${summary.cost_per_km} Kč/km` : '—'}
        />
      </div>

      {fuelTrend && fuelTrend.length > 0 && (
        <Card>
          <h2 className="mb-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
            Cena paliva v čase
          </h2>
          <FuelPriceTrendChart data={fuelTrend} />
        </Card>
      )}

      {fuelTrend && fuelTrend.some((p) => p.consumption_l_per_100km !== null) && (
        <Card>
          <h2 className="mb-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
            Spotřeba v čase
          </h2>
          <ConsumptionTrendChart data={fuelTrend} />
        </Card>
      )}

      {costBreakdown && (
        <Card>
          <h2 className="mb-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
            Rozložení nákladů
          </h2>
          <CostBreakdownChart data={costBreakdown} />
        </Card>
      )}

      <Card>
        <h2 className="mb-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
          Poslední aktivita
        </h2>
        <div className="flex flex-col">
          {summary.recent_activity.map((item, i) => (
            <div
              key={i}
              className={`flex items-center justify-between rounded-md px-2 py-1.5 text-sm ${
                i % 2 === 0 ? 'bg-gray-50 dark:bg-gray-900' : ''
              }`}
            >
              <span className="text-gray-700 dark:text-gray-300">
                {item.date} · {item.label}
              </span>
              <span className="text-gray-500 dark:text-gray-400">{formatCzk(item.cost)}</span>
            </div>
          ))}
          {summary.recent_activity.length === 0 && (
            <p className="text-sm text-gray-500 dark:text-gray-400">Zatím žádná aktivita.</p>
          )}
        </div>
      </Card>
    </div>
  )
}
