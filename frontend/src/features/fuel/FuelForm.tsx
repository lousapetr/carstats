import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { Button } from '../../components/ui/Button'
import { Field, inputClass } from '../../components/ui/Field'

const schema = z.object({
  date: z.string().min(1, 'Required'),
  mileage_km: z.coerce.number().positive('Must be positive'),
  liters: z.coerce.number().positive('Must be positive'),
  price_total: z.coerce.number().positive('Must be positive'),
  notes: z.string().optional(),
})

export type FuelFormValues = z.output<typeof schema>
type FuelFormInput = z.input<typeof schema>

export function FuelForm({
  onSubmit,
  isSubmitting,
}: {
  onSubmit: (values: FuelFormValues) => void
  isSubmitting: boolean
}) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FuelFormInput, unknown, FuelFormValues>({
    resolver: zodResolver(schema),
    defaultValues: { date: new Date().toISOString().slice(0, 10) },
  })

  return (
    <form
      onSubmit={handleSubmit((values) => {
        onSubmit(values)
        reset({ date: new Date().toISOString().slice(0, 10) })
      })}
      className="grid grid-cols-2 gap-3"
    >
      <Field label="Date" error={errors.date?.message}>
        <input type="date" className={inputClass} {...register('date')} />
      </Field>
      <Field label="Mileage (km)" error={errors.mileage_km?.message}>
        <input type="number" step="1" className={inputClass} {...register('mileage_km')} />
      </Field>
      <Field label="Liters" error={errors.liters?.message}>
        <input type="number" step="0.01" className={inputClass} {...register('liters')} />
      </Field>
      <Field label="Total price" error={errors.price_total?.message}>
        <input type="number" step="0.01" className={inputClass} {...register('price_total')} />
      </Field>
      <div className="col-span-2">
        <Field label="Notes">
          <input type="text" className={inputClass} {...register('notes')} />
        </Field>
      </div>
      <div className="col-span-2">
        <Button type="submit" disabled={isSubmitting} className="w-full">
          {isSubmitting ? 'Saving…' : 'Log fill-up'}
        </Button>
      </div>
    </form>
  )
}
