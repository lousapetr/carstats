import { api } from './client'
import type { Reminder, ReminderInput } from '../types'

export const remindersApi = {
  list: () => api.get<Reminder[]>('/api/reminders'),
  create: (data: ReminderInput) => api.post<Reminder>('/api/reminders', data),
  complete: (id: number) => api.post<Reminder>(`/api/reminders/${id}/complete`),
  remove: (id: number) => api.delete(`/api/reminders/${id}`),
}
