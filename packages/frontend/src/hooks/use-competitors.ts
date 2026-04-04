import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface CompetitorChannelInfo {
    id: string;
    youtube_channel_id: string;
    name: string;
    description: string | null;
    subscriber_count: number;
    video_count: number;
    thumbnail_url: string | null;
    last_crawled_at: string | null;
    is_active: boolean;
}

export interface CompetitorVideoInfo {
    video_id: string;
    title: string;
    view_count: number;
    like_count: number;
    comment_count: number;
    published_at: string;
    tags: string[];
    duration_seconds: number | null;
    thumbnail_url: string | null;
}

export interface CompetitorListResponse {
    competitors: CompetitorChannelInfo[];
    total: number;
}

export interface CompetitorDetailResponse {
    channel: CompetitorChannelInfo;
    recent_videos: CompetitorVideoInfo[];
}

export interface AddCompetitorRequest {
    youtube_channel_id: string;
}

export interface IntegrationsInfo {
    youtube_api_key_set: boolean;
    youtube_api_key_masked: string | null;
    elevenlabs_api_key_set: boolean;
    elevenlabs_api_key_masked: string | null;
}

export function useCompetitors() {
    return useQuery({
        queryKey: ['competitors'],
        queryFn: () => api.get<CompetitorListResponse>('/competitors/'),
        staleTime: 5 * 60 * 1000,
    });
}

export function useCompetitor(competitorId: string) {
    return useQuery({
        queryKey: ['competitors', 'detail', competitorId],
        queryFn: () => api.get<CompetitorDetailResponse>(`/competitors/${competitorId}`),
        enabled: !!competitorId,
    });
}

export function useAddCompetitor() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: AddCompetitorRequest) =>
            api.post<CompetitorChannelInfo>('/competitors/', data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['competitors'] });
        },
    });
}

export function useDeleteCompetitor() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (competitorId: string) =>
            api.delete<void>(`/competitors/${competitorId}`),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['competitors'] });
        },
    });
}

export function useRefreshCompetitor() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (competitorId: string) =>
            api.post<CompetitorDetailResponse>(`/competitors/${competitorId}/refresh`, {}),
        onSuccess: (_data, competitorId) => {
            queryClient.invalidateQueries({ queryKey: ['competitors', 'detail', competitorId] });
            queryClient.invalidateQueries({ queryKey: ['competitors'] });
        },
    });
}

export function useIntegrations() {
    return useQuery({
        queryKey: ['settings', 'integrations'],
        queryFn: () => api.get<IntegrationsInfo>('/settings/integrations'),
        staleTime: 30 * 1000,
    });
}

export function useUpdateIntegrations() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: { youtube_api_key?: string; elevenlabs_api_key?: string }) =>
            api.patch<IntegrationsInfo>('/settings/integrations', data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['settings', 'integrations'] });
        },
    });
}
