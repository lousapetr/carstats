export type ToastKind = 'error' | 'success'

export interface Toast {
  kind: ToastKind
  message: string
}

type ToastListener = (toast: Toast) => void

const listeners = new Set<ToastListener>()

export function subscribeToast(listener: ToastListener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

function emit(toast: Toast): void {
  listeners.forEach((listener) => listener(toast))
}

export function emitErrorToast(message: string): void {
  emit({ kind: 'error', message })
}

export function emitSuccessToast(message: string): void {
  emit({ kind: 'success', message })
}
