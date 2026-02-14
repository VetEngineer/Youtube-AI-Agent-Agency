import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface PlanQuota {
    monthly_pipelines: number;
    max_channels: number;
    media_generation: boolean;
    youtube_upload: boolean;
    priority_queue: boolean;
    api_access: boolean;
}

export interface PlanInfo {
    name: string;
    quotas: PlanQuota;
}

export interface PlanListResponse {
    plans: PlanInfo[];
}

export interface PlanUsageResponse {
    plan: string;
    pipelines_used: number;
    pipelines_limit: number;
    channels_used: number;
    channels_limit: number;
    features: Record<string, boolean>;
}

export function usePlans() {
    return useQuery({
        queryKey: ['plans'],
        queryFn: () => api.get<PlanListResponse>('/plans'),
    });
}

export function usePlanUsage() {
    return useQuery({
        queryKey: ['plans', 'usage'],
        queryFn: () => api.get<PlanUsageResponse>('/plans/usage'),
        refetchInterval: 30000,
    });
}
