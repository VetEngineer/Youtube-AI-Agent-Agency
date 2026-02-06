import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface DashboardSummary {
    total_runs: number;
    active_runs: number;
    success_runs: number;
    failed_runs: number;
    avg_duration_sec: number | null;
    estimated_cost_usd: number | null;
    recent_runs: PipelineRunSummary[];
}

export interface PipelineRunSummary {
    run_id: string;
    channel_id: string;
    topic: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    dry_run: boolean;
    created_at: string;
    completed_at: string | null;
}

export function useDashboardSummary(limit: number = 5) {
    return useQuery({
        queryKey: ['dashboard', 'summary', limit],
        queryFn: () => api.get<DashboardSummary>(`/dashboard/summary?limit=${limit}`),
        refetchInterval: 10000,
    });
}
