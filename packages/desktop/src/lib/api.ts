// In-memory API key cache — set by AuthProvider on init, cleared on logout.
// api.ts never calls tauri-store directly; AuthProvider is the single source of truth.
// The initial URL is overwritten by AuthProvider.init() before any request fires.
import { DEFAULT_BACKEND_URL } from '@/lib/tauri-store'

let _inMemoryApiKey: string | null = null
let _inMemoryBackendUrl: string = DEFAULT_BACKEND_URL

export function setInMemoryKey(key: string | null, backendUrl: string): void {
  _inMemoryApiKey = key
  _inMemoryBackendUrl = backendUrl
}

export function clearInMemoryKey(): void {
  _inMemoryApiKey = null
  _inMemoryBackendUrl = DEFAULT_BACKEND_URL
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export class NetworkError extends Error {
  constructor() {
    super('서버에 연결할 수 없습니다. 네트워크 연결을 확인하세요.')
    this.name = 'NetworkError'
  }
}

// Called by AuthProvider when a 401 is detected mid-session
let _on401: (() => void) | null = null

export function register401Handler(handler: () => void): void {
  _on401 = handler
}

export function unregister401Handler(): void {
  _on401 = null
}

async function fetchWithAuth<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const apiKey = _inMemoryApiKey
  const baseUrl = _inMemoryBackendUrl.replace(/\/+$/, '')

  const headers = new Headers({
    'Content-Type': 'application/json',
  })
  if (options.headers) {
    new Headers(options.headers).forEach((value, key) => {
      headers.set(key, value)
    })
  }

  if (apiKey) {
    headers.set('X-API-Key', apiKey)
  }

  let response: Response
  try {
    response = await fetch(`${baseUrl}${endpoint}`, { ...options, headers })
  } catch {
    throw new NetworkError()
  }

  if (response.status === 401) {
    _on401?.()
    throw new ApiError(401, '인증이 만료되었습니다. 다시 로그인하세요.')
  }

  if (!response.ok) {
    throw new ApiError(response.status, `API 오류 (${response.status})`)
  }

  if (response.status === 204) return undefined as T

  const text = await response.text()
  if (!text) return undefined as T
  try {
    return JSON.parse(text) as T
  } catch {
    throw new ApiError(response.status, 'API 응답을 파싱할 수 없습니다.')
  }
}

export const api = {
  get: <T>(endpoint: string) => fetchWithAuth<T>(endpoint, { method: 'GET' }),
  post: <T>(endpoint: string, body: unknown) =>
    fetchWithAuth<T>(endpoint, { method: 'POST', body: JSON.stringify(body) }),
  put: <T>(endpoint: string, body: unknown) =>
    fetchWithAuth<T>(endpoint, { method: 'PUT', body: JSON.stringify(body) }),
  patch: <T>(endpoint: string, body: unknown) =>
    fetchWithAuth<T>(endpoint, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: <T>(endpoint: string) => fetchWithAuth<T>(endpoint, { method: 'DELETE' }),
}
