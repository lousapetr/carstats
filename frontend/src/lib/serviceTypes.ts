import type { ServiceType } from '../types'

// A Record, so the compiler flags a ServiceType added to the union but not labelled here.
export const SERVICE_TYPE_LABELS: Record<ServiceType, string> = {
  oil_change: 'Výměna oleje',
  tires: 'Pneumatiky',
  engine_service: 'Servis motoru',
  additives: 'Aditiva',
  other: 'Jiné',
}

export const SERVICE_TYPE_VALUES = Object.keys(SERVICE_TYPE_LABELS) as [
  ServiceType,
  ...ServiceType[],
]

export const SERVICE_TYPES = SERVICE_TYPE_VALUES.map((value) => ({
  value,
  label: SERVICE_TYPE_LABELS[value],
}))

/** The type's label, with the free-text description appended for `other`. */
export function serviceEntryLabel(type: ServiceType, description: string | null): string {
  const label = SERVICE_TYPE_LABELS[type]
  return type === 'other' && description ? `${label} - ${description}` : label
}
