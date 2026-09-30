import { type FormEvent, type KeyboardEvent, useRef, useState } from 'react'
import { Button } from '../../components/ui/Button'
import { Field, inputClass } from '../../components/ui/Field'
import { periodLabel, rangeBounds, rangePeriod, yearPeriod } from '../../lib/periods'
import type { Period } from '../../types'

const CUSTOM = 'custom'
type Option = Period | typeof CUSTOM

const SHORT_LABELS: Partial<Record<Option, string>> = { '12m': '12 m', [CUSTOM]: 'Vlastní…' }

/** Scrollable pills acting as one radio group: Tab lands on the selected
 *  pill, arrow keys move the selection. "Vlastní…" only opens the date form;
 *  the period changes once a range is applied.
 */
export function PeriodSelector({
  value,
  years,
  bounds,
  onChange,
}: {
  value: Period
  years: number[]
  /** The current window's bounds, used to prefill the custom range form. */
  bounds: { start: string | null; end: string | null }
  onChange: (period: Period) => void
}) {
  const options: Option[] = ['all', 'ytd', '12m', ...years.map(yearPeriod)]
  const isRange = rangeBounds(value) !== null
  if (!isRange && !options.includes(value)) options.push(value)
  options.push(CUSTOM)

  // Remembers which period the form was opened over, so a back-button change
  // of period closes a form that was never applied.
  const [customOpenedAt, setCustomOpenedAt] = useState<Period | null>(null)
  const customOpen = customOpenedAt === value
  const selected: Option = customOpen || isRange ? CUSTOM : value
  const refs = useRef<(HTMLButtonElement | null)[]>([])

  function choose(option: Option) {
    if (option === CUSTOM) {
      setCustomOpenedAt(value)
    } else {
      setCustomOpenedAt(null)
      onChange(option)
    }
  }

  function onKeyDown(event: KeyboardEvent, index: number) {
    const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[event.key]
    if (step === undefined) return
    event.preventDefault()
    const next = (index + step + options.length) % options.length
    choose(options[next])
    refs.current[next]?.focus()
  }

  return (
    <div className="flex flex-col gap-2">
      <div
        role="radiogroup"
        aria-label="Období"
        className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 sm:mx-0 sm:px-0"
      >
        {options.map((option, i) => {
          const checked = option === selected
          const label = option === CUSTOM ? 'Vlastní období' : periodLabel(option)
          return (
            <button
              key={option}
              ref={(el) => {
                refs.current[i] = el
              }}
              type="button"
              role="radio"
              aria-checked={checked}
              aria-label={label}
              tabIndex={checked ? 0 : -1}
              onClick={() => choose(option)}
              onKeyDown={(event) => onKeyDown(event, i)}
              className={`shrink-0 rounded-full border px-3 py-1 text-sm whitespace-nowrap ${
                checked
                  ? 'border-gray-900 bg-gray-900 text-white dark:border-gray-100 dark:bg-gray-100 dark:text-gray-900'
                  : 'border-gray-300 bg-white text-gray-700 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-300'
              }`}
            >
              {SHORT_LABELS[option] ?? label}
            </button>
          )
        })}
      </div>
      {selected === CUSTOM && (
        <CustomRangeForm
          key={value}
          initial={rangeBounds(value) ?? { from: bounds.start ?? '', to: bounds.end ?? '' }}
          onApply={(from, to) => onChange(rangePeriod(from, to))}
        />
      )}
    </div>
  )
}

function CustomRangeForm({
  initial,
  onApply,
}: {
  initial: { from: string; to: string }
  onApply: (from: string, to: string) => void
}) {
  const [from, setFrom] = useState(initial.from)
  const [to, setTo] = useState(initial.to)
  const reversed = from !== '' && to !== '' && from > to

  function submit(event: FormEvent) {
    event.preventDefault()
    if (from !== '' && to !== '' && !reversed) onApply(from, to)
  }

  return (
    <form
      onSubmit={submit}
      className="grid grid-cols-2 gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end"
    >
      <Field label="Od">
        <input
          type="date"
          className={inputClass}
          value={from}
          max={to || undefined}
          onChange={(e) => setFrom(e.target.value)}
          required
        />
      </Field>
      <Field label="Do" error={reversed ? 'Konec je před začátkem' : undefined}>
        <input
          type="date"
          className={inputClass}
          value={to}
          min={from || undefined}
          onChange={(e) => setTo(e.target.value)}
          required
        />
      </Field>
      <Button type="submit" className="col-span-2 sm:col-span-1" disabled={reversed}>
        Použít
      </Button>
    </form>
  )
}
