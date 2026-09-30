import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { FuelTrendPoint } from '../../types'
import { formatDate } from '../../lib/dates'
import { formatConsumption, formatCzk, formatNumber, formatPricePerLiter } from '../../lib/format'
import { useIsDark } from '../../lib/useIsDark'
import { ChartTooltip } from './ChartTooltip'

const CHART_COLORS = {
  price: { light: '#2a78d6', dark: '#3987e5' },
  pricePerLiter: { light: '#1baf7a', dark: '#199e70' },
  consumption: { light: '#eb6834', dark: '#d95926' },
  grid: { light: '#e1e0d9', dark: '#2c2c2a' },
  axis: { light: '#898781', dark: '#898781' },
}

const PRICE_TREND_LABELS: Record<string, string> = {
  price_total: 'Cena celkem',
  price_per_liter: 'Cena za litr',
}

export function FuelPriceTrendChart({ data }: { data: FuelTrendPoint[] }) {
  const isDark = useIsDark()
  const totalColor = isDark ? CHART_COLORS.price.dark : CHART_COLORS.price.light
  const perLiterColor = isDark ? CHART_COLORS.pricePerLiter.dark : CHART_COLORS.pricePerLiter.light

  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke={isDark ? CHART_COLORS.grid.dark : CHART_COLORS.grid.light}
          vertical={false}
        />
        <XAxis
          dataKey="date"
          tickFormatter={formatDate}
          tick={{ fontSize: 11, fill: CHART_COLORS.axis.light }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tickFormatter={formatNumber}
          yAxisId="total"
          tick={{ fontSize: 11, fill: CHART_COLORS.axis.light }}
          tickLine={false}
          axisLine={false}
          width={36}
        />
        <YAxis
          tickFormatter={formatNumber}
          yAxisId="perLiter"
          orientation="right"
          tick={{ fontSize: 11, fill: CHART_COLORS.axis.light }}
          tickLine={false}
          axisLine={false}
          width={36}
        />
        <Tooltip
          content={({ active, label, payload }) => (
            <ChartTooltip
              active={active}
              title={typeof label === 'string' ? formatDate(label) : undefined}
              items={(payload ?? []).map((entry) => ({
                label: PRICE_TREND_LABELS[String(entry.dataKey)] ?? String(entry.name),
                value:
                  entry.dataKey === 'price_total'
                    ? formatCzk(Number(entry.value))
                    : formatPricePerLiter(Number(entry.value)),
                color: entry.color,
              }))}
            />
          )}
        />
        <Legend
          formatter={(value) => PRICE_TREND_LABELS[value] ?? value}
          wrapperStyle={{ fontSize: 11 }}
        />
        <Line
          yAxisId="total"
          type="monotone"
          dataKey="price_total"
          stroke={totalColor}
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
        />
        <Line
          yAxisId="perLiter"
          type="monotone"
          dataKey="price_per_liter"
          stroke={perLiterColor}
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function ConsumptionTrendChart({ data }: { data: FuelTrendPoint[] }) {
  const isDark = useIsDark()
  const color = isDark ? CHART_COLORS.consumption.dark : CHART_COLORS.consumption.light
  const points = data.filter((d) => d.consumption_l_per_100km !== null)

  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={points} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke={isDark ? CHART_COLORS.grid.dark : CHART_COLORS.grid.light}
          vertical={false}
        />
        <XAxis
          dataKey="date"
          tickFormatter={formatDate}
          tick={{ fontSize: 11, fill: CHART_COLORS.axis.light }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tickFormatter={formatNumber}
          tick={{ fontSize: 11, fill: CHART_COLORS.axis.light }}
          tickLine={false}
          axisLine={false}
          width={36}
        />
        <Tooltip
          content={({ active, label, payload }) => (
            <ChartTooltip
              active={active}
              title={typeof label === 'string' ? formatDate(label) : undefined}
              items={
                payload?.[0]
                  ? [{ value: formatConsumption(Number(payload[0].value)) }]
                  : []
              }
            />
          )}
        />
        <Line
          type="monotone"
          dataKey="consumption_l_per_100km"
          stroke={color}
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
