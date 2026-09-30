import { keepPreviousData, useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { useSearchParams } from 'react-router-dom'
import { dashboardApi } from '../../api/dashboard'
import { Card } from '../../components/ui/Card'
import { ErrorState } from '../../components/ui/ErrorState'
import { LoadingState } from '../../components/ui/LoadingState'
import { StatTile } from '../../components/ui/StatTile'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { formatDate } from '../../lib/dates'
import {
  formatConsumption,
  formatCostPerKm,
  formatCzk,
  formatKm,
  formatLiters,
  formatPercent,
  formatPricePerLiter,
  pluralize,
} from '../../lib/format'
import {
  DEFAULT_PERIOD,
  parsePeriod,
  periodLabel,
  previousPeriodLabel,
} from '../../lib/periods'
import { serviceEntryLabel } from '../../lib/serviceTypes'
import type { Period, TimelineItem } from '../../types'
import { CostBreakdownChart } from './CostBreakdownChart'
import { Delta } from './Delta'
import { FirstRunCard } from './FirstRunCard'
import { ConsumptionTrendChart, PricePerLiterChart } from './FuelTrendChart'
import { MonthlyCostChart } from './MonthlyCostChart'
import { PeriodSelector } from './PeriodSelector'

function timelineLabel(item: TimelineItem) {
  return item.kind === 'fuel'
    ? `Tankování (${formatLiters(item.liters)} · ${formatPricePerLiter(item.price_per_liter)})`
    : serviceEntryLabel(item.service_type, item.description)
}

function ChartCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Card>
      <h2 className="mb-2 text-sm font-semibold text-gray-900 dark:text-gray-100">{title}</h2>
      {children}
    </Card>
  )
}

export function DashboardPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const period = parsePeriod(searchParams.get('period'))

  const {
    data: dashboard,
    isPending,
    isPlaceholderData,
    refetch,
  } = useQuery({
    queryKey: ['dashboard', period],
    queryFn: () => dashboardApi.get(period),
    placeholderData: keepPreviousData,
  })

  function selectPeriod(next: Period) {
    setSearchParams((params) => {
      if (next === DEFAULT_PERIOD) params.delete('period')
      else params.set('period', next)
      return params
    })
  }

  if (isPending) return <LoadingState />
  // A failed background refetch keeps showing the last good data; only a
  // query with nothing to show falls through to the error.
  if (!dashboard) {
    return <ErrorState message="Přehled se nepodařilo načíst." onRetry={() => void refetch()} />
  }

  const carLabel =
    dashboard.car.name ||
    [dashboard.car.year, dashboard.car.make, dashboard.car.model].filter(Boolean).join(' ')
  const vs = previousPeriodLabel(dashboard.period)
  const { totals } = dashboard
  const attention = dashboard.upcoming_reminders.filter((r) => r.status !== 'ok')
  const hasConsumption = dashboard.fuel_trend.some((p) => p.consumption_l_per_100km !== null)

  return (
    <div className="flex flex-col gap-4">
      {/* The car and its reminders are about now, not the selected period, so
          they sit above the selector that scopes everything below it. */}
      <div>
        <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {carLabel || 'Vaše auto'}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {formatKm(dashboard.car.current_mileage_km)}
        </p>
      </div>

      {attention.length > 0 && (
        <Card className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Vyžaduje pozornost
          </h2>
          {attention.map((r) => (
            <div key={r.id} className="flex items-center justify-between text-sm">
              <span className="text-gray-700 dark:text-gray-300">{r.title}</span>
              <StatusBadge status={r.status} />
            </div>
          ))}
        </Card>
      )}

      {/* No entries in any year means nothing has been logged yet. */}
      {dashboard.available_years.length === 0 ? (
        <FirstRunCard />
      ) : (
        <>
          <PeriodSelector
            value={period}
            years={dashboard.available_years}
            bounds={dashboard.period}
            onChange={selectPeriod}
          />

          <div
            className={`flex flex-col gap-4 transition-opacity ${isPlaceholderData ? 'opacity-60' : ''}`}
            aria-busy={isPlaceholderData}
          >
            <Card>
              <div className="text-xs font-medium tracking-wide text-gray-500 uppercase dark:text-gray-400">
                Spotřeba
              </div>
              <div className="mt-1 text-4xl font-semibold text-gray-900 sm:text-5xl dark:text-gray-100">
                {formatConsumption(dashboard.avg_consumption_l_per_100km)}
              </div>
              <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {periodLabel(dashboard.period.key)}
                {dashboard.avg_consumption_delta !== null && (
                  <>
                    {' · '}
                    <Delta
                      value={dashboard.avg_consumption_delta}
                      formatMagnitude={(v) => formatConsumption(v)}
                      vs={vs}
                    />
                  </>
                )}
                {' · '}
                {dashboard.consumption_interval_count > 0
                  ? `z ${pluralize(dashboard.consumption_interval_count, 'intervalu', 'intervalů', 'intervalů')} mezi plnými nádržemi`
                  : 'žádný úsek mezi plnými nádržemi'}
              </div>
            </Card>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <StatTile
                label="Najeté kilometry"
                value={dashboard.distance_km !== null ? formatKm(dashboard.distance_km) : '—'}
              />
              <StatTile
                label="Celkové náklady"
                value={formatCzk(totals.total)}
                sub={
                  <Delta
                    value={dashboard.total_cost_delta_pct}
                    formatMagnitude={formatPercent}
                    vs={vs}
                  />
                }
              />
              <StatTile
                label="Palivo"
                value={formatCzk(totals.fuel)}
                sub={`${formatLiters(totals.fuel_liters)} · ${pluralize(totals.fuel_entries, 'tankování', 'tankování', 'tankování')}`}
              />
              <StatTile
                label="Servis"
                value={formatCzk(totals.maintenance)}
                sub={pluralize(totals.maintenance_entries, 'záznam', 'záznamy', 'záznamů')}
              />
              <StatTile label="Náklady/km" value={formatCostPerKm(dashboard.cost_per_km)} />
              <StatTile
                label="Průměrná cena paliva"
                value={
                  dashboard.avg_price_per_liter !== null
                    ? formatPricePerLiter(dashboard.avg_price_per_liter)
                    : '—'
                }
                sub={
                  <Delta
                    value={dashboard.avg_price_per_liter_delta}
                    formatMagnitude={formatPricePerLiter}
                    vs={vs}
                  />
                }
              />
            </div>

            {hasConsumption && (
              <ChartCard title="Spotřeba v čase">
                <ConsumptionTrendChart
                  data={dashboard.fuel_trend}
                  average={dashboard.avg_consumption_l_per_100km}
                />
              </ChartCard>
            )}

            {dashboard.monthly_costs.length > 0 && (
              <ChartCard
                title={dashboard.monthly_granularity === 'year' ? 'Roční náklady' : 'Měsíční náklady'}
              >
                <MonthlyCostChart
                  data={dashboard.monthly_costs}
                  granularity={dashboard.monthly_granularity}
                />
              </ChartCard>
            )}

            {dashboard.fuel_trend.length > 0 && (
              <ChartCard title="Cena paliva za litr">
                <PricePerLiterChart
                  data={dashboard.fuel_trend}
                  average={dashboard.avg_price_per_liter}
                />
              </ChartCard>
            )}

            <ChartCard title="Náklady podle kategorie">
              <CostBreakdownChart data={dashboard.cost_breakdown} />
            </ChartCard>

            <ChartCard title="Poslední aktivita">
              <div className="flex flex-col">
                {dashboard.recent_activity.map((item, i) => (
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
                {dashboard.recent_activity.length === 0 && (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    V tomto období žádná aktivita.
                  </p>
                )}
              </div>
            </ChartCard>
          </div>
        </>
      )}
    </div>
  )
}
