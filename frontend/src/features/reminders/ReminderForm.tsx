import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { Button } from '../../components/ui/Button'
import { Field, inputClass } from '../../components/ui/Field'

const emptyToUndefined = (val: unknown) => (val === '' ? undefined : val)

const schema = z.object({
  title: z.string().min(1, 'Povinné pole'),
  due_date: z.preprocess(emptyToUndefined, z.string().optional()),
  due_mileage_km: z.preprocess(emptyToUndefined, z.coerce.number().positive().optional()),
  recurrence_days: z.preprocess(emptyToUndefined, z.coerce.number().int().positive().optional()),
  recurrence_km: z.preprocess(emptyToUndefined, z.coerce.number().positive().optional()),
  notes: z.string().optional(),
})

export type ReminderFormValues = z.output<typeof schema>
type ReminderFormInput = z.input<typeof schema>

export function ReminderForm({
  onSubmit,
  isSubmitting,
  defaultValues,
  submitLabel,
  onCancel,
}: {
  onSubmit: (values: ReminderFormValues) => void
  isSubmitting: boolean
  defaultValues?: ReminderFormInput
  submitLabel?: string
  onCancel?: () => void
}) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ReminderFormInput, unknown, ReminderFormValues>({
    resolver: zodResolver(schema),
    defaultValues,
  })

  return (
    <form
      onSubmit={handleSubmit((values) => {
        onSubmit(values)
        if (!defaultValues) {
          reset({})
        }
      })}
      className="grid grid-cols-2 gap-3"
    >
      <div className="col-span-2">
        <Field label="Název" error={errors.title?.message}>
          <input type="text" className={inputClass} {...register('title')} />
        </Field>
      </div>
      <Field label="Termín (volitelné)" error={errors.due_date?.message}>
        <input type="date" className={inputClass} {...register('due_date')} />
      </Field>
      <Field label="Najeto km (volitelné)" error={errors.due_mileage_km?.message}>
        <input type="number" step="1" className={inputClass} {...register('due_mileage_km')} />
      </Field>
      <Field label="Opakovat po (dnech, volitelné)" error={errors.recurrence_days?.message}>
        <input type="number" step="1" className={inputClass} {...register('recurrence_days')} />
      </Field>
      <Field label="Opakovat po (km, volitelné)" error={errors.recurrence_km?.message}>
        <input type="number" step="1" className={inputClass} {...register('recurrence_km')} />
      </Field>
      <div className="col-span-2">
        <Field label="Poznámka">
          <input type="text" className={inputClass} {...register('notes')} />
        </Field>
      </div>
      <div className="col-span-2 flex gap-2">
        <Button type="submit" disabled={isSubmitting} className="flex-1">
          {isSubmitting ? 'Ukládám…' : (submitLabel ?? 'Přidat připomínku')}
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
