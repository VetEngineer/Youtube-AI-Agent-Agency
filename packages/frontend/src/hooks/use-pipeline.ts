import { useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface PipelineRunDetail {
    run_id: string;
    channel_id: string;
    topic: string;
    brand_name?: string;
    status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
    current_agent: string | null;
    dry_run: boolean;
    created_at: string;
    updated_at: string;
    completed_at: string | null;
    result?: {
        script?: string;
        video_url?: string;
        images?: string[];
    } | null;
    errors: string[];
    cost_usd?: number | null;
}

export interface PipelineRunsResponse {
    runs: PipelineRunDetail[];
    total: number;
    limit: number;
    offset: number;
}

export const PIPELINE_STAGES = [
    { key: 'brand_researcher', label: 'Research', icon: '🔍' },
    { key: 'script_writer', label: 'Script', icon: '📝' },
    { key: 'seo_optimizer', label: 'SEO', icon: '🎯' },
    { key: 'media_generator', label: 'Media', icon: '🎨' },
    { key: 'media_editor', label: 'Edit', icon: '🎬' },
    { key: 'publisher', label: 'Publish', icon: '📤' },
] as const;

export function usePipeline(runId: string) {
    return useQuery({
        queryKey: ['pipeline', runId],
        queryFn: () => api.get<PipelineRunDetail>(`/pipeline/runs/${runId}`),
        enabled: !!runId,
        refetchInterval: (query) => {
            const data = query.state.data;
            if (!data) return 1000;
            return ['completed', 'failed', 'cancelled'].includes(data.status) ? false : 5000;
        },
    });
}

export function usePipelineRuns(params?: {
    channel_id?: string;
    status?: string;
    limit?: number;
    offset?: number;
}) {
    const queryParams = new URLSearchParams();
    if (params?.channel_id) queryParams.set('channel_id', params.channel_id);
    if (params?.status) queryParams.set('status', params.status);
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.offset) queryParams.set('offset', params.offset.toString());

    const queryString = queryParams.toString();
    const endpoint = `/pipeline/runs${queryString ? `?${queryString}` : ''}`;

    return useQuery({
        queryKey: ['pipeline', 'runs', params],
        queryFn: () => api.get<PipelineRunsResponse>(endpoint),
    });
}

export function useCreatePipeline() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: { channel_id: string; topic: string; brand_name?: string; dry_run?: boolean }) =>
            api.post<{ run_id: string; status: string; channel_id: string; topic: string }>('/pipeline/run', data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['dashboard', 'summary'] });
            queryClient.invalidateQueries({ queryKey: ['pipeline', 'runs'] });
        },
    });
}

export function useCancelPipeline() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (runId: string) =>
            api.post<{ run_id: string; status: string }>(`/pipeline/runs/${runId}/cancel`, {}),
        onSuccess: (_data, runId) => {
            queryClient.invalidateQueries({ queryKey: ['pipeline', runId] });
            queryClient.invalidateQueries({ queryKey: ['pipeline', 'runs'] });
        },
    });
}

export function useRetryPipeline() {
    const queryClient = useQueryClient();
    const router = useRouter();

    return useMutation({
        mutationFn: (runId: string) =>
            api.post<{ run_id: string; status: string; channel_id: string; topic: string }>(
                `/pipeline/runs/${runId}/retry`,
                {}
            ),
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['pipeline', 'runs'] });
            router.push(`/pipelines/${data.run_id}`);
        },
    });
}

export function usePipelineSSE(runId: string) {
    const queryClient = useQueryClient();
    const esRef = useRef<EventSource | null>(null);

    useEffect(() => {
        if (!runId) return;

        const es = new EventSource(`/api/v1/pipeline/runs/${runId}/stream`);
        esRef.current = es;

        es.onmessage = (event) => {
            try {
                const data: Partial<PipelineRunDetail> = JSON.parse(event.data);
                queryClient.setQueryData(['pipeline', runId], (old: PipelineRunDetail | undefined) =>
                    old ? { ...old, ...data } : data
                );
                if (data.status && ['completed', 'failed', 'cancelled'].includes(data.status)) {
                    es.close();
                }
            } catch {
                // ignore parse errors
            }
        };

        es.onerror = () => {
            es.close();
        };

        return () => {
            es.close();
        };
    }, [runId, queryClient]);

    return { isStreaming: esRef.current?.readyState === EventSource.OPEN };
}
