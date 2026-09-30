import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { formatCzk, formatNumber } from '../../lib/format'
import type { Dashboard } from '../../types'
import { ChartFigure } from './ChartFigure'
import { ChartTooltip } from './ChartTooltip'
import { payloadNumber, useChartTheme } from './chartTheme'

const SERIES_LABELS: Record<string, string> = { fuel: 'Palivo', service: 'Servis' }

const MONTHS = [
  'leden',
  'únor',
  'březen',
  'duben',
  'květen',
  'červen',
  'červenec',
  'srpen',
  'září',
  'říjen',
  'listopad',
  'prosinec',
]

/** `2026-03` → `3/26`; a year bucket is left as is. */
function formatBucketTick(bucket: string) {
  const [year, month] = bucket.split('-')
  return month ? `${Number(month)}/${year.slice(2)}` : year
}

/** `2026-03` → `březen 2026`; a year bucket is left as is. */
function formatBucketTitle(bucket: string) {
  const [year, month] = bucket.split('-')
  return month ? `${MONTHS[Number(month) - 1]} ${year}` : year
}

export function MonthlyCostChart({
  data,
  granularity,
}: {
  data: Dashboard['monthly_costs']
  granularity: Dashboard['monthly_granularity']
}) {
  const theme = useChartTheme()
  const tick = { fontSize: 11, fill: theme.tick }

  return (
    <ChartFigure
      caption={`Skládaný sloupcový graf nákladů na palivo a servis v Kč po ${
        granularity === 'year' ? 'letech' : 'měsících'
      }.`}
    >
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.grid} vertical={false} />
          <XAxis
            dataKey="bucket"
            tickFormatter={formatBucketTick}
            tick={tick}
            tickLine={false}
            axisLine={false}
            minTickGap={8}
          />
          <YAxis
            tickFormatter={formatNumber}
            tick={tick}
            tickLine={false}
            axisLine={false}
            width={44}
          />
          <Tooltip
            cursor={{ fill: theme.grid, opacity: 0.5 }}
            content={({ active, label, payload }) => (
              <ChartTooltip
                active={active}
                title={typeof label === 'string' ? formatBucketTitle(label) : undefined}
                items={(payload ?? []).flatMap((entry) => {
                  const value = payloadNumber(entry.value)
                  return value !== null
                    ? [
                        {
                          label: SERIES_LABELS[String(entry.dataKey)] ?? String(entry.name),
                          value: formatCzk(value),
                          color: entry.color,
                        },
                      ]
                    : []
                })}
              />
            )}
          />
          <Legend
            formatter={(value: string) => SERIES_LABELS[value] ?? value}
            wrapperStyle={{ fontSize: 11 }}
          />
          <Bar dataKey="fuel" stackId="cost" fill={theme.category('fuel')} />
          <Bar
            dataKey="service"
            stackId="cost"
            fill={theme.category('service')}
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </ChartFigure>
  )
}
