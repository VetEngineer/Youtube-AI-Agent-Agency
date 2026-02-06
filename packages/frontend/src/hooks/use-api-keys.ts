import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface ApiKey {
    key_id: string;
    name: string;
    prefix: string;
    scopes: string[];
    created_at: string;
    expires_at: string | null;
    last_used_at: string | null;
    is_active: boolean;
}

export interface ApiKeysResponse {
    api_keys: ApiKey[];
    total: number;
}

export interface CreateApiKeyRequest {
    name: string;
    scopes: string[];
    expires_days?: number | null;
}

export interface CreateApiKeyResponse {
    key_id: string;
    name: string;
    key: string; // Plaintext key, shown only once
    prefix: string;
    scopes: string[];
    expires_at: string | null;
}

export function useApiKeys() {
    return useQuery({
        queryKey: ['admin', 'api-keys'],
        queryFn: () => api.get<ApiKeysResponse>('/admin/api-keys'),
        retry: (failureCount, error) => {
            // Don't retry on 401/403
            if (error instanceof Error && error.message.includes('401')) return false;
            if (error instanceof Error && error.message.includes('403')) return false;
            return failureCount < 2;
        },
    });
}

export function useCreateApiKey() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: CreateApiKeyRequest) =>
            api.post<CreateApiKeyResponse>('/admin/api-keys', data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin', 'api-keys'] });
        },
    });
}

export function useDeleteApiKey() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (keyId: string) =>
            api.delete<void>(`/admin/api-keys/${keyId}`),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin', 'api-keys'] });
        },
    });
}
