import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { Button } from '../../components/ui/Button'
import { Field, inputClass } from '../../components/ui/Field'

const schema = z.object({
  date: z.string().min(1, 'Required'),
  mileage_km: z.coerce.number().positive('Must be positive'),
  type: z.enum(['oil_change', 'tires', 'engine_service', 'other']),
  description: z.string().optional(),
  cost: z.coerce.number().min(0, 'Must be 0 or more'),
  notes: z.string().optional(),
})

export type MaintenanceFormValues = z.output<typeof schema>
type MaintenanceFormInput = z.input<typeof schema>

const TYPE_OPTIONS: { value: MaintenanceFormValues['type']; label: string }[] = [
  { value: 'oil_change', label: 'Oil change' },
  { value: 'tires', label: 'Tires' },
  { value: 'engine_service', label: 'Engine service' },
  { value: 'other', label: 'Other' },
]

export function MaintenanceForm({
  onSubmit,
  isSubmitting,
}: {
  onSubmit: (values: MaintenanceFormValues) => void
  isSubmitting: boolean
}) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<MaintenanceFormInput, unknown, MaintenanceFormValues>({
    resolver: zodResolver(schema),
    defaultValues: { date: new Date().toISOString().slice(0, 10), type: 'oil_change' },
  })

  return (
    <form
      onSubmit={handleSubmit((values) => {
        onSubmit(values)
        reset({ date: new Date().toISOString().slice(0, 10), type: 'oil_change' })
      })}
      className="grid grid-cols-2 gap-3"
    >
      <Field label="Date" error={errors.date?.message}>
        <input type="date" className={inputClass} {...register('date')} />
      </Field>
      <Field label="Mileage (km)" error={errors.mileage_km?.message}>
        <input type="number" step="1" className={inputClass} {...register('mileage_km')} />
      </Field>
      <Field label="Type" error={errors.type?.message}>
        <select className={inputClass} {...register('type')}>
          {TYPE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Cost" error={errors.cost?.message}>
        <input type="number" step="0.01" className={inputClass} {...register('cost')} />
      </Field>
      <div className="col-span-2">
        <Field label="Description">
          <input type="text" className={inputClass} {...register('description')} />
        </Field>
      </div>
      <div className="col-span-2">
        <Field label="Notes">
          <input type="text" className={inputClass} {...register('notes')} />
        </Field>
      </div>
      <div className="col-span-2">
        <Button type="submit" disabled={isSubmitting} className="w-full">
          {isSubmitting ? 'Saving…' : 'Log service'}
        </Button>
      </div>
    </form>
  )
}
