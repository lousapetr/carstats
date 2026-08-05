export interface CarProfile {
  make: string
  model: string
  year: number | null
  current_mileage_km: number
}

export interface FuelEntry {
  id: number
  date: string
  mileage_km: number
  liters: number
  price_total: number
  notes: string | null
  price_per_liter: number
  consumption_l_per_100km: number | null
}

export interface FuelEntryInput {
  date: string
  mileage_km: number
  liters: number
  price_total: number
  notes?: string | null
}

export type ServiceType = 'oil_change' | 'tires' | 'engine_service' | 'other'

export interface Attachment {
  id: number
  filename: string
  content_type: string
}

export interface ServiceEntry {
  id: number
  date: string
  mileage_km: number
  type: ServiceType
  description: string | null
  cost: number
  notes: string | null
  attachments: Attachment[]
}

export interface ServiceEntryInput {
  date: string
  mileage_km: number
  type: ServiceType
  description?: string | null
  cost: number
  notes?: string | null
}

export type ReminderStatus = 'ok' | 'due_soon' | 'overdue'

export interface Reminder {
  id: number
  title: string
  notes: string | null
  due_date: string | null
  due_mileage_km: number | null
  recurrence_days: number | null
  recurrence_km: number | null
  completed_at: string | null
  status: ReminderStatus
}

export interface ReminderInput {
  title: string
  notes?: string | null
  due_date?: string | null
  due_mileage_km?: number | null
  recurrence_days?: number | null
  recurrence_km?: number | null
}

export interface TimelineItem {
  date: string
  kind: 'fuel' | 'service'
  label: string
  cost: number
}

export interface DashboardSummary {
  car: CarProfile
  total_fuel_cost: number
  total_fuel_liters: number
  total_fuel_entries: number
  total_maintenance_cost: number
  total_maintenance_entries: number
  total_cost: number
  avg_consumption_l_per_100km: number | null
  upcoming_reminders: Reminder[]
  recent_activity: TimelineItem[]
}

export interface FuelTrendPoint {
  date: string
  price_total: number
  liters: number
  price_per_liter: number
  consumption_l_per_100km: number | null
}

export interface CostBreakdown {
  fuel_total: number
  maintenance_by_type: Record<string, number>
}
