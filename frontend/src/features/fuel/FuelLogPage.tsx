import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fuelApi } from '../../api/fuel'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import type { FuelEntryInput } from '../../types'
import { FuelForm } from './FuelForm'

export function FuelLogPage() {
  const queryClient = useQueryClient()

  const { data: entries, isLoading } = useQuery({
    queryKey: ['fuel-entries'],
    queryFn: fuelApi.list,
  })

  const createMutation = useMutation({
    mutationFn: (data: FuelEntryInput) => fuelApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fuel-entries'] })
      queryClient.invalidateQueries({ queryKey: ['car'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => fuelApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fuel-entries'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Fuel log</h1>

      <Card>
        <FuelForm
          onSubmit={(values) => createMutation.mutate(values)}
          isSubmitting={createMutation.isPending}
        />
      </Card>

      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}

      <div className="flex flex-col gap-2">
        {entries?.map((entry) => (
          <Card key={entry.id} className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {entry.date} · {entry.mileage_km.toLocaleString()} km
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {entry.liters} L · {entry.price_total.toFixed(2)} ({entry.price_per_liter}/L)
                {entry.consumption_l_per_100km !== null &&
                  ` · ${entry.consumption_l_per_100km} L/100km`}
              </div>
              {entry.notes && (
                <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">{entry.notes}</div>
              )}
            </div>
            <Button variant="danger" onClick={() => deleteMutation.mutate(entry.id)}>
              Delete
            </Button>
          </Card>
        ))}
        {entries?.length === 0 && (
          <p className="text-sm text-gray-500 dark:text-gray-400">No fill-ups logged yet.</p>
        )}
      </div>
    </div>
  )
}
