import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { CostBreakdown } from '../../types'
import { formatCzk, formatNumber } from '../../lib/format'
import { SERVICE_TYPE_LABELS } from '../../lib/serviceTypes'
import { useIsDark } from '../../lib/useIsDark'
import { ChartTooltip } from './ChartTooltip'

const CATEGORY_LABELS: Record<string, string> = { fuel: 'Palivo', ...SERVICE_TYPE_LABELS }

const CATEGORY_COLORS: Record<string, { light: string; dark: string }> = {
  fuel: { light: '#2a78d6', dark: '#3987e5' },
  oil_change: { light: '#eb6834', dark: '#d95926' },
  tires: { light: '#1baf7a', dark: '#199e70' },
  engine_service: { light: '#eda100', dark: '#c98500' },
  additives: { light: '#8b5cf6', dark: '#7c3aed' },
  other: { light: '#e87ba4', dark: '#d55181' },
}

export function CostBreakdownChart({ data }: { data: CostBreakdown }) {
  const isDark = useIsDark()

  const rows = [
    { key: 'fuel', value: data.fuel_total },
    ...Object.entries(data.maintenance_by_type).map(([key, value]) => ({ key, value })),
  ].filter((row) => row.value > 0)

  if (rows.length === 0) {
    return <p className="text-sm text-gray-500 dark:text-gray-400">Zatím žádné náklady.</p>
  }

  const chartData = rows.map((row) => ({
    name: CATEGORY_LABELS[row.key] ?? row.key,
    value: row.value,
    key: row.key,
  }))

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#2c2c2a' : '#e1e0d9'} vertical={false} />
        <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#898781' }} tickLine={false} axisLine={false} />
        <YAxis tickFormatter={formatNumber} tick={{ fontSize: 11, fill: '#898781' }} tickLine={false} axisLine={false} width={40} />
        <Tooltip
          content={({ active, payload }) => (
            <ChartTooltip
              active={active}
              title={typeof payload?.[0]?.payload?.name === 'string' ? payload[0].payload.name : undefined}
              items={
                payload?.[0]
                  ? [{ value: formatCzk(Number(payload[0].value)) }]
                  : []
              }
            />
          )}
        />
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          {chartData.map((row) => (
            <Cell
              key={row.key}
              fill={
                isDark
                  ? (CATEGORY_COLORS[row.key]?.dark ?? '#898781')
                  : (CATEGORY_COLORS[row.key]?.light ?? '#898781')
              }
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
