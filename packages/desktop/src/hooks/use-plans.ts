import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from '@/lib/api'

export interface PlanQuota {
  monthly_pipelines: number
  max_channels: number
  media_generation: boolean
  youtube_upload: boolean
  priority_queue: boolean
  api_access: boolean
}

export interface PlanInfo {
  name: string
  quotas: PlanQuota
}

export interface PlanListResponse {
  plans: PlanInfo[]
}

export interface PlanUsageResponse {
  plan: string
  pipelines_used: number
  pipelines_limit: number
  channels_used: number
  channels_limit: number
  features: Record<string, boolean>
}

interface UseFetchResult<T> {
  data: T | null
  isLoading: boolean
  error: Error | null
  refetch: () => void
}

export function usePlans(): UseFetchResult<PlanListResponse> {
  const [data, setData] = useState<PlanListResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const isMountedRef = useRef(false)

  const fetchData = useCallback(async () => {
    try {
      const result = await api.get<PlanListResponse>('/plans')
      if (isMountedRef.current) {
        setData(result)
        setError(null)
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err instanceof Error ? err : new Error('플랜 목록을 불러오지 못했습니다.'))
      }
    } finally {
      if (isMountedRef.current) setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    isMountedRef.current = true
    void fetchData()
    return () => { isMountedRef.current = false }
  }, [fetchData])

  return { data, isLoading, error, refetch: fetchData }
}

export function usePlanUsage(): UseFetchResult<PlanUsageResponse> {
  const [data, setData] = useState<PlanUsageResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const isMountedRef = useRef(false)

  const fetchData = useCallback(async () => {
    try {
      const result = await api.get<PlanUsageResponse>('/plans/usage')
      if (isMountedRef.current) {
        setData(result)
        setError(null)
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err instanceof Error ? err : new Error('플랜 사용량을 불러오지 못했습니다.'))
      }
    } finally {
      if (isMountedRef.current) setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    isMountedRef.current = true
    void fetchData()

    const interval = setInterval(() => { void fetchData() }, 30_000)

    return () => {
      isMountedRef.current = false
      clearInterval(interval)
    }
  }, [fetchData])

  return { data, isLoading, error, refetch: fetchData }
}
