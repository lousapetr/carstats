import { api } from './client'

export interface CurrentUser {
  email: string
}

export const authApi = {
  me: () => api.get<CurrentUser>('/auth/me'),
  logout: () => api.post<{ ok: boolean }>('/auth/logout'),
}
