import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '../../api/dashboard'
import { Card } from '../../components/ui/Card'
import { ErrorState } from '../../components/ui/ErrorState'
import { LoadingState } from '../../components/ui/LoadingState'
import { StatTile } from '../../components/ui/StatTile'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { formatDate } from '../../lib/dates'
import { formatConsumption, formatCostPerKm, formatCzk, formatKm, formatLiters } from '../../lib/format'
import { serviceEntryLabel } from '../../lib/serviceTypes'
import type { TimelineItem } from '../../types'
import { CostBreakdownChart } from './CostBreakdownChart'
import { FirstRunCard } from './FirstRunCard'
import { ConsumptionTrendChart, PricePerLiterChart } from './FuelTrendChart'

function timelineLabel(item: TimelineItem) {
  return item.kind === 'fuel'
    ? `Tankování (${formatLiters(item.liters)})`
    : serviceEntryLabel(item.service_type, item.description)
}

export function DashboardPage() {
  const summaryQuery = useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: dashboardApi.summary,
  })
  const fuelTrendQuery = useQuery({
    queryKey: ['dashboard', 'fuel-trend'],
    queryFn: dashboardApi.fuelTrend,
  })
  const costBreakdownQuery = useQuery({
    queryKey: ['dashboard', 'cost-breakdown'],
    queryFn: dashboardApi.costBreakdown,
  })
  const queries = [summaryQuery, fuelTrendQuery, costBreakdownQuery]

  if (queries.some((q) => q.isError)) {
    return (
      <ErrorState
        message="Přehled se nepodařilo načíst."
        onRetry={() => queries.filter((q) => q.isError).forEach((q) => void q.refetch())}
      />
    )
  }
  const summary = summaryQuery.data
  const fuelTrend = fuelTrendQuery.data
  const costBreakdown = costBreakdownQuery.data
  if (!summary || !fuelTrend || !costBreakdown) return <LoadingState />

  const isFirstRun = summary.total_fuel_entries === 0 && summary.total_maintenance_entries === 0

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
          {formatKm(summary.car.current_mileage_km)}
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

      {isFirstRun ? (
        <FirstRunCard />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatTile label="Celkové náklady" value={formatCzk(summary.total_cost)} />
            <StatTile label="Náklady na palivo" value={formatCzk(summary.total_fuel_cost)} />
            <StatTile label="Náklady na servis" value={formatCzk(summary.total_maintenance_cost)} />
            <StatTile label="Náklady na km" value={formatCostPerKm(summary.cost_per_km)} />
            <StatTile label="Náklady letos" value={formatCzk(summary.total_cost_this_year)} />
            <StatTile label="Náklady vloni" value={formatCzk(summary.total_cost_last_year)} />
            <StatTile
              label="Spotřeba celkem"
              value={formatConsumption(summary.avg_consumption_l_per_100km)}
            />
            <StatTile
              label="Spotřeba letos"
              value={formatConsumption(summary.avg_consumption_l_per_100km_this_year)}
            />
            <StatTile
              label="Spotřeba vloni"
              value={formatConsumption(summary.avg_consumption_l_per_100km_last_year)}
            />
          </div>

          {fuelTrend.length > 0 && (
            <Card>
              <h2 className="mb-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
                Cena paliva za litr
              </h2>
              <PricePerLiterChart data={fuelTrend} />
            </Card>
          )}

          {fuelTrend.some((p) => p.consumption_l_per_100km !== null) && (
            <Card>
              <h2 className="mb-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
                Spotřeba v čase
              </h2>
              <ConsumptionTrendChart data={fuelTrend} />
            </Card>
          )}

          <Card>
            <h2 className="mb-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
              Náklady podle kategorie
            </h2>
            <CostBreakdownChart data={costBreakdown} />
          </Card>

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
                    {formatDate(item.date)} · {timelineLabel(item)}
                  </span>
                  <span className="text-gray-500 dark:text-gray-400">{formatCzk(item.cost)}</span>
                </div>
              ))}
              {summary.recent_activity.length === 0 && (
                <p className="text-sm text-gray-500 dark:text-gray-400">Zatím žádná aktivita.</p>
              )}
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
