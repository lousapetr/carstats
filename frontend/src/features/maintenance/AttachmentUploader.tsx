import { useMutation, useQueryClient } from '@tanstack/react-query'
import { type ChangeEvent, useRef, useState } from 'react'
import { mutationErrorMessage } from '../../api/errors'
import { maintenanceApi } from '../../api/maintenance'
import { Button } from '../../components/ui/Button'
import { confirmDialog } from '../../lib/confirmBus'
import type { Attachment } from '../../types'

// Mirrors MAX_UPLOAD_BYTES in backend/app/attachments/storage.py.
const MAX_UPLOAD_BYTES = 20 * 1024 * 1024

export function AttachmentUploader({
  entryId,
  attachments,
}: {
  entryId: number
  attachments: Attachment[]
}) {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [sizeError, setSizeError] = useState<string | null>(null)

  const uploadMutation = useMutation({
    mutationFn: (file: File) => maintenanceApi.uploadAttachment(entryId, file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['service-entries'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (attachmentId: number) => maintenanceApi.deleteAttachment(attachmentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['service-entries'] }),
  })

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    if (file.size > MAX_UPLOAD_BYTES) {
      const maxMb = MAX_UPLOAD_BYTES / (1024 * 1024)
      setSizeError(`Soubor ${file.name} je příliš velký (max ${maxMb} MB).`)
      return
    }
    setSizeError(null)
    uploadMutation.mutate(file)
  }

  // Upload and delete failures also toast via the global MutationCache handler;
  // this line stays put so the reason is still visible after the toast fades.
  const error =
    sizeError ??
    (uploadMutation.isError ? mutationErrorMessage(uploadMutation.error) : null) ??
    (deleteMutation.isError ? mutationErrorMessage(deleteMutation.error) : null)

  return (
    <div className="mt-2 flex flex-col gap-1">
      <div className="flex flex-wrap items-center gap-2">
        {attachments.map((attachment) => (
          <span
            key={attachment.id}
            className="flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-300"
          >
            <a
              href={maintenanceApi.attachmentDownloadUrl(attachment.id)}
              target="_blank"
              rel="noreferrer"
              className="underline underline-offset-2"
            >
              {attachment.filename}
            </a>
            <button
              onClick={async () => {
                if (await confirmDialog(`Opravdu smazat přílohu ${attachment.filename}?`)) {
                  deleteMutation.mutate(attachment.id)
                }
              }}
              className="text-gray-400 hover:text-red-600"
              aria-label={`Odebrat ${attachment.filename}`}
            >
              ×
            </button>
          </span>
        ))}
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileChange}
          accept="image/*,application/pdf"
        />
        <Button
          type="button"
          variant="secondary"
          className="px-2.5 py-1 text-xs"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploadMutation.isPending}
        >
          {uploadMutation.isPending ? 'Nahrávám…' : '+ Přidat fakturu/fotku'}
        </Button>
      </div>
      {error && (
        <p role="alert" className="text-xs text-red-700 dark:text-red-400">
          {error}
        </p>
      )}
    </div>
  )
}
