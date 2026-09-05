import { useEffect, useState } from 'react'
import { type ConfirmRequest, subscribeConfirm } from '../../lib/confirmBus'
import { Button } from './Button'

export function ConfirmDialogHost() {
  const [pending, setPending] = useState<ConfirmRequest | null>(null)

  useEffect(() => subscribeConfirm(setPending), [])

  if (!pending) return null

  const respond = (value: boolean) => {
    pending.resolve(value)
    setPending(null)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="w-full max-w-sm rounded-lg bg-white p-5 shadow-xl dark:bg-gray-900">
        <p className="text-sm text-gray-900 dark:text-gray-100">{pending.message}</p>
        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={() => respond(false)}>
            Zrušit
          </Button>
          <Button type="button" variant="danger" onClick={() => respond(true)}>
            Smazat
          </Button>
        </div>
      </div>
    </div>
  )
}
