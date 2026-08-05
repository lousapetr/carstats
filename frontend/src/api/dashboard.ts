import { api } from './client'
import type { CostBreakdown, DashboardSummary, FuelTrendPoint } from '../types'

export const dashboardApi = {
  summary: () => api.get<DashboardSummary>('/api/dashboard/summary'),
  fuelTrend: () => api.get<FuelTrendPoint[]>('/api/dashboard/fuel-trend'),
  costBreakdown: () => api.get<CostBreakdown>('/api/dashboard/cost-breakdown'),
}
