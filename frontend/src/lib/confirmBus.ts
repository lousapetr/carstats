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

/** Shows a confirmation dialog (via ConfirmDialogHost) and resolves true/false.
 *  With no host mounted there is nothing to confirm with, so it resolves false
 *  rather than leaving the caller's promise dangling forever. Only the first
 *  host is asked, so a second one can't swallow the answer.
 */
export function confirmDialog(message: string): Promise<boolean> {
  const [listener] = listeners
  if (!listener) return Promise.resolve(false)
  return new Promise((resolve) => listener({ message, resolve }))
}
