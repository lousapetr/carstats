import type { ReactNode } from 'react'

export function Field({
  label,
  error,
  children,
}: {
  label: string
  error?: string
  children: ReactNode
}) {
  return (
    <label className="flex flex-col">
      <span className="mb-1 flex flex-1 items-end text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
      </span>
      {children}
      {error && <span className="mt-1 block text-xs text-red-600">{error}</span>}
    </label>
  )
}

export const inputClass =
  'w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-gray-500 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100'

// iOS Safari gives date inputs an intrinsic min-width (overflowing a grid cell), a shorter
// native height and centered text; this makes them match the other inputs.
export const dateInputClass = `${inputClass} min-w-0 min-h-[2.375rem] appearance-none [&::-webkit-date-and-time-value]:text-left`
