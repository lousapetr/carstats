import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { Button } from '../../components/ui/Button'
import { Field, inputClass } from '../../components/ui/Field'
import { CURRENCIES, CURRENCY_CODES, CURRENCY_LABELS } from '../../lib/currencies'

const schema = z.object({
  date: z.string().min(1, 'Povinné pole'),
  mileage_km: z.coerce.number().positive('Musí být kladné číslo'),
  liters: z.coerce.number().positive('Musí být kladné číslo'),
  price_per_liter: z.coerce.number().positive('Musí být kladné číslo'),
  currency: z.enum(CURRENCY_CODES),
  notes: z.string().optional(),
})

export type FuelFormValues = z.output<typeof schema>
type FuelFormInput = z.input<typeof schema>

export function FuelForm({
  onSubmit,
  isSubmitting,
  defaultValues,
  submitLabel,
  onCancel,
}: {
  onSubmit: (values: FuelFormValues) => void
  isSubmitting: boolean
  defaultValues?: FuelFormInput
  submitLabel?: string
  onCancel?: () => void
}) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FuelFormInput, unknown, FuelFormValues>({
    resolver: zodResolver(schema),
    defaultValues: defaultValues ?? {
      date: new Date().toISOString().slice(0, 10),
      currency: 'CZK',
    },
  })

  return (
    <form
      onSubmit={handleSubmit((values) => {
        onSubmit(values)
        if (!defaultValues) {
          reset({ date: new Date().toISOString().slice(0, 10), currency: 'CZK' })
        }
      })}
      className="grid grid-cols-2 gap-3"
    >
      <Field label="Datum" error={errors.date?.message}>
        <input type="date" className={inputClass} {...register('date')} />
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
          step="0.01"
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
