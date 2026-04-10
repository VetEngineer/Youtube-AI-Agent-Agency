import { useState, useEffect, useCallback, useRef } from 'react'
import { api, ApiError } from '@/lib/api'

export interface SubscriptionData {
  plan: string
  status: string
  current_period_end: string | null
}

interface CheckoutResponse {
  checkout_url: string
}

interface PortalResponse {
  portal_url: string
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

export function useSubscription(): UseFetchResult<SubscriptionData> {
  const [data, setData] = useState<SubscriptionData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const isMountedRef = useRef(false)

  const fetchData = useCallback(async (retryCount = 0) => {
    let willRetry = false
    try {
      const result = await api.get<SubscriptionData>('/billing/subscription')
      if (isMountedRef.current) {
        setData(result)
        setError(null)
      }
    } catch (err) {
      if (isMountedRef.current) {
        const shouldRetry =
          !(err instanceof ApiError && (err.status === 401 || err.status === 501)) &&
          retryCount < 2

        if (shouldRetry) {
          willRetry = true
          void fetchData(retryCount + 1)
          return
        }
        setError(err instanceof Error ? err : new Error('구독 정보를 불러오지 못했습니다.'))
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

  return { data, isLoading, error, refetch: fetchData }
}

// Desktop: window.location.href redirect is replaced with returning checkout_url
// for the caller to handle (e.g., open in external browser via Tauri shell)
export function useCheckout(): UseMutationResult<CheckoutResponse, string> {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const mutate = useCallback(async (plan: string): Promise<CheckoutResponse> => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await api.post<CheckoutResponse>('/billing/checkout', { plan })
      return result
    } catch (err) {
      const e = err instanceof Error ? err : new Error('결제 페이지 연결에 실패했습니다.')
      setError(e)
      throw e
    } finally {
      setIsLoading(false)
    }
  }, [])

  const reset = useCallback(() => setError(null), [])

  return { mutate, isLoading, error, reset }
}

// Desktop: portal redirect returns portal_url for Tauri to open externally
export function usePortal(): UseMutationResult<PortalResponse, void> {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const mutate = useCallback(async (_: void): Promise<PortalResponse> => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await api.post<PortalResponse>('/billing/portal', {})
      return result
    } catch (err) {
      const e = err instanceof Error ? err : new Error('고객 포털 연결에 실패했습니다.')
      setError(e)
      throw e
    } finally {
      setIsLoading(false)
    }
  }, [])

  const reset = useCallback(() => setError(null), [])

  return { mutate, isLoading, error, reset }
}
