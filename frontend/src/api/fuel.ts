import { api } from './client'
import type { FuelEntry, FuelEntryInput } from '../types'

export const fuelApi = {
  list: () => api.get<FuelEntry[]>('/api/fuel-entries'),
  create: (data: FuelEntryInput, force = false) =>
    api.post<FuelEntry>(`/api/fuel-entries${force ? '?force=true' : ''}`, data),
  update: (id: number, data: FuelEntryInput, force = false) =>
    api.put<FuelEntry>(`/api/fuel-entries/${id}${force ? '?force=true' : ''}`, data),
  remove: (id: number) => api.delete(`/api/fuel-entries/${id}`),
}
