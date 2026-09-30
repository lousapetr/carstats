import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { CostBreakdown } from '../../types'
import { formatCzk } from '../../lib/format'
import { SERVICE_TYPE_LABELS } from '../../lib/serviceTypes'
import { ChartFigure } from './ChartFigure'
import { ChartTooltip } from './ChartTooltip'
import { payloadNumber, useChartTheme } from './chartTheme'

const CATEGORY_LABELS: Record<string, string> = { fuel: 'Palivo', ...SERVICE_TYPE_LABELS }

const BAR_HEIGHT = 36

export function CostBreakdownChart({ data }: { data: CostBreakdown }) {
  const theme = useChartTheme()

  const rows = [
    { key: 'fuel', value: data.fuel_total },
    ...Object.entries(data.maintenance_by_type).map(([key, value]) => ({ key, value })),
  ]
    .filter((row) => row.value > 0)
    .sort((a, b) => b.value - a.value)
    .map((row) => ({ ...row, name: CATEGORY_LABELS[row.key] ?? row.key }))

  if (rows.length === 0) {
    return <p className="text-sm text-gray-500 dark:text-gray-400">Zatím žádné náklady.</p>
  }

  return (
    <div className="flex flex-col gap-2">
      <ChartFigure caption="Vodorovný sloupcový graf nákladů podle kategorie v Kč; stejná čísla jsou v tabulce níže.">
        <ResponsiveContainer width="100%" height={Math.max(120, rows.length * BAR_HEIGHT + 16)}>
          <BarChart
            data={rows}
            layout="vertical"
            margin={{ top: 8, right: 8, bottom: 0, left: 0 }}
          >
            <XAxis type="number" hide domain={[0, (max: number) => max * 1.35]} />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fontSize: 11, fill: theme.tick }}
              tickLine={false}
              axisLine={false}
              width={96}
            />
            <Tooltip
              cursor={{ fill: theme.grid, opacity: 0.5 }}
              content={({ active, payload }) => {
                const value = payloadNumber(payload?.[0]?.value)
                const name = payload?.[0]?.payload?.name
                return (
                  <ChartTooltip
                    active={active}
                    title={typeof name === 'string' ? name : undefined}
                    items={value !== null ? [{ value: formatCzk(value) }] : []}
                  />
                )
              }}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
              {rows.map((row) => (
                <Cell key={row.key} fill={theme.category(row.key)} />
              ))}
              <LabelList
                dataKey="value"
                position="right"
                formatter={(v: unknown) => {
                  const n = payloadNumber(v)
                  return n !== null ? formatCzk(n) : ''
                }}
                style={{ fontSize: 11, fill: theme.tick }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartFigure>
      <details className="text-sm">
        <summary className="cursor-pointer text-gray-500 dark:text-gray-400">
          Zobrazit jako tabulku
        </summary>
        <table className="mt-2 w-full">
          <thead>
            <tr className="text-left text-xs text-gray-500 dark:text-gray-400">
              <th className="py-1 font-medium">Kategorie</th>
              <th className="py-1 text-right font-medium">Náklady</th>
            </tr>
          </thead>
          <tbody className="text-gray-700 dark:text-gray-300">
            {rows.map((row) => (
              <tr key={row.key} className="border-t border-gray-100 dark:border-gray-800">
                <td className="py-1">{row.name}</td>
                <td className="py-1 text-right tabular-nums">{formatCzk(row.value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  )
}
