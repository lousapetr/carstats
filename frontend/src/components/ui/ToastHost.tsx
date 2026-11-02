import { useEffect, useState } from 'react'
import { subscribeToast, type Toast, type ToastKind } from '../../lib/toastBus'

interface ToastItem extends Toast {
  id: number
}

const DISPLAY_MS: Record<ToastKind, number> = { error: 6000, success: 2500 }

const TOAST_CLASSES: Record<ToastKind, { box: string; close: string }> = {
  error: {
    box: 'border-red-200 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200',
    close: 'text-red-400 hover:text-red-600 dark:hover:text-red-300',
  },
  success: {
    box: 'border-green-200 bg-green-50 text-green-800 dark:border-green-900 dark:bg-green-950 dark:text-green-200',
    close: 'text-green-400 hover:text-green-600 dark:hover:text-green-300',
  },
}

let nextId = 0

export function ToastHost() {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  useEffect(
    () =>
      subscribeToast((toast) => {
        const id = ++nextId
        setToasts((prev) => [...prev, { ...toast, id }])
        setTimeout(() => {
          setToasts((prev) => prev.filter((t) => t.id !== id))
        }, DISPLAY_MS[toast.kind])
      }),
    [],
  )

  if (toasts.length === 0) return null

  return (
    <div className="fixed inset-x-0 top-4 z-50 flex flex-col items-center gap-2 px-4">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role={toast.kind === 'error' ? 'alert' : 'status'}
          className={`flex w-full max-w-sm items-start gap-2 rounded-lg border px-4 py-3 text-sm shadow-lg ${TOAST_CLASSES[toast.kind].box}`}
        >
          <span className="flex-1">{toast.message}</span>
          <button
            onClick={() => setToasts((prev) => prev.filter((t) => t.id !== toast.id))}
            className={`shrink-0 ${TOAST_CLASSES[toast.kind].close}`}
            aria-label="Zavřít"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  )
}
