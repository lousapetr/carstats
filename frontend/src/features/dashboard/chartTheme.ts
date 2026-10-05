import { useIsDark } from '../../lib/useIsDark'

type Themed = { light: string; dark: string }

const BLUE: Themed = { light: '#2a78d6', dark: '#3987e5' }
const ORANGE: Themed = { light: '#eb6834', dark: '#d95926' }
const AQUA: Themed = { light: '#1baf7a', dark: '#199e70' }
const RED: Themed = { light: '#e34948', dark: '#e66767' }
const GRAY: Themed = { light: '#898781', dark: '#898781' }

// One hue per cost group, shared by every chart so a colour means the same
// thing everywhere: orange is the car's upkeep, aqua fixed fees. Fills may sit
// below 3:1 on white; charts using them carry visible value labels or a text
// twin instead of relying on the colour.
export const CATEGORY_COLORS: Record<string, Themed> = {
  fuel: BLUE,
  service: ORANGE,
  oil_change: ORANGE,
  tires: ORANGE,
  engine_service: ORANGE,
  additives: ORANGE,
  insurance: AQUA,
  inspection: AQUA,
  vignette: AQUA,
  fines: RED,
  road_trip: GRAY,
  other: GRAY,
}

/** The chart payload's value as a number, or null when it's missing or not numeric. */
export function payloadNumber(value: unknown): number | null {
  const n = typeof value === 'number' ? value : Number(value)
  return value === null || value === undefined || !Number.isFinite(n) ? null : n
}

const BASE = {
  // Recessive on purpose: gridlines should not compete with the data.
  grid: { light: '#e1e0d9', dark: '#2c2c2a' },
  // Tick text is text, so it needs real contrast, unlike the gridlines.
  tick: { light: '#52514e', dark: '#c3c2b7' },
  consumption: { light: '#eb6834', dark: '#d95926' },
  pricePerLiter: { light: '#1baf7a', dark: '#199e70' },
}

export function useChartTheme() {
  const isDark = useIsDark()
  const pick = (c: Themed) => (isDark ? c.dark : c.light)
  return {
    grid: pick(BASE.grid),
    tick: pick(BASE.tick),
    consumption: pick(BASE.consumption),
    pricePerLiter: pick(BASE.pricePerLiter),
    category: (key: string) => pick(CATEGORY_COLORS[key] ?? GRAY),
  }
}
