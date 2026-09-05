import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { Button } from '../../components/ui/Button'
import { Field, inputClass } from '../../components/ui/Field'
import { CURRENCIES, CURRENCY_CODES, CURRENCY_LABELS } from '../../lib/currencies'

const schema = z.object({
  date: z.string().min(1, 'Povinné pole'),
  mileage_km: z.coerce.number().positive('Musí být kladné číslo'),
  type: z.enum(['oil_change', 'tires', 'engine_service', 'additives', 'other']),
  description: z.string().optional(),
  cost: z.coerce.number().min(0, 'Musí být 0 nebo více'),
  currency: z.enum(CURRENCY_CODES),
  notes: z.string().optional(),
})

export type MaintenanceFormValues = z.output<typeof schema>
type MaintenanceFormInput = z.input<typeof schema>

const TYPE_OPTIONS: { value: MaintenanceFormValues['type']; label: string }[] = [
  { value: 'oil_change', label: 'Výměna oleje' },
  { value: 'tires', label: 'Pneumatiky' },
  { value: 'engine_service', label: 'Servis motoru' },
  { value: 'additives', label: 'Aditiva' },
  { value: 'other', label: 'Jiné' },
]

export function MaintenanceForm({
  onSubmit,
  isSubmitting,
  defaultValues,
  submitLabel,
  onCancel,
}: {
  onSubmit: (values: MaintenanceFormValues) => void
  isSubmitting: boolean
  defaultValues?: MaintenanceFormInput
  submitLabel?: string
  onCancel?: () => void
}) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<MaintenanceFormInput, unknown, MaintenanceFormValues>({
    resolver: zodResolver(schema),
    defaultValues: defaultValues ?? {
      date: new Date().toISOString().slice(0, 10),
      type: 'oil_change',
      currency: 'CZK',
    },
  })

  return (
    <form
      onSubmit={handleSubmit((values) => {
        onSubmit(values)
        if (!defaultValues) {
          reset({
            date: new Date().toISOString().slice(0, 10),
            type: 'oil_change',
            currency: 'CZK',
          })
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
      <Field label="Typ" error={errors.type?.message}>
        <select className={inputClass} {...register('type')}>
          {TYPE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Cena" error={errors.cost?.message}>
        <input type="number" step="0.01" className={inputClass} {...register('cost')} />
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
        <Field label="Popis">
          <input type="text" className={inputClass} {...register('description')} />
        </Field>
      </div>
      <div className="col-span-2">
        <Field label="Poznámka">
          <input type="text" className={inputClass} {...register('notes')} />
        </Field>
      </div>
      <div className="col-span-2 flex gap-2">
        <Button type="submit" disabled={isSubmitting} className="flex-1">
          {isSubmitting ? 'Ukládám…' : (submitLabel ?? 'Zapsat servis')}
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
