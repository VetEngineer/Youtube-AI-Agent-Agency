import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface SubscriptionData {
    plan: string;
    status: string;
    current_period_end: string | null;
}

interface CheckoutResponse {
    checkout_url: string;
}

interface PortalResponse {
    portal_url: string;
}

export function useSubscription() {
    return useQuery({
        queryKey: ['billing', 'subscription'],
        queryFn: () => api.get<SubscriptionData>('/billing/subscription'),
        retry: (failureCount, error) => {
            if (error instanceof Error && error.message.includes('401')) return false;
            if (error instanceof Error && error.message.includes('501')) return false;
            return failureCount < 2;
        },
    });
}

export function useCheckout() {
    return useMutation({
        mutationFn: async (plan: string) => {
            const result = await api.post<CheckoutResponse>('/billing/checkout', { plan });
            window.location.href = result.checkout_url;
            return result;
        },
    });
}

export function usePortal() {
    return useMutation({
        mutationFn: async () => {
            const result = await api.post<PortalResponse>('/billing/portal', {});
            window.location.href = result.portal_url;
            return result;
        },
    });
}
