import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface Channel {
    channel_id: string;
    name: string;
    category: string;
    has_brand_guide: boolean;
}

export interface ChannelsResponse {
    channels: Channel[];
    total: number;
}

export interface CreateChannelRequest {
    channel_id: string;
    name: string;
    category?: string;
}

export interface UpdateChannelRequest {
    name?: string;
    category?: string;
}

export function useChannels() {
    return useQuery({
        queryKey: ['channels'],
        queryFn: () => api.get<ChannelsResponse>('/channels/'),
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}

export function useChannel(channelId: string) {
    return useQuery({
        queryKey: ['channels', channelId],
        queryFn: () => api.get<Channel>(`/channels/${channelId}`),
        enabled: !!channelId,
    });
}

export function useCreateChannel() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: CreateChannelRequest) =>
            api.post<Channel>('/channels/', data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['channels'] });
        },
    });
}

export function useUpdateChannel() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ channelId, data }: { channelId: string; data: UpdateChannelRequest }) =>
            api.patch<Channel>(`/channels/${channelId}`, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['channels'] });
        },
    });
}

export function useDeleteChannel() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (channelId: string) =>
            api.delete<void>(`/channels/${channelId}`),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['channels'] });
        },
    });
}
