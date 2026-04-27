export const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  token?: string | null,
): Promise<T> {
  const headers: Record<string, string> = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  // 204 No Content — return nothing
  if (res.status === 204) return undefined as T

  const json: unknown = await res.json().catch(() => ({ detail: res.statusText }))

  if (!res.ok) {
    const detail =
      json !== null && typeof json === 'object' && 'detail' in json
        ? String((json as Record<string, unknown>).detail)
        : res.statusText
    throw new ApiError(res.status, detail)
  }

  return json as T
}

export const get  = <T>(path: string, token?: string | null) =>
  request<T>('GET', path, undefined, token)

export const post = <T>(path: string, body?: unknown, token?: string | null) =>
  request<T>('POST', path, body, token)

export const del  = <T>(path: string, token?: string | null) =>
  request<T>('DELETE', path, undefined, token)

export const patch = <T>(path: string, body?: unknown, token?: string | null) =>
  request<T>('PATCH', path, body, token)
