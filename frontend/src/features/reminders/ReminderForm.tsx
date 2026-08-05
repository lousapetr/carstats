import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { Button } from '../../components/ui/Button'
import { Field, inputClass } from '../../components/ui/Field'

const emptyToUndefined = (val: unknown) => (val === '' ? undefined : val)

const schema = z.object({
  title: z.string().min(1, 'Required'),
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
}: {
  onSubmit: (values: ReminderFormValues) => void
  isSubmitting: boolean
}) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ReminderFormInput, unknown, ReminderFormValues>({ resolver: zodResolver(schema) })

  return (
    <form
      onSubmit={handleSubmit((values) => {
        onSubmit(values)
        reset({})
      })}
      className="grid grid-cols-2 gap-3"
    >
      <div className="col-span-2">
        <Field label="Title" error={errors.title?.message}>
          <input type="text" className={inputClass} {...register('title')} />
        </Field>
      </div>
      <Field label="Due date (optional)" error={errors.due_date?.message}>
        <input type="date" className={inputClass} {...register('due_date')} />
      </Field>
      <Field label="Due mileage, km (optional)" error={errors.due_mileage_km?.message}>
        <input type="number" step="1" className={inputClass} {...register('due_mileage_km')} />
      </Field>
      <Field label="Repeat every N days (optional)" error={errors.recurrence_days?.message}>
        <input type="number" step="1" className={inputClass} {...register('recurrence_days')} />
      </Field>
      <Field label="Repeat every N km (optional)" error={errors.recurrence_km?.message}>
        <input type="number" step="1" className={inputClass} {...register('recurrence_km')} />
      </Field>
      <div className="col-span-2">
        <Field label="Notes">
          <input type="text" className={inputClass} {...register('notes')} />
        </Field>
      </div>
      <div className="col-span-2">
        <Button type="submit" disabled={isSubmitting} className="w-full">
          {isSubmitting ? 'Saving…' : 'Add reminder'}
        </Button>
      </div>
    </form>
  )
}
