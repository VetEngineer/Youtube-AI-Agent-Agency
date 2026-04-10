import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from '@/lib/api'

export interface Channel {
  channel_id: string
  name: string
  category: string
  has_brand_guide: boolean
}

export interface ChannelsResponse {
  channels: Channel[]
  total: number
}

export interface CreateChannelRequest {
  channel_id: string
  name: string
  category?: string
  description?: string
}

export interface UpdateChannelRequest {
  name?: string
  category?: string
}

interface UseChannelsResult {
  data: ChannelsResponse | null
  isLoading: boolean
  error: Error | null
  refetch: () => void
}

export function useChannels(): UseChannelsResult {
  const [data, setData] = useState<ChannelsResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const isMountedRef = useRef(true)

  const fetchData = useCallback(async () => {
    try {
      const result = await api.get<ChannelsResponse>('/channels/')
      if (isMountedRef.current) {
        setData(result)
        setError(null)
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err instanceof Error ? err : new Error('채널 목록을 불러오지 못했습니다.'))
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

interface UseChannelResult {
  data: Channel | null
  isLoading: boolean
  error: Error | null
  refetch: () => void
}

export function useChannel(channelId: string): UseChannelResult {
  const [data, setData] = useState<Channel | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const isMountedRef = useRef(true)

  const fetchData = useCallback(async () => {
    if (!channelId) return
    try {
      const result = await api.get<Channel>(`/channels/${channelId}`)
      if (isMountedRef.current) {
        setData(result)
        setError(null)
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err instanceof Error ? err : new Error('채널 정보를 불러오지 못했습니다.'))
      }
    } finally {
      if (isMountedRef.current) setIsLoading(false)
    }
  }, [channelId])

  useEffect(() => {
    isMountedRef.current = true
    void fetchData()
    return () => { isMountedRef.current = false }
  }, [fetchData])

  return { data, isLoading, error, refetch: fetchData }
}

interface UseMutationResult<TData, TVariables> {
  mutate: (variables: TVariables) => Promise<TData>
  isLoading: boolean
  error: Error | null
  reset: () => void
}

export function useCreateChannel(onSuccess?: () => void): UseMutationResult<Channel, CreateChannelRequest> {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const mutate = useCallback(async (data: CreateChannelRequest): Promise<Channel> => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await api.post<Channel>('/channels/', data)
      onSuccess?.()
      return result
    } catch (err) {
      const e = err instanceof Error ? err : new Error('채널 생성에 실패했습니다.')
      setError(e)
      throw e
    } finally {
      setIsLoading(false)
    }
  }, [onSuccess])

  const reset = useCallback(() => setError(null), [])

  return { mutate, isLoading, error, reset }
}

export function useUpdateChannel(onSuccess?: () => void): UseMutationResult<Channel, { channelId: string; data: UpdateChannelRequest }> {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const mutate = useCallback(async ({ channelId, data }: { channelId: string; data: UpdateChannelRequest }): Promise<Channel> => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await api.patch<Channel>(`/channels/${channelId}`, data)
      onSuccess?.()
      return result
    } catch (err) {
      const e = err instanceof Error ? err : new Error('채널 수정에 실패했습니다.')
      setError(e)
      throw e
    } finally {
      setIsLoading(false)
    }
  }, [onSuccess])

  const reset = useCallback(() => setError(null), [])

  return { mutate, isLoading, error, reset }
}

export function useDeleteChannel(onSuccess?: () => void): UseMutationResult<void, string> {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const mutate = useCallback(async (channelId: string): Promise<void> => {
    setIsLoading(true)
    setError(null)
    try {
      await api.delete<void>(`/channels/${channelId}`)
      onSuccess?.()
    } catch (err) {
      const e = err instanceof Error ? err : new Error('채널 삭제에 실패했습니다.')
      setError(e)
      throw e
    } finally {
      setIsLoading(false)
    }
  }, [onSuccess])

  const reset = useCallback(() => setError(null), [])

  return { mutate, isLoading, error, reset }
}
