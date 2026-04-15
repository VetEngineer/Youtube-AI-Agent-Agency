'use client';

import { Progress } from '@/components/ui/progress';
import { usePlanUsage } from '@/hooks/use-plans';
import { cn } from '@/lib/utils';

interface QuotaBadgeProps {
    className?: string;
}

export function QuotaBadge({ className }: QuotaBadgeProps) {
    const { data: usage, isLoading } = usePlanUsage();

    if (isLoading || !usage) {
        return (
            <div className={cn('flex items-center gap-2 text-sm', className)}>
                <div className="h-4 w-20 rounded bg-muted/20 animate-pulse motion-reduce:animate-none" />
            </div>
        );
    }

    const isUnlimited = usage.pipelines_limit === -1;
    const percentage = isUnlimited
        ? 0
        : Math.min((usage.pipelines_used / usage.pipelines_limit) * 100, 100);

    const isWarning = !isUnlimited && percentage >= 80;
    const isExceeded = !isUnlimited && percentage >= 100;

    const label = isUnlimited
        ? `${usage.pipelines_used} used`
        : `${usage.pipelines_used}/${usage.pipelines_limit}`;

    return (
        <div className={cn('space-y-1.5', className)}>
            <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Pipelines</span>
                <span
                    className={cn(
                        'font-medium',
                        isExceeded && 'text-red-400',
                        isWarning && !isExceeded && 'text-yellow-400',
                    )}
                >
                    {label}
                </span>
            </div>
            {!isUnlimited && (
                <Progress
                    value={percentage}
                    className={cn(
                        'h-2',
                        isExceeded && '[&>[data-slot=progress-indicator]]:bg-red-500',
                        isWarning && !isExceeded && '[&>[data-slot=progress-indicator]]:bg-yellow-500',
                    )}
                />
            )}
        </div>
    );
}
