import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { useAuth } from '@/providers/AuthProvider'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface PipelineRunDetail {
  run_id: string
  channel_id: string
  topic: string
  brand_name?: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  current_agent: string | null
  dry_run: boolean
  created_at: string
  updated_at: string
  completed_at: string | null
  result?: {
    script?: string
    video_url?: string
    images?: string[]
  } | null
  errors: string[]
  cost_usd?: number | null
}

export interface PipelineRunsResponse {
  runs: PipelineRunDetail[]
  total: number
  limit: number
  offset: number
}

export interface CreatePipelineRequest {
  channel_id: string
  topic: string
  brand_name?: string
  dry_run?: boolean
}

export interface CreatePipelineResponse {
  run_id: string
  status: string
  channel_id: string
  topic: string
}

export const PIPELINE_STAGES = [
  { key: 'brand_researcher', label: 'Research', icon: '🔍' },
  { key: 'script_writer', label: 'Script', icon: '📝' },
  { key: 'seo_optimizer', label: 'SEO', icon: '🎯' },
  { key: 'media_generator', label: 'Media', icon: '🎨' },
  { key: 'media_editor', label: 'Edit', icon: '🎬' },
  { key: 'publisher', label: 'Publish', icon: '📤' },
] as const

const TERMINAL_STATUSES = new Set(['completed', 'failed', 'cancelled'])

// ---------------------------------------------------------------------------
// Shared local mutation result type
// ---------------------------------------------------------------------------

interface UseMutationResult<TData, TVariables> {
  mutate: (variables: TVariables) => Promise<TData>
  isLoading: boolean
  error: Error | null
  reset: () => void
}

// ---------------------------------------------------------------------------
// usePipeline — single run detail, auto-polling until terminal
// ---------------------------------------------------------------------------

interface UsePipelineResult {
  data: PipelineRunDetail | null
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

export function usePipeline(runId: string): UsePipelineResult {
  const [data, setData] = useState<PipelineRunDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const isMountedRef = useRef(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchData = useCallback(async () => {
    if (!runId) return
    try {
      const result = await api.get<PipelineRunDetail>(`/pipeline/runs/${runId}`)
      if (!isMountedRef.current) return
      setData(result)
      setError(null)
      // Stop polling once terminal
      if (TERMINAL_STATUSES.has(result.status) && intervalRef.current !== null) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err instanceof Error ? err : new Error('파이프라인 정보를 불러오지 못했습니다.'))
      }
    } finally {
      if (isMountedRef.current) setIsLoading(false)
    }
  }, [runId])

  useEffect(() => {
    if (!runId) return
    isMountedRef.current = true
    void fetchData()

    // Poll every 5 s for non-terminal runs; initial fetch may clear the interval
    intervalRef.current = setInterval(() => { void fetchData() }, 5_000)

    return () => {
      isMountedRef.current = false
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [fetchData, runId])

  return { data, isLoading, error, refetch: fetchData }
}

// ---------------------------------------------------------------------------
// usePipelineRuns — list with optional filters
// ---------------------------------------------------------------------------

interface UsePipelineRunsResult {
  data: PipelineRunsResponse | null
  isLoading: boolean
  error: Error | null
  refetch: () => void
}

export function usePipelineRuns(params?: {
  channel_id?: string
  status?: string
  limit?: number
  offset?: number
}): UsePipelineRunsResult {
  const [data, setData] = useState<PipelineRunsResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const isMountedRef = useRef(false)

  const buildEndpoint = useCallback(() => {
    const queryParams = new URLSearchParams()
    if (params?.channel_id) queryParams.set('channel_id', params.channel_id)
    if (params?.status) queryParams.set('status', params.status)
    if (params?.limit != null) queryParams.set('limit', params.limit.toString())
    if (params?.offset != null) queryParams.set('offset', params.offset.toString())
    const qs = queryParams.toString()
    return `/pipeline/runs${qs ? `?${qs}` : ''}`
  // params 객체 참조 대신 원시값을 개별 의존성으로 사용하여 불필요한 재실행 방지
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params?.channel_id, params?.status, params?.limit, params?.offset])

  const fetchData = useCallback(async () => {
    try {
      const result = await api.get<PipelineRunsResponse>(buildEndpoint())
      if (isMountedRef.current) {
        setData(result)
        setError(null)
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err instanceof Error ? err : new Error('파이프라인 목록을 불러오지 못했습니다.'))
      }
    } finally {
      if (isMountedRef.current) setIsLoading(false)
    }
  }, [buildEndpoint])

  useEffect(() => {
    isMountedRef.current = true
    void fetchData()
    return () => { isMountedRef.current = false }
  }, [fetchData])

  return { data, isLoading, error, refetch: fetchData }
}

// ---------------------------------------------------------------------------
// useCreatePipeline
// ---------------------------------------------------------------------------

export function useCreatePipeline(onSuccess?: () => void): UseMutationResult<CreatePipelineResponse, CreatePipelineRequest> {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const mutate = useCallback(async (data: CreatePipelineRequest): Promise<CreatePipelineResponse> => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await api.post<CreatePipelineResponse>('/pipeline/run', data)
      onSuccess?.()
      return result
    } catch (err) {
      const e = err instanceof Error ? err : new Error('파이프라인 시작에 실패했습니다.')
      setError(e)
      throw e
    } finally {
      setIsLoading(false)
    }
  }, [onSuccess])

  const reset = useCallback(() => setError(null), [])

  return { mutate, isLoading, error, reset }
}

// ---------------------------------------------------------------------------
// useCancelPipeline
// ---------------------------------------------------------------------------

export function useCancelPipeline(onSuccess?: (runId: string) => void): UseMutationResult<{ run_id: string; status: string }, string> {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const mutate = useCallback(async (runId: string): Promise<{ run_id: string; status: string }> => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await api.post<{ run_id: string; status: string }>(`/pipeline/runs/${runId}/cancel`, {})
      onSuccess?.(runId)
      return result
    } catch (err) {
      const e = err instanceof Error ? err : new Error('파이프라인 취소에 실패했습니다.')
      setError(e)
      throw e
    } finally {
      setIsLoading(false)
    }
  }, [onSuccess])

  const reset = useCallback(() => setError(null), [])

  return { mutate, isLoading, error, reset }
}

// ---------------------------------------------------------------------------
// useRetryPipeline — navigates to new run on success
// ---------------------------------------------------------------------------

export function useRetryPipeline(onSuccess?: () => void): UseMutationResult<CreatePipelineResponse, string> {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const mutate = useCallback(async (runId: string): Promise<CreatePipelineResponse> => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await api.post<CreatePipelineResponse>(`/pipeline/runs/${runId}/retry`, {})
      onSuccess?.()
      navigate(`/pipelines/${result.run_id}`)
      return result
    } catch (err) {
      const e = err instanceof Error ? err : new Error('파이프라인 재시도에 실패했습니다.')
      setError(e)
      throw e
    } finally {
      setIsLoading(false)
    }
  }, [navigate, onSuccess])

  const reset = useCallback(() => setError(null), [])

  return { mutate, isLoading, error, reset }
}

// ---------------------------------------------------------------------------
// usePipelineSSE — real-time run updates via EventSource
//
// SSE does not support custom headers so the API key is passed as a query
// parameter (same design as the frontend, see issue #71).
// The backendUrl is read from AuthProvider so it adapts to any server URL.
// ---------------------------------------------------------------------------

interface UsePipelineSSEResult {
  isStreaming: boolean
}

/**
 * SSE 구독 훅. onUpdate는 반드시 useCallback으로 메모이제이션된 안정적인 함수여야 합니다.
 * 불안정한 참조(인라인 함수)를 전달하면 렌더마다 EventSource가 재연결됩니다.
 * @param onUpdate MUST be a stable callback (useCallback). Unstable references cause reconnection on every render.
 */
export function usePipelineSSE(
  runId: string,
  onUpdate: (patch: Partial<PipelineRunDetail>) => void
): UsePipelineSSEResult {
  const { apiKey, backendUrl } = useAuth()
  const isMountedRef = useRef(false)
  const reconnectCountRef = useRef(0)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const MAX_RECONNECT = 3
  const [isStreaming, setIsStreaming] = useState(false)
  const [retryKey, setRetryKey] = useState(0)

  useEffect(() => {
    if (!runId || !apiKey) return
    isMountedRef.current = true

    const base = backendUrl.replace(/\/+$/, '')
    const params = `?api_key=${encodeURIComponent(apiKey)}`
    const url = `${base}/pipeline/runs/${runId}/stream${params}`

    const es = new EventSource(url)
    setIsStreaming(true)

    es.onopen = () => {
      reconnectCountRef.current = 0
    }

    es.onmessage = (event: MessageEvent<string>) => {
      try {
        const data = JSON.parse(event.data) as Partial<PipelineRunDetail>
        onUpdate(data)
        if (data.status && TERMINAL_STATUSES.has(data.status)) {
          es.close()
          setIsStreaming(false)
        }
      } catch {
        // Ignore parse errors — malformed SSE frames should not crash the UI
      }
    }

    es.onerror = () => {
      es.close()
      if (reconnectCountRef.current < MAX_RECONNECT && isMountedRef.current) {
        const delay = Math.pow(2, reconnectCountRef.current) * 1000
        reconnectCountRef.current++
        reconnectTimerRef.current = setTimeout(() => {
          if (isMountedRef.current) setRetryKey((k) => k + 1)
        }, delay)
      } else {
        reconnectCountRef.current = 0
        setIsStreaming(false)
      }
    }

    return () => {
      isMountedRef.current = false
      es.close()
      if (reconnectTimerRef.current !== null) {
        clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }
      setIsStreaming(false)
    }
  }, [runId, apiKey, backendUrl, onUpdate, retryKey])

  return { isStreaming }
}
