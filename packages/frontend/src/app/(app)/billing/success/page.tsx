'use client';

import { useEffect, useEffectEvent, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { api, ApiError } from '@/lib/api';

export default function BillingSuccessPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [countdown, setCountdown] = useState(5);
    const [isConfirming, setIsConfirming] = useState(false);
    const [confirmError, setConfirmError] = useState<string | null>(null);
    const hasConfirmedRef = useRef(false);
    const tossTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const paymentKey = searchParams.get('paymentKey');
    const orderId = searchParams.get('orderId');
    const amount = searchParams.get('amount');
    const isTossRedirect = Boolean(paymentKey && orderId && amount);
    const parsedAmount = amount ? Number(amount) : Number.NaN;
    const hasValidTossParams = isTossRedirect && Number.isFinite(parsedAmount) && parsedAmount > 0;
    const displayError =
        confirmError ?? (isTossRedirect && !hasValidTossParams ? '결제 승인 정보가 올바르지 않습니다.' : null);

    // 컴포넌트 언마운트 시 Toss 타이머 cleanup
    useEffect(() => {
        return () => {
            if (tossTimerRef.current !== null) {
                clearInterval(tossTimerRef.current);
            }
        };
    }, []);

    const confirmTossPayment = useEffectEvent(async (
        confirmedPaymentKey: string,
        confirmedOrderId: string,
        confirmedAmount: number
    ) => {
        setIsConfirming(true);
        setConfirmError(null);

        try {
            await api.post('/billing/toss/confirm', {
                payment_key: confirmedPaymentKey,
                order_id: confirmedOrderId,
                amount: confirmedAmount,
            });

            tossTimerRef.current = setInterval(() => {
                setCountdown((prev) => {
                    if (prev <= 1) {
                        if (tossTimerRef.current !== null) {
                            clearInterval(tossTimerRef.current);
                            tossTimerRef.current = null;
                        }
                        router.push('/settings');
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);
        } catch (error) {
            if (error instanceof ApiError) {
                setConfirmError(`결제 승인에 실패했습니다. (${error.status})`);
                return;
            }

            setConfirmError(
                error instanceof Error ? error.message : '결제 승인 중 오류가 발생했습니다.'
            );
        } finally {
            setIsConfirming(false);
        }
    });

    useEffect(() => {
        if (isTossRedirect) {
            return;
        }

        const timer = setInterval(() => {
            setCountdown((prev) => {
                if (prev <= 1) {
                    clearInterval(timer);
                    router.push('/settings');
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);

        return () => clearInterval(timer);
    }, [isTossRedirect, router]);

    useEffect(() => {
        if (!hasValidTossParams || hasConfirmedRef.current || !paymentKey || !orderId) {
            return;
        }

        hasConfirmedRef.current = true;
        void confirmTossPayment(paymentKey, orderId, parsedAmount);
    }, [hasValidTossParams, orderId, parsedAmount, paymentKey]);

    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6">
            <div
                className={`flex items-center justify-center w-16 h-16 rounded-full ${
                    displayError ? 'bg-red-500/10' : 'bg-green-500/10'
                }`}
            >
                {displayError ? (
                    <AlertCircle className="h-8 w-8 text-red-500" />
                ) : (
                    <CheckCircle2 className="h-8 w-8 text-green-500" />
                )}
            </div>
            <div className="text-center space-y-2">
                <h2 className="text-2xl font-bold">
                    {displayError ? '결제 승인이 필요합니다' : '결제가 완료되었습니다!'}
                </h2>
                <p className="text-muted-foreground">
                    {displayError
                        ? displayError
                        : isConfirming
                          ? '토스 결제 승인 후 구독을 활성화하고 있습니다...'
                          : `구독이 활성화되었습니다. ${countdown}초 후 설정 페이지로 이동합니다...`}
                </p>
            </div>
            <div className="flex items-center gap-3">
                <Button onClick={() => router.push('/settings')}>
                    설정으로 이동
                </Button>
                <Button variant="outline" onClick={() => router.push('/')}>
                    대시보드로 이동
                </Button>
            </div>
            {isConfirming && (
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            )}
        </div>
    );
}
