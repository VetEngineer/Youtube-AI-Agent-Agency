import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from '@/lib/api'

export interface CompetitorChannelInfo {
  id: string
  youtube_channel_id: string
  name: string
  description: string | null
  subscriber_count: number
  video_count: number
  thumbnail_url: string | null
  last_crawled_at: string | null
  is_active: boolean
}

export interface CompetitorVideoInfo {
  video_id: string
  title: string
  view_count: number
  like_count: number
  comment_count: number
  published_at: string
  tags: string[]
  duration_seconds: number | null
  thumbnail_url: string | null
}

export interface CompetitorListResponse {
  competitors: CompetitorChannelInfo[]
  total: number
}

export interface CompetitorDetailResponse {
  channel: CompetitorChannelInfo
  recent_videos: CompetitorVideoInfo[]
}

export interface AddCompetitorRequest {
  youtube_channel_id: string
}

export interface IntegrationsInfo {
  youtube_api_key_set: boolean
  youtube_api_key_masked: string | null
  elevenlabs_api_key_set: boolean
  elevenlabs_api_key_masked: string | null
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

export function useCompetitors(): UseFetchResult<CompetitorListResponse> {
  const [data, setData] = useState<CompetitorListResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const isMountedRef = useRef(true)

  const fetchData = useCallback(async () => {
    try {
      const result = await api.get<CompetitorListResponse>('/competitors/')
      if (isMountedRef.current) {
        setData(result)
        setError(null)
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err instanceof Error ? err : new Error('경쟁사 목록을 불러오지 못했습니다.'))
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

export function useCompetitor(competitorId: string): UseFetchResult<CompetitorDetailResponse> {
  const [data, setData] = useState<CompetitorDetailResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const isMountedRef = useRef(true)

  const fetchData = useCallback(async (signal?: AbortSignal) => {
    if (!competitorId) return
    try {
      const result = await api.get<CompetitorDetailResponse>(`/competitors/${competitorId}`, signal)
      if (isMountedRef.current) {
        setData(result)
        setError(null)
      }
    } catch (err) {
      if ((err as Error).name === 'AbortError') return
      if (isMountedRef.current) {
        setError(err instanceof Error ? err : new Error('경쟁사 상세 정보를 불러오지 못했습니다.'))
      }
    } finally {
      if (isMountedRef.current) setIsLoading(false)
    }
  }, [competitorId])

  useEffect(() => {
    isMountedRef.current = true
    const controller = new AbortController()
    void fetchData(controller.signal)
    return () => {
      isMountedRef.current = false
      controller.abort()
    }
  }, [fetchData])

  return { data, isLoading, error, refetch: fetchData }
}

export function useAddCompetitor(onSuccess?: () => void): UseMutationResult<CompetitorChannelInfo, AddCompetitorRequest> {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const mutate = useCallback(async (data: AddCompetitorRequest): Promise<CompetitorChannelInfo> => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await api.post<CompetitorChannelInfo>('/competitors/', data)
      onSuccess?.()
      return result
    } catch (err) {
      const e = err instanceof Error ? err : new Error('경쟁사 추가에 실패했습니다.')
      setError(e)
      throw e
    } finally {
      setIsLoading(false)
    }
  }, [onSuccess])

  const reset = useCallback(() => setError(null), [])

  return { mutate, isLoading, error, reset }
}

export function useDeleteCompetitor(onSuccess?: () => void): UseMutationResult<void, string> {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const mutate = useCallback(async (competitorId: string): Promise<void> => {
    setIsLoading(true)
    setError(null)
    try {
      await api.delete<void>(`/competitors/${competitorId}`)
      onSuccess?.()
    } catch (err) {
      const e = err instanceof Error ? err : new Error('경쟁사 삭제에 실패했습니다.')
      setError(e)
      throw e
    } finally {
      setIsLoading(false)
    }
  }, [onSuccess])

  const reset = useCallback(() => setError(null), [])

  return { mutate, isLoading, error, reset }
}

export function useRefreshCompetitor(onSuccess?: (data: CompetitorDetailResponse, competitorId: string) => void): UseMutationResult<CompetitorDetailResponse, string> {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const mutate = useCallback(async (competitorId: string): Promise<CompetitorDetailResponse> => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await api.post<CompetitorDetailResponse>(`/competitors/${competitorId}/refresh`, {})
      onSuccess?.(result, competitorId)
      return result
    } catch (err) {
      const e = err instanceof Error ? err : new Error('경쟁사 새로고침에 실패했습니다.')
      setError(e)
      throw e
    } finally {
      setIsLoading(false)
    }
  }, [onSuccess])

  const reset = useCallback(() => setError(null), [])

  return { mutate, isLoading, error, reset }
}

export function useIntegrations(): UseFetchResult<IntegrationsInfo> {
  const [data, setData] = useState<IntegrationsInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const isMountedRef = useRef(true)

  const fetchData = useCallback(async () => {
    try {
      const result = await api.get<IntegrationsInfo>('/settings/integrations')
      if (isMountedRef.current) {
        setData(result)
        setError(null)
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err instanceof Error ? err : new Error('통합 설정을 불러오지 못했습니다.'))
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

export function useUpdateIntegrations(onSuccess?: () => void): UseMutationResult<IntegrationsInfo, { youtube_api_key?: string; elevenlabs_api_key?: string }> {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const mutate = useCallback(async (data: { youtube_api_key?: string; elevenlabs_api_key?: string }): Promise<IntegrationsInfo> => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await api.patch<IntegrationsInfo>('/settings/integrations', data)
      onSuccess?.()
      return result
    } catch (err) {
      const e = err instanceof Error ? err : new Error('통합 설정 저장에 실패했습니다.')
      setError(e)
      throw e
    } finally {
      setIsLoading(false)
    }
  }, [onSuccess])

  const reset = useCallback(() => setError(null), [])

  return { mutate, isLoading, error, reset }
}
