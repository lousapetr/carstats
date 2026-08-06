import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { remindersApi } from '../../api/reminders'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StatusBadge } from '../../components/ui/StatusBadge'
import type { Reminder, ReminderInput } from '../../types'
import { ReminderForm } from './ReminderForm'

function toFormValues(reminder: Reminder) {
  return {
    title: reminder.title,
    due_date: reminder.due_date ?? undefined,
    due_mileage_km: reminder.due_mileage_km ?? undefined,
    recurrence_days: reminder.recurrence_days ?? undefined,
    recurrence_km: reminder.recurrence_km ?? undefined,
    notes: reminder.notes ?? undefined,
  }
}

export function RemindersPage() {
  const queryClient = useQueryClient()
  const [editingReminder, setEditingReminder] = useState<Reminder | null>(null)

  const { data: reminders, isLoading } = useQuery({
    queryKey: ['reminders'],
    queryFn: remindersApi.list,
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['reminders'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  }

  const createMutation = useMutation({
    mutationFn: (data: ReminderInput) => remindersApi.create(data),
    onSuccess: invalidate,
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: ReminderInput }) =>
      remindersApi.update(id, data),
    onSuccess: () => {
      invalidate()
      setEditingReminder(null)
    },
  })

  const completeMutation = useMutation({
    mutationFn: (id: number) => remindersApi.complete(id),
    onSuccess: invalidate,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => remindersApi.remove(id),
    onSuccess: invalidate,
  })

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Připomínky</h1>

      <Card>
        <ReminderForm
          key={editingReminder?.id ?? 'new'}
          defaultValues={editingReminder ? toFormValues(editingReminder) : undefined}
          submitLabel={editingReminder ? 'Uložit změny' : undefined}
          onCancel={editingReminder ? () => setEditingReminder(null) : undefined}
          onSubmit={(values) => {
            if (editingReminder) {
              updateMutation.mutate({ id: editingReminder.id, data: values })
            } else {
              createMutation.mutate(values)
            }
          }}
          isSubmitting={createMutation.isPending || updateMutation.isPending}
        />
      </Card>

      {isLoading && <p className="text-sm text-gray-500">Načítám…</p>}

      <div className="flex flex-col gap-2">
        {reminders?.map((reminder) => (
          <Card key={reminder.id} className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
                  {reminder.title}
                </span>
                <StatusBadge status={reminder.status} />
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {reminder.due_date && `Termín ${reminder.due_date}`}
                {reminder.due_date && reminder.due_mileage_km !== null && ' · '}
                {reminder.due_mileage_km !== null &&
                  `Při ${reminder.due_mileage_km.toLocaleString()} km`}
              </div>
            </div>
            <div className="flex shrink-0 gap-2">
              <Button variant="secondary" onClick={() => setEditingReminder(reminder)}>
                Upravit
              </Button>
              <Button variant="secondary" onClick={() => completeMutation.mutate(reminder.id)}>
                Hotovo
              </Button>
              <Button variant="danger" onClick={() => deleteMutation.mutate(reminder.id)}>
                Smazat
              </Button>
            </div>
          </Card>
        ))}
        {reminders?.length === 0 && (
          <p className="text-sm text-gray-500 dark:text-gray-400">Žádné aktivní připomínky.</p>
        )}
      </div>
    </div>
  )
}
