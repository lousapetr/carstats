import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { carApi } from '../../api/car'
import { exportApi } from '../../api/export'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Field, inputClass } from '../../components/ui/Field'
import type { CarProfileInput } from '../../types'

const linkButtonClass =
  'rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-900 transition hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:hover:bg-gray-800'

export function SettingsPage() {
  const queryClient = useQueryClient()

  const { data: car } = useQuery({ queryKey: ['car'], queryFn: carApi.get })

  const [form, setForm] = useState<CarProfileInput>({ name: '', make: '', model: '', year: null })

  useEffect(() => {
    if (car) {
      setForm({ name: car.name, make: car.make, model: car.model, year: car.year })
    }
  }, [car])

  const updateCarMutation = useMutation({
    mutationFn: (data: CarProfileInput) => carApi.update(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['car'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Nastavení</h1>

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
          Údaje o autě
        </h2>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            updateCarMutation.mutate(form)
          }}
          className="grid grid-cols-2 gap-3"
        >
          <div className="col-span-2">
            <Field label="Přezdívka">
              <input
                type="text"
                className={inputClass}
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </Field>
          </div>
          <Field label="Značka">
            <input
              type="text"
              className={inputClass}
              value={form.make}
              onChange={(e) => setForm({ ...form, make: e.target.value })}
            />
          </Field>
          <Field label="Model">
            <input
              type="text"
              className={inputClass}
              value={form.model}
              onChange={(e) => setForm({ ...form, model: e.target.value })}
            />
          </Field>
          <Field label="Rok výroby">
            <input
              type="number"
              className={inputClass}
              value={form.year ?? ''}
              onChange={(e) =>
                setForm({ ...form, year: e.target.value ? Number(e.target.value) : null })
              }
            />
          </Field>
          <div className="col-span-2">
            <Button type="submit" disabled={updateCarMutation.isPending}>
              {updateCarMutation.isPending ? 'Ukládám…' : 'Uložit'}
            </Button>
          </div>
        </form>
      </Card>

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
          Export dat
        </h2>
        <div className="flex flex-wrap gap-2">
          <a href={exportApi.fuelCsvUrl} className={linkButtonClass}>
            Export tankování (CSV)
          </a>
          <a href={exportApi.maintenanceCsvUrl} className={linkButtonClass}>
            Export servisu (CSV)
          </a>
        </div>
      </Card>
    </div>
  )
}
