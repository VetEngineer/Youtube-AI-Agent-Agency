import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface PipelineRunDetail {
    run_id: string;
    channel_id: string;
    topic: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    current_agent: string;
    created_at: string;
    result?: {
        script?: string;
        video_url?: string;
    };
    errors?: string[];
}

export function usePipeline(runId: string) {
    return useQuery({
        queryKey: ['pipeline', runId],
        queryFn: () => api.get<PipelineRunDetail>(`/pipeline/runs/${runId}`),
        enabled: !!runId,
        refetchInterval: (data) => {
            if (!data) return 1000;
            return ['completed', 'failed'].includes(data.status) ? false : 3000;
        },
    });
}

export function useCreatePipeline() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: { channel_id: string; topic: string; style?: string }) =>
            api.post<{ run_id: string }>('/pipeline/run', data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['dashboard', 'summary'] });
        },
    });
}
