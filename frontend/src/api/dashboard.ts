import { api } from './client'
import type { CostBreakdown, Dashboard, DashboardSummary, FuelTrendPoint, Period } from '../types'

export const dashboardApi = {
  get: (period: Period) =>
    api.get<Dashboard>(`/api/dashboard?period=${encodeURIComponent(period)}`),
  summary: () => api.get<DashboardSummary>('/api/dashboard/summary'),
  fuelTrend: () => api.get<FuelTrendPoint[]>('/api/dashboard/fuel-trend'),
  costBreakdown: () => api.get<CostBreakdown>('/api/dashboard/cost-breakdown'),
}
