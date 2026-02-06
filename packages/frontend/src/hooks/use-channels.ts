import { useQuery } from '@tanstack/react-query';
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
