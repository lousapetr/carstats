export interface ConfirmRequest {
  message: string
  resolve: (value: boolean) => void
}

type ConfirmListener = (request: ConfirmRequest) => void

const listeners = new Set<ConfirmListener>()

export function subscribeConfirm(listener: ConfirmListener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

/** Shows a confirmation dialog (via ConfirmDialogHost) and resolves true/false. */
export function confirmDialog(message: string): Promise<boolean> {
  return new Promise((resolve) => {
    listeners.forEach((listener) => listener({ message, resolve }))
  })
}
