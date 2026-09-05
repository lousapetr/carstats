import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { CostBreakdown } from '../../types'

const CATEGORY_COLORS: Record<string, { light: string; dark: string; label: string }> = {
  fuel: { light: '#2a78d6', dark: '#3987e5', label: 'Palivo' },
  oil_change: { light: '#eb6834', dark: '#d95926', label: 'Výměna oleje' },
  tires: { light: '#1baf7a', dark: '#199e70', label: 'Pneumatiky' },
  engine_service: { light: '#eda100', dark: '#c98500', label: 'Servis motoru' },
  additives: { light: '#8b5cf6', dark: '#7c3aed', label: 'Aditiva' },
  other: { light: '#e87ba4', dark: '#d55181', label: 'Jiné' },
}

function useIsDark() {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(prefers-color-scheme: dark)').matches
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
    name: CATEGORY_COLORS[row.key]?.label ?? row.key,
    value: row.value,
    key: row.key,
  }))

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#2c2c2a' : '#e1e0d9'} vertical={false} />
        <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#898781' }} tickLine={false} axisLine={false} />
        <YAxis tick={{ fontSize: 11, fill: '#898781' }} tickLine={false} axisLine={false} width={40} />
        <Tooltip
          formatter={(value, _name, props) => [
            `${Number(value).toFixed(2)} Kč`,
            props.payload?.name ?? '',
          ]}
          contentStyle={{ fontSize: 12 }}
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
