export class ApiError extends Error {
  status: number
  /** The backend's own `detail` message, or null when the response carried
   *  none and `message` is only the HTTP status text. */
  detail: string | null

  constructor(status: number, detail: string | null, statusText: string) {
    super(detail ?? statusText)
    this.status = status
    this.detail = detail
  }
}

/** FastAPI puts a plain string in `detail` for HTTPException, but a list of
 *  error objects for a 422 schema violation — flatten both to one message. */
async function errorDetail(response: Response): Promise<string | null> {
  const body: unknown = await response.json().catch(() => null)
  const detail = (body as { detail?: unknown } | null)?.detail
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (item as { msg?: string }).msg ?? '')
      .filter((msg) => msg !== '')
    if (messages.length > 0) return messages.join('; ')
  }
  if (typeof detail === 'string' && detail !== '') {
    return detail
  }
  return null
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const isFormData = options.body instanceof FormData
  const response = await fetch(path, {
    ...options,
    credentials: 'same-origin',
    headers: {
      ...(options.body && !isFormData ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  })

  if (!response.ok) {
    throw new ApiError(response.status, await errorDetail(response), response.statusText)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body !== undefined ? JSON.stringify(body) : undefined }),
  postForm: <T>(path: string, formData: FormData) =>
    request<T>(path, { method: 'POST', body: formData }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  delete: (path: string) => request<void>(path, { method: 'DELETE' }),
}
