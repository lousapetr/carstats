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

const emptyToUndefined = (val: unknown) => (val === '' ? undefined : val)

const fullSchema = z.object({
  date: z.string().min(1, 'Povinné pole'),
  mileage_km: z.coerce.number().positive('Musí být kladné číslo'),
  liters: z.coerce.number().positive('Musí být kladné číslo'),
  price_per_liter: z.coerce.number().positive('Musí být kladné číslo'),
  currency: z.enum(CURRENCY_CODES),
  full_tank: z.boolean().default(true),
  notes: z.string().max(1000, 'Nejvýše 1000 znaků').optional(),
})

const optionalPositive = z.preprocess(
  emptyToUndefined,
  z.coerce.number().positive('Musí být kladné číslo').optional(),
)

// A draft may leave everything but currency and full_tank empty, as long as one
// substantive field is filled in. That error sits on `notes` because react-hook-form
// drops `root` errors on submit.
const draftSchema = z
  .object({
    date: z.string().transform((v) => v || undefined),
    mileage_km: optionalPositive,
    liters: optionalPositive,
    price_per_liter: optionalPositive,
    currency: z.enum(CURRENCY_CODES),
    full_tank: z.boolean().default(true),
    notes: z.string().max(1000, 'Nejvýše 1000 znaků').optional(),
  })
  .refine(
    (v) =>
      v.mileage_km !== undefined ||
      v.liters !== undefined ||
      v.price_per_liter !== undefined ||
      !!v.notes?.trim(),
    { message: 'Vyplňte aspoň jeden údaj.', path: ['notes'] },
  )

/** Draft output is the loosest shape; a complete entry's values fit it too. */
export type FuelFormValues = z.output<typeof draftSchema>
type FuelFormInput = z.input<typeof draftSchema>

// The complete-entry schema's input type marks mileage and the money fields required,
// the form's (draft) one leaves them optional; both describe the same field values.
const fullResolver = zodResolver(fullSchema) as unknown as Resolver<
  FuelFormInput,
  unknown,
  FuelFormValues
>
const draftResolver = zodResolver(draftSchema)

// Every field explicit: reset() leaves a field it gets no value for showing its old input.
const blankValues = (): DefaultValues<FuelFormInput> => ({
  date: todayIso(),
  mileage_km: '',
  liters: '',
  price_per_liter: '',
  currency: 'CZK',
  full_tank: true,
  notes: '',
})

export function FuelForm({
  onSubmit,
  isSubmitting,
  defaultValues,
  submitLabel,
  onCancel,
}: {
  onSubmit: (values: FuelFormValues, options: { draft: boolean }) => Promise<unknown>
  isSubmitting: boolean
  defaultValues?: FuelFormInput
  submitLabel?: string
  onCancel?: () => void
}) {
  // Set by whichever submit button was pressed (Enter presses the primary one),
  // so validation and the submit handler agree on draft vs. complete.
  const modeRef = useRef<'full' | 'draft'>('full')
  const resolver: Resolver<FuelFormInput, unknown, FuelFormValues> = (values, context, options) =>
    modeRef.current === 'draft'
      ? draftResolver(values, context, options)
      : fullResolver(values, context, options)

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting: isFormSubmitting },
  } = useForm<FuelFormInput, unknown, FuelFormValues>({
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
        // Clear the form only once the server accepted the entry: a rejected
        // one (e.g. the mileage-consistency guard) has to stay put to be
        // corrected. The failure itself is toasted by the shared MutationCache.
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
          {busy ? 'Ukládám…' : (submitLabel ?? 'Zapsat tankování')}
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
