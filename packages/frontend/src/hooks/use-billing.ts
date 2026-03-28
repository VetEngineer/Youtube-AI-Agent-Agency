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

interface TossCheckoutResponse {
    client_key: string;
    amount: number;
    order_id: string;
    order_name: string;
    customer_key: string;
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

export function useTossCheckout() {
    return useMutation({
        mutationFn: async (plan: string) => {
            const result = await api.post<TossCheckoutResponse>('/billing/toss/checkout', { plan });

            const { loadTossPayments } = await import('@tosspayments/tosspayments-sdk');
            const tossPayments = await loadTossPayments(result.client_key);
            const payment = tossPayments.payment({ customerKey: result.customer_key });

            await payment.requestPayment({
                method: 'CARD',
                amount: { currency: 'KRW', value: result.amount },
                orderId: result.order_id,
                orderName: result.order_name,
                successUrl: `${window.location.origin}/billing/success`,
                failUrl: `${window.location.origin}/billing/cancel`,
            });

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
