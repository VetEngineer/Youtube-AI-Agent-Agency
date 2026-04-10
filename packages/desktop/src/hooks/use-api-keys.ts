import { useState, useEffect, useCallback, useRef } from 'react'
import { api, ApiError } from '@/lib/api'

export interface ApiKey {
  key_id: string
  name: string
  prefix: string
  scopes: string[]
  created_at: string
  expires_at: string | null
  last_used_at: string | null
  is_active: boolean
}

export interface ApiKeysResponse {
  api_keys: ApiKey[]
  total: number
}

export interface CreateApiKeyRequest {
  name: string
  scopes: string[]
  expires_days?: number | null
}

export interface CreateApiKeyResponse {
  key_id: string
  name: string
  key: string // Plaintext key, shown only once
  prefix: string
  scopes: string[]
  expires_at: string | null
}

interface UseFetchResult<T> {
  data: T | null
  isLoading: boolean
  error: Error | null
  refetch: () => void
}

interface UseMutationResult<TData, TVariables> {
  mutate: (variables: TVariables) => Promise<TData>
  isLoading: boolean
  error: Error | null
  reset: () => void
}

function shouldRetry(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiError && (error.status === 401 || error.status === 403)) return false
  return failureCount < 2
}

export function useApiKeys(): UseFetchResult<ApiKeysResponse> {
  const [data, setData] = useState<ApiKeysResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const isMountedRef = useRef(true)

  const fetchData = useCallback(async (retryCount = 0) => {
    let willRetry = false
    try {
      const result = await api.get<ApiKeysResponse>('/admin/api-keys')
      if (isMountedRef.current) {
        setData(result)
        setError(null)
      }
    } catch (err) {
      if (isMountedRef.current) {
        if (shouldRetry(retryCount, err)) {
          willRetry = true
          void fetchData(retryCount + 1)
          return
        }
        setError(err instanceof Error ? err : new Error('API 키 목록을 불러오지 못했습니다.'))
      }
    } finally {
      if (!willRetry && isMountedRef.current) setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    isMountedRef.current = true
    void fetchData()
    return () => { isMountedRef.current = false }
  }, [fetchData])

  return { data, isLoading, error, refetch: () => fetchData() }
}

export function useCreateApiKey(onSuccess?: () => void): UseMutationResult<CreateApiKeyResponse, CreateApiKeyRequest> {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const mutate = useCallback(async (data: CreateApiKeyRequest): Promise<CreateApiKeyResponse> => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await api.post<CreateApiKeyResponse>('/admin/api-keys', data)
      onSuccess?.()
      return result
    } catch (err) {
      const e = err instanceof Error ? err : new Error('API 키 생성에 실패했습니다.')
      setError(e)
      throw e
    } finally {
      setIsLoading(false)
    }
  }, [onSuccess])

  const reset = useCallback(() => setError(null), [])

  return { mutate, isLoading, error, reset }
}

export function useDeleteApiKey(onSuccess?: () => void): UseMutationResult<void, string> {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const mutate = useCallback(async (keyId: string): Promise<void> => {
    setIsLoading(true)
    setError(null)
    try {
      await api.delete<void>(`/admin/api-keys/${keyId}`)
      onSuccess?.()
    } catch (err) {
      const e = err instanceof Error ? err : new Error('API 키 삭제에 실패했습니다.')
      setError(e)
      throw e
    } finally {
      setIsLoading(false)
    }
  }, [onSuccess])

  const reset = useCallback(() => setError(null), [])

  return { mutate, isLoading, error, reset }
}
