import { api } from './client'
import type { CarProfile } from '../types'

export const carApi = {
  get: () => api.get<CarProfile>('/api/car'),
  update: (data: { make: string; model: string; year: number | null }) =>
    api.put<CarProfile>('/api/car', data),
}
