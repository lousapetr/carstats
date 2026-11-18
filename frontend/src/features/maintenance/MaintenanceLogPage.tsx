import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRef, useState } from 'react'
import { maintenanceApi } from '../../api/maintenance'
import { ActionMenu } from '../../components/ui/ActionMenu'
import { Card } from '../../components/ui/Card'
import { ErrorState } from '../../components/ui/ErrorState'
import { LoadingState } from '../../components/ui/LoadingState'
import { confirmDialog } from '../../lib/confirmBus'
import { formatDate } from '../../lib/dates'
import { formatCzk, formatKm, formatMoney } from '../../lib/format'
import { SERVICE_TYPE_LABELS } from '../../lib/serviceTypes'
import { submitConfirmingDuplicate } from '../../lib/submitConfirmingDuplicate'
import { useEditParam } from '../../lib/useEditParam'
import type { ServiceEntry, ServiceEntryInput } from '../../types'
import { AttachmentUploader } from './AttachmentUploader'
import { MaintenanceForm } from './MaintenanceForm'

function toFormValues(entry: ServiceEntry) {
  return {
    date: entry.date ?? '',
    mileage_km: entry.mileage_km ?? '',
    type: entry.type,
    description: entry.description ?? undefined,
    cost: entry.cost ?? '',
    currency: entry.currency,
    notes: entry.notes ?? undefined,
  }
}

const DASH = '–'

export function MaintenanceLogPage() {
  const queryClient = useQueryClient()
  const [editingEntry, setEditingEntry] = useState<ServiceEntry | null>(null)
  const formRef = useRef<HTMLDivElement>(null)

  const entriesQuery = useQuery({ queryKey: ['service-entries'], queryFn: maintenanceApi.list })
  const { data: entries, isPending, isError, refetch } = entriesQuery

  useEditParam(entriesQuery, (entry) => {
    setEditingEntry(entry)
    formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['service-entries'] })
    queryClient.invalidateQueries({ queryKey: ['car'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  }

  const createMutation = useMutation({
    mutationFn: ({ data, force }: { data: ServiceEntryInput; force: boolean }) =>
      maintenanceApi.create(data, force),
    onSuccess: invalidate,
    meta: {
      successMessage: (entry) =>
        (entry as ServiceEntry).is_draft ? 'Uloženo jako rozpracované.' : 'Servisní záznam uložen.',
      confirmsDuplicate: true,
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      data,
      force,
    }: {
      id: number
      data: ServiceEntryInput
      force: boolean
    }) =>
      maintenanceApi.update(id, data, force),
    onSuccess: () => {
      invalidate()
      setEditingEntry(null)
    },
    meta: {
      successMessage: (entry) =>
        (entry as ServiceEntry).is_draft ? 'Uloženo jako rozpracované.' : 'Změny uloženy.',
      confirmsDuplicate: true,
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => maintenanceApi.remove(id),
    onSuccess: invalidate,
  })

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Servis a údržba</h1>

      <div ref={formRef}>
        <Card>
          <MaintenanceForm
            key={editingEntry?.id ?? 'new'}
            defaultValues={editingEntry ? toFormValues(editingEntry) : undefined}
            submitLabel={
              editingEntry ? (editingEntry.is_draft ? 'Dokončit' : 'Uložit změny') : undefined
            }
            onCancel={editingEntry ? () => setEditingEntry(null) : undefined}
            onSubmit={(values, { draft }) =>
              submitConfirmingDuplicate((force) =>
                editingEntry
                  ? updateMutation.mutateAsync({
                      id: editingEntry.id,
                      data: { ...values, is_draft: draft },
                      force,
                    })
                  : createMutation.mutateAsync({ data: { ...values, is_draft: draft }, force }),
              )
            }
            isSubmitting={createMutation.isPending || updateMutation.isPending}
          />
        </Card>
      </div>

      {isPending && <LoadingState />}
      {isError && (
        <ErrorState message="Servisní záznamy se nepodařilo načíst." onRetry={() => void refetch()} />
      )}

      <div className="flex flex-col gap-2">
        {entries?.map((entry) => (
          <Card key={entry.id}>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {SERVICE_TYPE_LABELS[entry.type]} · {entry.date ? formatDate(entry.date) : DASH}
                  {entry.is_draft && (
                    <span className="ml-2 rounded bg-sky-100 px-1.5 py-0.5 text-xs font-normal text-sky-800 dark:bg-sky-900 dark:text-sky-200">
                      rozpracované
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {entry.mileage_km !== null ? formatKm(entry.mileage_km) : DASH} ·{' '}
                  {entry.cost !== null ? formatMoney(entry.cost, entry.currency) : DASH}
                  {entry.currency !== 'CZK' &&
                    entry.cost_czk !== null &&
                    ` (${formatCzk(entry.cost_czk)})`}
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
