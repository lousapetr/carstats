import { zodResolver } from '@hookform/resolvers/zod'
import { useQuery } from '@tanstack/react-query'
import { useRef } from 'react'
import { type DefaultValues, type Resolver, useForm } from 'react-hook-form'
import { z } from 'zod'
import { currencyApi } from '../../api/currency'
import { Button } from '../../components/ui/Button'
import { dateInputClass, Field, inputClass } from '../../components/ui/Field'
import { CURRENCIES, CURRENCY_CODES, CURRENCY_LABELS } from '../../lib/currencies'
import { todayIso } from '../../lib/dates'
import { SERVICE_TYPE_VALUES, SERVICE_TYPES } from '../../lib/serviceTypes'

const emptyToUndefined = (val: unknown) => (val === '' ? undefined : val)

const fullSchema = z.object({
  date: z.string().min(1, 'Povinné pole'),
  mileage_km: z.coerce.number().positive('Musí být kladné číslo'),
  type: z.enum(SERVICE_TYPE_VALUES),
  description: z.string().max(1000, 'Nejvýše 1000 znaků').optional(),
  cost: z.preprocess(
    emptyToUndefined,
    z.coerce.number({ error: 'Povinné pole' }).min(0, 'Musí být 0 nebo více'),
  ),
  currency: z.enum(CURRENCY_CODES),
  notes: z.string().max(1000, 'Nejvýše 1000 znaků').optional(),
})

// A draft may leave date, mileage and cost empty, as long as one substantive
// field is filled in. That error sits on `notes` because react-hook-form drops
// `root` errors on submit.
const draftSchema = z
  .object({
    date: z.string().transform((v) => v || undefined),
    mileage_km: z.preprocess(
      emptyToUndefined,
      z.coerce.number().positive('Musí být kladné číslo').optional(),
    ),
    type: z.enum(SERVICE_TYPE_VALUES),
    description: z.string().max(1000, 'Nejvýše 1000 znaků').optional(),
    cost: z.preprocess(
      emptyToUndefined,
      z.coerce.number().min(0, 'Musí být 0 nebo více').optional(),
    ),
    currency: z.enum(CURRENCY_CODES),
    notes: z.string().max(1000, 'Nejvýše 1000 znaků').optional(),
  })
  .refine(
    (v) =>
      v.mileage_km !== undefined ||
      v.cost !== undefined ||
      !!v.description?.trim() ||
      !!v.notes?.trim(),
    { message: 'Vyplňte aspoň jeden údaj.', path: ['notes'] },
  )

/** Draft output is the loosest shape; a complete entry's values fit it too. */
export type MaintenanceFormValues = z.output<typeof draftSchema>
type MaintenanceFormInput = z.input<typeof draftSchema>

// The complete-entry schema's input type marks mileage and the money fields required,
// the form's (draft) one leaves them optional; both describe the same field values.
const fullResolver = zodResolver(fullSchema) as unknown as Resolver<
  MaintenanceFormInput,
  unknown,
  MaintenanceFormValues
>
const draftResolver = zodResolver(draftSchema)

// Every field explicit: reset() leaves a field it gets no value for showing its old input.
const blankValues = (): DefaultValues<MaintenanceFormInput> => ({
  date: todayIso(),
  mileage_km: '',
  type: 'oil_change',
  description: '',
  cost: '',
  currency: 'CZK',
  notes: '',
})

export function MaintenanceForm({
  onSubmit,
  isSubmitting,
  defaultValues,
  submitLabel,
  onCancel,
}: {
  onSubmit: (values: MaintenanceFormValues, options: { draft: boolean }) => Promise<unknown>
  isSubmitting: boolean
  defaultValues?: MaintenanceFormInput
  submitLabel?: string
  onCancel?: () => void
}) {
  // See FuelForm: the pressed submit button decides draft vs. complete.
  const modeRef = useRef<'full' | 'draft'>('full')
  const resolver: Resolver<MaintenanceFormInput, unknown, MaintenanceFormValues> = (
    values,
    context,
    options,
  ) =>
    modeRef.current === 'draft'
      ? draftResolver(values, context, options)
      : fullResolver(values, context, options)

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting: isFormSubmitting },
  } = useForm<MaintenanceFormInput, unknown, MaintenanceFormValues>({
    resolver,
    defaultValues: defaultValues ?? blankValues(),
  })

  const currency = watch('currency')
  const { data: rates } = useQuery({ queryKey: ['currency-rates'], queryFn: currencyApi.list })
  const currentRate = rates?.find((r) => r.currency === currency)?.rate_to_czk

  // The form is busy from submit through validation, the request and any confirm dialog.
  const busy = isSubmitting || isFormSubmitting

  return (
    <form
      onSubmit={handleSubmit(async (values) => {
        // See FuelForm: reset only after the server accepted the entry.
        try {
          await onSubmit(values, { draft: modeRef.current === 'draft' })
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
      <Field label="Typ" error={errors.type?.message}>
        <select className={inputClass} {...register('type')}>
          {SERVICE_TYPES.map((opt) => (
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
        <Field label="Popis">
          <input type="text" className={inputClass} {...register('description')} />
        </Field>
      </div>
      <div className="col-span-2">
        <Field label="Poznámka" error={errors.notes?.message}>
          <input type="text" className={inputClass} {...register('notes')} />
        </Field>
      </div>
      <div className="col-span-2 flex gap-2">
        <Button
          type="submit"
          disabled={busy}
          className="flex-1"
          onClick={() => (modeRef.current = 'full')}
        >
          {busy ? 'Ukládám…' : (submitLabel ?? 'Zapsat servis')}
        </Button>
        <Button
          type="submit"
          variant="secondary"
          disabled={busy}
          onClick={() => (modeRef.current = 'draft')}
        >
          Uložit jako rozpracované
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
