'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { XCircle } from 'lucide-react';

export default function BillingCancelPage() {
    const router = useRouter();

    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6">
            <div className="flex items-center justify-center size-16 rounded-full bg-red-500/10">
                <XCircle className="h-8 w-8 text-red-500" />
            </div>
            <div className="text-center space-y-2">
                <h2 className="text-2xl font-bold text-balance">결제가 취소되었습니다</h2>
                <p className="text-muted-foreground">
                    결제가 취소되었습니다. 요금이 청구되지 않았습니다.
                </p>
            </div>
            <div className="flex items-center gap-3">
                <Button onClick={() => router.push('/settings')}>
                    설정으로 돌아가기
                </Button>
                <Button variant="outline" onClick={() => router.push('/')}>
                    대시보드로 이동
                </Button>
            </div>
        </div>
    );
}
