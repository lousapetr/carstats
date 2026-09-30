import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { maintenanceApi } from '../../api/maintenance'
import { ActionMenu } from '../../components/ui/ActionMenu'
import { Card } from '../../components/ui/Card'
import { confirmDialog } from '../../lib/confirmBus'
import { formatDate } from '../../lib/dates'
import { formatCzk, formatKm, formatMoney } from '../../lib/format'
import { SERVICE_TYPE_LABELS } from '../../lib/serviceTypes'
import type { ServiceEntry, ServiceEntryInput } from '../../types'
import { AttachmentUploader } from './AttachmentUploader'
import { MaintenanceForm } from './MaintenanceForm'

function toFormValues(entry: ServiceEntry) {
  return {
    date: entry.date,
    mileage_km: entry.mileage_km,
    type: entry.type,
    description: entry.description ?? undefined,
    cost: entry.cost,
    currency: entry.currency,
    notes: entry.notes ?? undefined,
  }
}

export function MaintenanceLogPage() {
  const queryClient = useQueryClient()
  const [editingEntry, setEditingEntry] = useState<ServiceEntry | null>(null)

  const { data: entries, isLoading } = useQuery({
    queryKey: ['service-entries'],
    queryFn: maintenanceApi.list,
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['service-entries'] })
    queryClient.invalidateQueries({ queryKey: ['car'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  }

  const createMutation = useMutation({
    mutationFn: (data: ServiceEntryInput) => maintenanceApi.create(data),
    onSuccess: invalidate,
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: ServiceEntryInput }) =>
      maintenanceApi.update(id, data),
    onSuccess: () => {
      invalidate()
      setEditingEntry(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => maintenanceApi.remove(id),
    onSuccess: invalidate,
  })

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Servis a údržba</h1>

      <Card>
        <MaintenanceForm
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

      {isLoading && <p className="text-sm text-gray-500">Načítám…</p>}

      <div className="flex flex-col gap-2">
        {entries?.map((entry) => (
          <Card key={entry.id}>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {SERVICE_TYPE_LABELS[entry.type]} · {formatDate(entry.date)}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {formatKm(entry.mileage_km)} · {formatMoney(entry.cost, entry.currency)}
                  {entry.currency !== 'CZK' && ` (${formatCzk(entry.cost_czk)})`}
                </div>
                {entry.description && (
                  <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {entry.description}
                  </div>
                )}
              </div>
              <ActionMenu
                actions={[
                  { label: 'Upravit', onClick: () => setEditingEntry(entry) },
                  {
                    label: 'Smazat',
                    danger: true,
                    onClick: async () => {
                      if (await confirmDialog('Opravdu smazat tento záznam servisu?')) {
                        deleteMutation.mutate(entry.id)
                      }
                    },
                  },
                ]}
              />
            </div>
            <AttachmentUploader entryId={entry.id} attachments={entry.attachments} />
          </Card>
        ))}
        {entries?.length === 0 && (
          <p className="text-sm text-gray-500 dark:text-gray-400">Zatím žádné záznamy servisu.</p>
        )}
      </div>
    </div>
  )
}
