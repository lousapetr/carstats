import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { FuelTrendPoint } from '../../types'
import { formatDate, formatShortDate } from '../../lib/dates'
import { formatConsumption, formatNumber, formatPricePerLiter } from '../../lib/format'
import { ChartFigure } from './ChartFigure'
import { ChartTooltip } from './ChartTooltip'
import { payloadNumber, useChartTheme } from './chartTheme'

function SingleSeriesLineChart({
  data,
  dataKey,
  color,
  caption,
  formatValue,
}: {
  data: FuelTrendPoint[]
  dataKey: 'price_per_liter' | 'consumption_l_per_100km'
  color: string
  caption: string
  formatValue: (value: number) => string
}) {
  const theme = useChartTheme()
  const tick = { fontSize: 11, fill: theme.tick }

  return (
    <ChartFigure caption={caption}>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.grid} vertical={false} />
          <XAxis
            dataKey="date"
            tickFormatter={formatShortDate}
            tick={tick}
            tickLine={false}
            axisLine={false}
            minTickGap={16}
          />
          <YAxis
            tickFormatter={formatNumber}
            tick={tick}
            tickLine={false}
            axisLine={false}
            width={36}
            domain={['auto', 'auto']}
          />
          <Tooltip
            content={({ active, label, payload }) => {
              const value = payloadNumber(payload?.[0]?.value)
              return (
                <ChartTooltip
                  active={active}
                  title={typeof label === 'string' ? formatDate(label) : undefined}
                  items={value !== null ? [{ value: formatValue(value) }] : []}
                />
              )
            }}
          />
          <Line
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartFigure>
  )
}

export function PricePerLiterChart({ data }: { data: FuelTrendPoint[] }) {
  const theme = useChartTheme()
  return (
    <SingleSeriesLineChart
      data={data}
      dataKey="price_per_liter"
      color={theme.pricePerLiter}
      caption="Spojnicový graf ceny paliva za litr v Kč podle data tankování."
      formatValue={formatPricePerLiter}
    />
  )
}

export function ConsumptionTrendChart({ data }: { data: FuelTrendPoint[] }) {
  const theme = useChartTheme()
  return (
    <SingleSeriesLineChart
      data={data.filter((d) => d.consumption_l_per_100km !== null)}
      dataKey="consumption_l_per_100km"
      color={theme.consumption}
      caption="Spojnicový graf spotřeby v litrech na 100 km podle data plného tankování."
      formatValue={(v) => formatConsumption(v)}
    />
  )
}
