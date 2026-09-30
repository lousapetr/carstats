import { api } from './client'
import type { Dashboard, Period } from '../types'

export const dashboardApi = {
  get: (period: Period) =>
    api.get<Dashboard>(`/api/dashboard?period=${encodeURIComponent(period)}`),
}
