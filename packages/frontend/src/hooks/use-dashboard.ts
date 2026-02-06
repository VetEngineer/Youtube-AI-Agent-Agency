import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface DashboardSummary {
    total_runs: number;
    active_runs: number;
    success_runs: number;
    failed_runs: number;
    recent_runs: PipelineRunSummary[];
}

export interface PipelineRunSummary {
    run_id: string;
    topic: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    created_at: string;
}

export function useDashboardSummary() {
    return useQuery({
        queryKey: ['dashboard', 'summary'],
        queryFn: () => api.get<DashboardSummary>('/dashboard/summary'),
        refetchInterval: 10000, // Refresh every 10 seconds
    });
}
