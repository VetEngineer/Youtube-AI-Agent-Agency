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

export function useCompetitors(workspaceId: string) {
    return useQuery({
        queryKey: ['competitors', workspaceId],
        queryFn: () =>
            api.get<CompetitorListResponse>(`/competitors/?workspace_id=${workspaceId}`),
        staleTime: 5 * 60 * 1000, // 5 minutes
        enabled: !!workspaceId,
    });
}

export function useCompetitor(competitorId: string) {
    return useQuery({
        queryKey: ['competitors', 'detail', competitorId],
        queryFn: () => api.get<CompetitorDetailResponse>(`/competitors/${competitorId}`),
        enabled: !!competitorId,
    });
}

export function useAddCompetitor(workspaceId: string) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: AddCompetitorRequest) =>
            api.post<CompetitorChannelInfo>(
                `/competitors/?workspace_id=${workspaceId}`,
                data,
            ),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['competitors', workspaceId] });
        },
    });
}

export function useDeleteCompetitor(workspaceId: string) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (competitorId: string) =>
            api.delete<void>(`/competitors/${competitorId}`),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['competitors', workspaceId] });
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
