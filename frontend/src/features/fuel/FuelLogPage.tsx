import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { fuelApi } from '../../api/fuel'
import { ActionMenu } from '../../components/ui/ActionMenu'
import { Card } from '../../components/ui/Card'
import { ErrorState } from '../../components/ui/ErrorState'
import { LoadingState } from '../../components/ui/LoadingState'
import { confirmDialog } from '../../lib/confirmBus'
import { formatDate } from '../../lib/dates'
import {
  formatConsumption,
  formatCzk,
  formatKm,
  formatLiters,
  formatMoney,
  formatMoneyPerLiter,
} from '../../lib/format'
import type { FuelEntry, FuelEntryInput } from '../../types'
import { FuelForm } from './FuelForm'

function toFormValues(entry: FuelEntry) {
  return {
    date: entry.date,
    mileage_km: entry.mileage_km,
    liters: entry.liters,
    price_per_liter: entry.price_per_liter,
    currency: entry.currency,
    full_tank: entry.full_tank,
    notes: entry.notes ?? undefined,
  }
}

export function FuelLogPage() {
  const queryClient = useQueryClient()
  const [editingEntry, setEditingEntry] = useState<FuelEntry | null>(null)

  const { data: entries, isPending, isError, refetch } = useQuery({
    queryKey: ['fuel-entries'],
    queryFn: fuelApi.list,
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['fuel-entries'] })
    queryClient.invalidateQueries({ queryKey: ['car'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  }

  const createMutation = useMutation({
    mutationFn: (data: FuelEntryInput) => fuelApi.create(data),
    onSuccess: invalidate,
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: FuelEntryInput }) => fuelApi.update(id, data),
    onSuccess: () => {
      invalidate()
      setEditingEntry(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => fuelApi.remove(id),
    onSuccess: invalidate,
  })

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Tankování</h1>

      <Card>
        <FuelForm
          key={editingEntry?.id ?? 'new'}
          defaultValues={editingEntry ? toFormValues(editingEntry) : undefined}
          submitLabel={editingEntry ? 'Uložit změny' : undefined}
          onCancel={editingEntry ? () => setEditingEntry(null) : undefined}
          onSubmit={(values) =>
            editingEntry
              ? updateMutation.mutateAsync({ id: editingEntry.id, data: values })
              : createMutation.mutateAsync(values)
          }
          isSubmitting={createMutation.isPending || updateMutation.isPending}
        />
      </Card>

      {isPending && <LoadingState />}
      {isError && (
        <ErrorState message="Tankování se nepodařilo načíst." onRetry={() => void refetch()} />
      )}

      <div className="flex flex-col gap-2">
        {entries?.map((entry) => (
          <Card key={entry.id} className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {formatDate(entry.date)} · {formatKm(entry.mileage_km)}
                {!entry.full_tank && (
                  <span className="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-xs font-normal text-amber-800 dark:bg-amber-900 dark:text-amber-200">
                    částečné tankování
                  </span>
                )}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {formatLiters(entry.liters)} ·{' '}
                {formatMoneyPerLiter(entry.price_per_liter, entry.currency)} ·{' '}
                {formatMoney(entry.price_total, entry.currency)}
                {entry.currency !== 'CZK' && ` (${formatCzk(entry.price_total_czk)})`}
                {entry.full_tank &&
                  (entry.consumption_l_per_100km !== null
                    ? ` · ${formatConsumption(entry.consumption_l_per_100km)}`
                    : ' · spotřeba: –')}
              </div>
              {entry.notes && (
                <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">{entry.notes}</div>
              )}
            </div>
            <ActionMenu
              actions={[
                { label: 'Upravit', onClick: () => setEditingEntry(entry) },
                {
                  label: 'Smazat',
                  danger: true,
                  onClick: async () => {
                    if (await confirmDialog('Opravdu smazat toto tankování?')) {
                      deleteMutation.mutate(entry.id)
                    }
                  },
                },
              ]}
            />
          </Card>
        ))}
        {entries?.length === 0 && (
          <p className="text-sm text-gray-500 dark:text-gray-400">Zatím žádná tankování.</p>
        )}
      </div>
    </div>
  )
}
