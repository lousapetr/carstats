import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { carApi } from '../../api/car'
import { currencyApi } from '../../api/currency'
import { exportApi } from '../../api/export'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Field, inputClass } from '../../components/ui/Field'
import { CURRENCY_LABELS } from '../../lib/currencies'
import type { CarProfileInput, Currency } from '../../types'

const linkButtonClass =
  'rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-900 transition hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:hover:bg-gray-800'

export function SettingsPage() {
  const queryClient = useQueryClient()

  const { data: car } = useQuery({ queryKey: ['car'], queryFn: carApi.get })
  const { data: rates } = useQuery({ queryKey: ['currency-rates'], queryFn: currencyApi.list })

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

  const updateRateMutation = useMutation({
    mutationFn: ({ currency, rate }: { currency: Currency; rate: number }) =>
      currencyApi.update(currency, rate),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['currency-rates'] }),
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
        <h2 className="mb-1 text-sm font-semibold text-gray-900 dark:text-gray-100">
          Kurzy měn
        </h2>
        <p className="mb-3 text-xs text-gray-500 dark:text-gray-400">
          Kurz vůči Kč se použije při zápisu nové položky v dané měně a zůstane u ní uložený,
          takže pozdější změna kurzu neovlivní minulé záznamy.
        </p>
        <div className="flex flex-col gap-2">
          {rates?.map((rate) => (
            <div key={rate.currency} className="flex items-center justify-between gap-2">
              <span className="text-sm text-gray-700 dark:text-gray-300">
                {CURRENCY_LABELS[rate.currency]}
              </span>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  step="0.01"
                  className={`${inputClass} w-28`}
                  defaultValue={rate.rate_to_czk}
                  onBlur={(e) => {
                    const value = Number(e.target.value)
                    if (value > 0 && value !== rate.rate_to_czk) {
                      updateRateMutation.mutate({ currency: rate.currency, rate: value })
                    }
                  }}
                />
                <span className="text-xs text-gray-400">Kč</span>
              </div>
            </div>
          ))}
        </div>
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
