type ToastListener = (message: string) => void

const listeners = new Set<ToastListener>()

export function subscribeToast(listener: ToastListener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function emitErrorToast(message: string): void {
  listeners.forEach((listener) => listener(message))
}
