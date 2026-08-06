import { useEffect, useState } from 'react'
import { subscribeToast } from '../../lib/toastBus'

interface ToastItem {
  id: number
  message: string
}

const DISPLAY_MS = 6000

let nextId = 0

export function ToastHost() {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  useEffect(
    () =>
      subscribeToast((message) => {
        const id = ++nextId
        setToasts((prev) => [...prev, { id, message }])
        setTimeout(() => {
          setToasts((prev) => prev.filter((t) => t.id !== id))
        }, DISPLAY_MS)
      }),
    [],
  )

  if (toasts.length === 0) return null

  return (
    <div className="fixed inset-x-0 top-4 z-50 flex flex-col items-center gap-2 px-4">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role="alert"
          className="flex w-full max-w-sm items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 shadow-lg dark:border-red-900 dark:bg-red-950 dark:text-red-200"
        >
          <span className="flex-1">{toast.message}</span>
          <button
            onClick={() => setToasts((prev) => prev.filter((t) => t.id !== toast.id))}
            className="shrink-0 text-red-400 hover:text-red-600 dark:hover:text-red-300"
            aria-label="Zavřít"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  )
}
