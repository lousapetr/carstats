import { api } from './client'
import type { Reminder, ReminderInput } from '../types'

export const remindersApi = {
  list: () => api.get<Reminder[]>('/api/reminders'),
  create: (data: ReminderInput, force = false) =>
    api.post<Reminder>(`/api/reminders${force ? '?force=true' : ''}`, data),
  update: (id: number, data: ReminderInput, force = false) =>
    api.put<Reminder>(`/api/reminders/${id}${force ? '?force=true' : ''}`, data),
  complete: (id: number) => api.post<Reminder>(`/api/reminders/${id}/complete`),
  remove: (id: number) => api.delete(`/api/reminders/${id}`),
}
