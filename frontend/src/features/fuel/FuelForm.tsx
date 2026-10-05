import { zodResolver } from '@hookform/resolvers/zod'
import { useQuery } from '@tanstack/react-query'
import { type DefaultValues, useForm } from 'react-hook-form'
import { z } from 'zod'
import { currencyApi } from '../../api/currency'
import { Button } from '../../components/ui/Button'
import { dateInputClass, Field, inputClass } from '../../components/ui/Field'
import { CURRENCIES, CURRENCY_CODES, CURRENCY_LABELS } from '../../lib/currencies'
import { todayIso } from '../../lib/dates'

const schema = z.object({
  date: z.string().min(1, 'Povinné pole'),
  mileage_km: z.coerce.number().positive('Musí být kladné číslo'),
  liters: z.coerce.number().positive('Musí být kladné číslo'),
  price_per_liter: z.coerce.number().positive('Musí být kladné číslo'),
  currency: z.enum(CURRENCY_CODES),
  full_tank: z.boolean().default(true),
  notes: z.string().max(1000, 'Nejvýše 1000 znaků').optional(),
})

export type FuelFormValues = z.output<typeof schema>
type FuelFormInput = z.input<typeof schema>

const blankValues = (): DefaultValues<FuelFormInput> => ({
  date: todayIso(),
  currency: 'CZK',
  full_tank: true,
})

export function FuelForm({
  onSubmit,
  isSubmitting,
  defaultValues,
  submitLabel,
  onCancel,
}: {
  onSubmit: (values: FuelFormValues) => Promise<unknown>
  isSubmitting: boolean
  defaultValues?: FuelFormInput
  submitLabel?: string
  onCancel?: () => void
}) {
  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<FuelFormInput, unknown, FuelFormValues>({
    resolver: zodResolver(schema),
    defaultValues: defaultValues ?? blankValues(),
  })

  const currency = watch('currency')
  const { data: rates } = useQuery({ queryKey: ['currency-rates'], queryFn: currencyApi.list })
  const currentRate = rates?.find((r) => r.currency === currency)?.rate_to_czk

  return (
    <form
      onSubmit={handleSubmit(async (values) => {
        // Clear the form only once the server accepted the entry: a rejected
        // one (e.g. the mileage-consistency guard) has to stay put to be
        // corrected. The failure itself is toasted by the shared MutationCache.
        try {
          await onSubmit(values)
        } catch {
          return
        }
        if (!defaultValues) {
          reset(blankValues())
        }
      })}
      className="grid grid-cols-2 gap-3"
    >
      <Field label="Datum" error={errors.date?.message}>
        <input type="date" className={dateInputClass} {...register('date')} />
      </Field>
      <Field label="Stav tachometru (km)" error={errors.mileage_km?.message}>
        <input type="number" step="1" className={inputClass} {...register('mileage_km')} />
      </Field>
      <Field label="Litry" error={errors.liters?.message}>
        <input type="number" step="0.01" className={inputClass} {...register('liters')} />
      </Field>
      <Field label="Cena za litr" error={errors.price_per_liter?.message}>
        <input
          type="number"
          step="0.001"
          className={inputClass}
          {...register('price_per_liter')}
        />
      </Field>
      <Field label="Měna">
        <select className={inputClass} {...register('currency')}>
          {CURRENCIES.map((c) => (
            <option key={c} value={c}>
              {CURRENCY_LABELS[c]}
            </option>
          ))}
        </select>
      </Field>
      {currency !== 'CZK' && (
        <Field label="Kurz k CZK (ČNB)">
          <input
            type="number"
            className={`${inputClass} opacity-60`}
            value={currentRate ?? ''}
            disabled
            readOnly
          />
        </Field>
      )}
      <div className="col-span-2">
        <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
          <input type="checkbox" className="h-4 w-4" {...register('full_tank')} />
          Plná nádrž
        </label>
      </div>
      <div className="col-span-2">
        <Field label="Poznámka">
          <input type="text" className={inputClass} {...register('notes')} />
        </Field>
      </div>
      <div className="col-span-2 flex gap-2">
        <Button type="submit" disabled={isSubmitting} className="flex-1">
          {isSubmitting ? 'Ukládám…' : (submitLabel ?? 'Zapsat tankování')}
        </Button>
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel}>
            Zrušit
          </Button>
        )}
      </div>
    </form>
  )
}
