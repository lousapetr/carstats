import { type MouseEvent, useState } from 'react'
import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ResponsiveContainer,
  Text,
  XAxis,
  YAxis,
  type YAxisTickContentProps,
} from 'recharts'
import type { CostBreakdown, TimelineItem } from '../../types'
import { formatCzk } from '../../lib/format'
import { SERVICE_TYPE_LABELS } from '../../lib/serviceTypes'
import { ActivityList } from './ActivityList'
import { ChartFigure } from './ChartFigure'
import { payloadNumber, useChartTheme } from './chartTheme'

const CATEGORY_LABELS: Record<string, string> = { fuel: 'Tankování', ...SERVICE_TYPE_LABELS }

const BAR_HEIGHT = 36
// Room right of the longest bar for its value, which must never wrap.
const VALUE_LABEL_WIDTH = 68
const VALUE_LABEL_GAP = 6
const PLOT_TOP = 8

/** The item's cost-breakdown key: `fuel`, or the service type. */
function activityCategory(item: TimelineItem): string {
  return item.kind === 'fuel' ? 'fuel' : item.service_type
}

export function CostBreakdownChart({
  data,
  activity,
}: {
  data: CostBreakdown
  activity: TimelineItem[]
}) {
  const theme = useChartTheme()
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [chartWidth, setChartWidth] = useState(0)
  // Narrow screens give the bars room and wrap the category names instead.
  const axisWidth = chartWidth > 0 && chartWidth < 400 ? 64 : 104

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

  // A period change can drop the selected category from the chart.
  const selected = rows.find((row) => row.key === selectedKey) ?? null

  const chartHeight = Math.max(120, rows.length * BAR_HEIGHT + 16)

  // The category axis splits the plot into equal bands, so the click's height
  // alone names the row, wherever across the card it lands.
  function selectAt(e: MouseEvent<HTMLDivElement>) {
    const rect = e.currentTarget.getBoundingClientRect()
    const band = (rect.height - PLOT_TOP) / rows.length
    toggleRow(Math.floor((e.clientY - rect.top - PLOT_TOP) / band))
  }

  function toggleRow(index: number) {
    const row = rows[index]
    if (!row) return
    if (row.key === selected?.key) {
      setSelectedKey(null)
    } else {
      setSelectedKey(row.key)
      setDetailsOpen(true)
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <ChartFigure caption="Vodorovný sloupcový graf nákladů podle kategorie v Kč; klepnutím na kategorii se pod ním zobrazí její záznamy.">
        <div onClick={selectAt} className="cursor-pointer">
          <ResponsiveContainer
            width="100%"
            height={chartHeight}
            onResize={(width) => setChartWidth(width)}
          >
            <BarChart
              data={rows}
              layout="vertical"
              margin={{ top: PLOT_TOP, right: VALUE_LABEL_WIDTH, bottom: 0, left: 0 }}
            >
              <XAxis type="number" hide domain={[0, 'dataMax']} />
              <YAxis
                type="category"
                dataKey="name"
                tick={({ x, y, payload }: YAxisTickContentProps) => (
                  <Text
                    x={x}
                    y={y}
                    width={axisWidth - 8}
                    textAnchor="end"
                    verticalAnchor="middle"
                    fontSize={11}
                    fill={theme.tick}
                  >
                    {String(payload.value)}
                  </Text>
                )}
                tickLine={false}
                axisLine={false}
                width={axisWidth}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
                {rows.map((row) => (
                  <Cell
                    key={row.key}
                    fill={theme.category(row.key)}
                    fillOpacity={selected && row.key !== selected.key ? 0.35 : 1}
                  />
                ))}
                <LabelList
                  dataKey="value"
                  content={({ x, y, width, height, value }) => {
                    const n = payloadNumber(value)
                    if (n === null) return null
                    return (
                      <text
                        x={Number(x) + Number(width) + VALUE_LABEL_GAP}
                        y={Number(y) + Number(height) / 2}
                        dominantBaseline="central"
                        fontSize={11}
                        fill={theme.tick}
                        style={{ whiteSpace: 'nowrap' }}
                      >
                        {formatCzk(n)}
                      </text>
                    )
                  }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </ChartFigure>
      <details
        className="text-sm"
        open={detailsOpen}
        onToggle={(e) => setDetailsOpen(e.currentTarget.open)}
      >
        <summary className="cursor-pointer text-gray-500 dark:text-gray-400">
          Zobrazit detaily{selected && ` — ${selected.name}`}
        </summary>
        <div className="mt-2">
          {selected ? (
            <ActivityList
              items={activity.filter((item) => activityCategory(item) === selected.key)}
              empty="V tomto období žádné záznamy."
            />
          ) : (
            <p className="text-gray-500 dark:text-gray-400">Klikněte na kategorii v grafu.</p>
          )}
        </div>
      </details>
    </div>
  )
}
