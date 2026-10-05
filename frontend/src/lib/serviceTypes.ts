import type { ServiceType } from '../types'

// A Record, so the compiler flags a ServiceType added to the union but not labelled here.
export const SERVICE_TYPE_LABELS: Record<ServiceType, string> = {
  oil_change: 'Výměna oleje',
  tires: 'Pneumatiky',
  engine_service: 'Servis',
  additives: 'Aditiva',
  insurance: 'Pojištění',
  vignette: 'Dálniční známka',
  road_trip: 'Roadtripy',
  inspection: 'STK',
  fines: 'Pokuty',
  other: 'Jiné',
}

export const SERVICE_TYPE_VALUES = Object.keys(SERVICE_TYPE_LABELS) as [
  ServiceType,
  ...ServiceType[],
]

// Alphabetical by label; the catch-all 'other' stays last.
export const SERVICE_TYPES = SERVICE_TYPE_VALUES.map((value) => ({
  value,
  label: SERVICE_TYPE_LABELS[value],
})).sort(
  (a, b) =>
    Number(a.value === 'other') - Number(b.value === 'other') ||
    a.label.localeCompare(b.label, 'cs'),
)

/** The type's label, with the free-text description appended when present. */
export function serviceEntryLabel(type: ServiceType, description: string | null): string {
  const label = SERVICE_TYPE_LABELS[type]
  return description ? `${label} - ${description}` : label
}
