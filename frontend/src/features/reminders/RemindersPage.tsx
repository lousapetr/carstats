import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { remindersApi } from '../../api/reminders'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { StatusBadge } from '../../components/ui/StatusBadge'
import type { ReminderInput } from '../../types'
import { ReminderForm } from './ReminderForm'

export function RemindersPage() {
  const queryClient = useQueryClient()

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
      <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Reminders</h1>

      <Card>
        <ReminderForm
          onSubmit={(values) => createMutation.mutate(values)}
          isSubmitting={createMutation.isPending}
        />
      </Card>

      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}

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
                {reminder.due_date && `Due ${reminder.due_date}`}
                {reminder.due_date && reminder.due_mileage_km !== null && ' · '}
                {reminder.due_mileage_km !== null &&
                  `Due at ${reminder.due_mileage_km.toLocaleString()} km`}
              </div>
            </div>
            <div className="flex shrink-0 gap-2">
              <Button variant="secondary" onClick={() => completeMutation.mutate(reminder.id)}>
                Done
              </Button>
              <Button variant="danger" onClick={() => deleteMutation.mutate(reminder.id)}>
                Delete
              </Button>
            </div>
          </Card>
        ))}
        {reminders?.length === 0 && (
          <p className="text-sm text-gray-500 dark:text-gray-400">No active reminders.</p>
        )}
      </div>
    </div>
  )
}
