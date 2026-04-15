'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Plus, XCircle, Inbox } from 'lucide-react';
import { usePipelineRuns } from '@/hooks/use-pipeline';

const STATUS_FILTERS = ['all', 'pending', 'running', 'completed', 'failed'] as const;
type StatusFilter = (typeof STATUS_FILTERS)[number];

function getStatusBadge(status: string) {
    switch (status) {
        case 'completed':
            return <Badge className="bg-green-500/20 text-green-400 border-green-500/30">Completed</Badge>;
        case 'running':
            return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">Running</Badge>;
        case 'failed':
            return <Badge className="bg-red-500/20 text-red-400 border-red-500/30">Failed</Badge>;
        case 'pending':
            return <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30">Pending</Badge>;
        default:
            return <Badge variant="secondary">{status}</Badge>;
    }
}

function formatDuration(createdAt: string, completedAt: string | null): string {
    if (!completedAt) return '-';
    const ms = new Date(completedAt).getTime() - new Date(createdAt).getTime();
    const secs = Math.floor(ms / 1000);
    const mins = Math.floor(secs / 60);
    const rem = secs % 60;
    return mins > 0 ? `${mins}m ${rem}s` : `${secs}s`;
}

export default function PipelinesPage() {
    const router = useRouter();
    const [filter, setFilter] = useState<StatusFilter>('all');
    const { data, isLoading, error } = usePipelineRuns({ status: filter === 'all' ? undefined : filter });

    const runs = data?.runs ?? [];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold text-balance">Pipelines</h2>
                    <p className="text-muted-foreground text-pretty">All pipeline executions.</p>
                </div>
                <Button asChild>
                    <Link href="/pipelines/new">
                        <Plus className="mr-2 h-4 w-4" /> New Pipeline
                    </Link>
                </Button>
            </div>

            <div className="flex gap-2 flex-wrap">
                {STATUS_FILTERS.map((s) => (
                    <Button
                        key={s}
                        variant={filter === s ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setFilter(s)}
                        className="capitalize"
                    >
                        {s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
                    </Button>
                ))}
            </div>

            {isLoading && (
                <div className="space-y-2">
                    {[1, 2, 3, 4, 5].map((i) => (
                        <Skeleton key={i} className="h-14 w-full rounded-lg" />
                    ))}
                </div>
            )}

            {error && (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                    <XCircle className="h-10 w-10 text-red-400 mb-3" />
                    <p className="text-sm text-muted-foreground">파이프라인 목록을 불러오지 못했습니다.</p>
                </div>
            )}

            {!isLoading && !error && runs.length === 0 && (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                    <div className="mb-4">
                        <div className="flex size-16 items-center justify-center rounded-full bg-primary/10 border border-primary/20">
                            <Inbox className="size-7 text-primary" />
                        </div>
                    </div>
                    <h3 className="text-lg font-semibold mb-1 text-balance">파이프라인이 없습니다</h3>
                    <p className="text-sm text-muted-foreground mb-4 text-pretty">첫 번째 파이프라인을 실행해 보세요.</p>
                    <Button asChild>
                        <Link href="/pipelines/new">
                            <Plus className="mr-2 h-4 w-4" /> New Pipeline
                        </Link>
                    </Button>
                </div>
            )}

            {!isLoading && !error && runs.length > 0 && (
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                    {runs.map((run) => (
                        <div
                            key={run.run_id}
                            className="group rounded-xl border border-border bg-card p-4 cursor-pointer transition-all hover:border-primary/30"
                            onClick={() => router.push(`/pipelines/${run.run_id}`)}
                        >
                            <div className="flex items-start justify-between gap-2 mb-3">
                                <p className="text-sm font-medium leading-snug line-clamp-2 flex-1">{run.topic}</p>
                                {getStatusBadge(run.status)}
                            </div>
                            <div className="flex items-center justify-between text-xs text-muted-foreground">
                                <span className="truncate max-w-[120px]">{run.channel_id}</span>
                                <div className="flex items-center gap-2 shrink-0">
                                    <span>{formatDuration(run.created_at, run.completed_at)}</span>
                                    <span>{new Date(run.created_at).toLocaleDateString()}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
