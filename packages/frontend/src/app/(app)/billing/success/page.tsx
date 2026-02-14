'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { CheckCircle2, Loader2 } from 'lucide-react';

export default function BillingSuccessPage() {
    const router = useRouter();
    const [countdown, setCountdown] = useState(5);

    useEffect(() => {
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
    }, [router]);

    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6">
            <div className="flex items-center justify-center w-16 h-16 rounded-full bg-green-500/10">
                <CheckCircle2 className="h-8 w-8 text-green-500" />
            </div>
            <div className="text-center space-y-2">
                <h2 className="text-2xl font-bold">Payment Successful</h2>
                <p className="text-muted-foreground">
                    Your subscription has been activated. Redirecting to settings in {countdown} seconds...
                </p>
            </div>
            <div className="flex items-center gap-3">
                <Button onClick={() => router.push('/settings')}>
                    Go to Settings
                </Button>
                <Button variant="outline" onClick={() => router.push('/')}>
                    Go to Dashboard
                </Button>
            </div>
            {countdown > 0 && (
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            )}
        </div>
    );
}
