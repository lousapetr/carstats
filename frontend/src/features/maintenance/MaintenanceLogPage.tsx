import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { maintenanceApi } from '../../api/maintenance'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import type { ServiceEntryInput } from '../../types'
import { AttachmentUploader } from './AttachmentUploader'
import { MaintenanceForm } from './MaintenanceForm'

const TYPE_LABELS: Record<string, string> = {
  oil_change: 'Oil change',
  tires: 'Tires',
  engine_service: 'Engine service',
  other: 'Other',
}

export function MaintenanceLogPage() {
  const queryClient = useQueryClient()

  const { data: entries, isLoading } = useQuery({
    queryKey: ['service-entries'],
    queryFn: maintenanceApi.list,
  })

  const createMutation = useMutation({
    mutationFn: (data: ServiceEntryInput) => maintenanceApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['service-entries'] })
      queryClient.invalidateQueries({ queryKey: ['car'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => maintenanceApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['service-entries'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Maintenance log</h1>

      <Card>
        <MaintenanceForm
          onSubmit={(values) => createMutation.mutate(values)}
          isSubmitting={createMutation.isPending}
        />
      </Card>

      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}

      <div className="flex flex-col gap-2">
        {entries?.map((entry) => (
          <Card key={entry.id}>
            <div className="flex items-start justify-between">
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {TYPE_LABELS[entry.type]} · {entry.date}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {entry.mileage_km.toLocaleString()} km · {entry.cost.toFixed(2)}
                </div>
                {entry.description && (
                  <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {entry.description}
                  </div>
                )}
              </div>
              <Button variant="danger" onClick={() => deleteMutation.mutate(entry.id)}>
                Delete
              </Button>
            </div>
            <AttachmentUploader entryId={entry.id} attachments={entry.attachments} />
          </Card>
        ))}
        {entries?.length === 0 && (
          <p className="text-sm text-gray-500 dark:text-gray-400">No service entries yet.</p>
        )}
      </div>
    </div>
  )
}
