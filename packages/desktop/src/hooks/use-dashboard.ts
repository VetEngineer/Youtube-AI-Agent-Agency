import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from '@/lib/api'

export interface DashboardSummary {
  total_runs: number
  active_runs: number
  success_runs: number
  failed_runs: number
  avg_duration_sec: number | null
  estimated_cost_usd: number | null
  recent_runs: PipelineRunSummary[]
}

export interface PipelineRunSummary {
  run_id: string
  channel_id: string
  topic: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  dry_run: boolean
  created_at: string
  completed_at: string | null
}

interface UseDashboardSummaryResult {
  data: DashboardSummary | null
  isLoading: boolean
  error: Error | null
  refetch: () => void
}

export function useDashboardSummary(limit: number = 5): UseDashboardSummaryResult {
  const [data, setData] = useState<DashboardSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const isMountedRef = useRef(true)

  const fetchData = useCallback(async () => {
    try {
      const result = await api.get<DashboardSummary>(`/dashboard/summary?limit=${limit}`)
      if (isMountedRef.current) {
        setData(result)
        setError(null)
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err instanceof Error ? err : new Error('대시보드 데이터를 불러오지 못했습니다.'))
      }
    } finally {
      if (isMountedRef.current) setIsLoading(false)
    }
  }, [limit])

  useEffect(() => {
    isMountedRef.current = true
    void fetchData()

    const interval = setInterval(() => { void fetchData() }, 10_000)

    return () => {
      isMountedRef.current = false
      clearInterval(interval)
    }
  }, [fetchData])

  return { data, isLoading, error, refetch: fetchData }
}
