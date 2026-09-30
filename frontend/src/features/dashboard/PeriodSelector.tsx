import { type KeyboardEvent, useRef } from 'react'
import { periodLabel, yearPeriod } from '../../lib/periods'
import type { Period } from '../../types'

const SHORT_LABELS: Partial<Record<Period, string>> = { '12m': '12 m' }

/** Scrollable pills acting as one radio group: Tab lands on the selected
 *  pill, arrow keys move the selection.
 */
export function PeriodSelector({
  value,
  years,
  onChange,
}: {
  value: Period
  years: number[]
  onChange: (period: Period) => void
}) {
  const options: Period[] = ['all', 'ytd', '12m', ...years.map(yearPeriod)]
  if (!options.includes(value)) options.push(value)
  const refs = useRef<(HTMLButtonElement | null)[]>([])

  function onKeyDown(event: KeyboardEvent, index: number) {
    const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[event.key]
    if (step === undefined) return
    event.preventDefault()
    const next = (index + step + options.length) % options.length
    onChange(options[next])
    refs.current[next]?.focus()
  }

  return (
    <div
      role="radiogroup"
      aria-label="Období"
      className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 sm:mx-0 sm:px-0"
    >
      {options.map((option, i) => {
        const selected = option === value
        return (
          <button
            key={option}
            ref={(el) => {
              refs.current[i] = el
            }}
            type="button"
            role="radio"
            aria-checked={selected}
            aria-label={periodLabel(option)}
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(option)}
            onKeyDown={(event) => onKeyDown(event, i)}
            className={`shrink-0 rounded-full border px-3 py-1 text-sm whitespace-nowrap ${
              selected
                ? 'border-gray-900 bg-gray-900 text-white dark:border-gray-100 dark:bg-gray-100 dark:text-gray-900'
                : 'border-gray-300 bg-white text-gray-700 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-300'
            }`}
          >
            {SHORT_LABELS[option] ?? periodLabel(option)}
          </button>
        )
      })}
    </div>
  )
}
