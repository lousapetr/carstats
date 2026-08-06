import { api } from './client'
import type { CarProfile, CarProfileInput } from '../types'

export const carApi = {
  get: () => api.get<CarProfile>('/api/car'),
  update: (data: CarProfileInput) => api.put<CarProfile>('/api/car', data),
}
