import { api } from './client'
import type { Attachment, ServiceEntry, ServiceEntryInput } from '../types'

export const maintenanceApi = {
  list: () => api.get<ServiceEntry[]>('/api/service-entries'),
  create: (data: ServiceEntryInput) => api.post<ServiceEntry>('/api/service-entries', data),
  update: (id: number, data: ServiceEntryInput) =>
    api.put<ServiceEntry>(`/api/service-entries/${id}`, data),
  remove: (id: number) => api.delete(`/api/service-entries/${id}`),
  uploadAttachment: (entryId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.postForm<Attachment>(`/api/service-entries/${entryId}/attachments`, formData)
  },
  deleteAttachment: (attachmentId: number) => api.delete(`/api/attachments/${attachmentId}`),
  attachmentDownloadUrl: (attachmentId: number) => `/api/attachments/${attachmentId}/download`,
}
