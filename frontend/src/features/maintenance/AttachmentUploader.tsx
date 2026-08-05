import { useMutation, useQueryClient } from '@tanstack/react-query'
import { type ChangeEvent, useRef } from 'react'
import { maintenanceApi } from '../../api/maintenance'
import { Button } from '../../components/ui/Button'
import type { Attachment } from '../../types'

export function AttachmentUploader({
  entryId,
  attachments,
}: {
  entryId: number
  attachments: Attachment[]
}) {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)

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
    if (file) uploadMutation.mutate(file)
    event.target.value = ''
  }

  return (
    <div className="mt-2 flex flex-wrap items-center gap-2">
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
            onClick={() => deleteMutation.mutate(attachment.id)}
            className="text-gray-400 hover:text-red-600"
            aria-label={`Remove ${attachment.filename}`}
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
        {uploadMutation.isPending ? 'Uploading…' : '+ Add invoice/photo'}
      </Button>
    </div>
  )
}
