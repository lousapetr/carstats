import { api } from './client'
import type { FuelEntry, FuelEntryInput } from '../types'

export const fuelApi = {
  list: () => api.get<FuelEntry[]>('/api/fuel-entries'),
  create: (data: FuelEntryInput) => api.post<FuelEntry>('/api/fuel-entries', data),
  remove: (id: number) => api.delete(`/api/fuel-entries/${id}`),
}
