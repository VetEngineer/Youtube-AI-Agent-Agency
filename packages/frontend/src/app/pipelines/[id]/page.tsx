'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { usePipeline, PIPELINE_STAGES } from '@/hooks/use-pipeline';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Plus, RotateCcw, ExternalLink, CheckCircle, Circle, Loader2, XCircle } from 'lucide-react';

function getStageStatus(currentAgent: string | null, stageKey: string, pipelineStatus: string): 'completed' | 'current' | 'pending' | 'failed' {
    if (pipelineStatus === 'failed') {
        const stageIndex = PIPELINE_STAGES.findIndex(s => s.key === stageKey);
        const currentIndex = PIPELINE_STAGES.findIndex(s => s.key === currentAgent);
        if (currentIndex >= 0 && stageIndex === currentIndex) return 'failed';
        if (stageIndex < currentIndex) return 'completed';
        return 'pending';
    }
    if (pipelineStatus === 'completed') return 'completed';
    if (!currentAgent) return 'pending';

    const stageIndex = PIPELINE_STAGES.findIndex(s => s.key === stageKey);
    const currentIndex = PIPELINE_STAGES.findIndex(s => s.key === currentAgent);

    if (stageIndex < currentIndex) return 'completed';
    if (stageIndex === currentIndex) return 'current';
    return 'pending';
}

function StageIcon({ status }: { status: 'completed' | 'current' | 'pending' | 'failed' }) {
    switch (status) {
        case 'completed':
            return <CheckCircle className="h-5 w-5 text-green-500" />;
        case 'current':
            return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
        case 'failed':
            return <XCircle className="h-5 w-5 text-red-500" />;
        default:
            return <Circle className="h-5 w-5 text-muted-foreground" />;
    }
}

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

export default function PipelineDetailPage() {
    const params = useParams();
    const id = params?.id as string;

    const { data: pipeline, isLoading, error } = usePipeline(id);

    if (isLoading) {
        return (
            <div className="space-y-6">
                <div className="flex items-center gap-4">
                    <div className="h-8 w-8 rounded bg-muted/20 animate-pulse" />
                    <div className="space-y-2">
                        <div className="h-6 w-48 rounded bg-muted/20 animate-pulse" />
                        <div className="h-4 w-32 rounded bg-muted/20 animate-pulse" />
                    </div>
                </div>
                <div className="h-64 rounded-xl bg-muted/20 animate-pulse" />
            </div>
        );
    }

    if (error || !pipeline) {
        return (
            <div className="flex flex-col items-center justify-center py-12 text-center">
                <XCircle className="h-12 w-12 text-red-400 mb-4" />
                <h3 className="text-lg font-semibold">Pipeline not found</h3>
                <p className="text-sm text-muted-foreground mt-1">The pipeline may have been deleted or the ID is invalid.</p>
                <Button asChild className="mt-4">
                    <Link href="/">
                        <ArrowLeft className="mr-2 h-4 w-4" /> Back to Dashboard
                    </Link>
                </Button>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" asChild>
                        <Link href="/">
                            <ArrowLeft className="h-4 w-4" />
                        </Link>
                    </Button>
                    <div>
                        <h2 className="text-2xl font-bold tracking-tight">{pipeline.topic}</h2>
                        <p className="text-sm text-muted-foreground">
                            {pipeline.channel_id} {pipeline.dry_run && '(Dry Run)'}
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    {getStatusBadge(pipeline.status)}
                    {(pipeline.status === 'completed' || pipeline.status === 'failed') && (
                        <Button variant="outline" size="sm" asChild>
                            <Link href="/pipelines/new">
                                <Plus className="mr-2 h-4 w-4" /> New Pipeline
                            </Link>
                        </Button>
                    )}
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
                <div className="md:col-span-2 space-y-6">
                    <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
                        <h3 className="font-semibold mb-4">Pipeline Progress</h3>
                        <div className="space-y-1">
                            {PIPELINE_STAGES.map((stage, index) => {
                                const status = getStageStatus(pipeline.current_agent, stage.key, pipeline.status);
                                return (
                                    <div key={stage.key} className="flex items-center gap-4">
                                        <div className="flex flex-col items-center">
                                            <StageIcon status={status} />
                                            {index < PIPELINE_STAGES.length - 1 && (
                                                <div className={`w-0.5 h-8 ${status === 'completed' ? 'bg-green-500' : 'bg-muted'}`} />
                                            )}
                                        </div>
                                        <div className={`flex-1 py-2 ${status === 'current' ? 'font-medium' : ''}`}>
                                            <div className="flex items-center gap-2">
                                                <span className="text-lg">{stage.icon}</span>
                                                <span>{stage.label}</span>
                                                {status === 'current' && (
                                                    <span className="text-xs text-blue-400 animate-pulse">In progress...</span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
                        <h3 className="font-semibold mb-4">Execution Log</h3>
                        <div className="bg-black/50 text-white p-4 rounded-lg font-mono text-sm h-48 overflow-y-auto">
                            <div className="text-gray-400">[{new Date(pipeline.created_at).toLocaleTimeString()}] Pipeline initialized</div>
                            {pipeline.current_agent && (
                                <div className="text-blue-400">[{new Date(pipeline.updated_at).toLocaleTimeString()}] Running: {pipeline.current_agent}</div>
                            )}
                            {pipeline.completed_at && (
                                <div className="text-green-400">[{new Date(pipeline.completed_at).toLocaleTimeString()}] Pipeline completed</div>
                            )}
                            {pipeline.errors && pipeline.errors.length > 0 && (
                                <div className="text-red-400 mt-2">
                                    {pipeline.errors.map((e, i) => (
                                        <div key={i}>[Error] {e}</div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
                        <h3 className="font-semibold mb-4">Details</h3>
                        <dl className="space-y-3 text-sm">
                            <div>
                                <dt className="text-muted-foreground">Run ID</dt>
                                <dd className="font-mono text-xs truncate">{pipeline.run_id}</dd>
                            </div>
                            <div>
                                <dt className="text-muted-foreground">Channel</dt>
                                <dd>{pipeline.channel_id}</dd>
                            </div>
                            {pipeline.brand_name && (
                                <div>
                                    <dt className="text-muted-foreground">Brand</dt>
                                    <dd>{pipeline.brand_name}</dd>
                                </div>
                            )}
                            <div>
                                <dt className="text-muted-foreground">Created</dt>
                                <dd>{new Date(pipeline.created_at).toLocaleString()}</dd>
                            </div>
                            {pipeline.completed_at && (
                                <div>
                                    <dt className="text-muted-foreground">Completed</dt>
                                    <dd>{new Date(pipeline.completed_at).toLocaleString()}</dd>
                                </div>
                            )}
                        </dl>
                    </div>

                    <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
                        <h3 className="font-semibold mb-4">Results</h3>
                        {pipeline.result ? (
                            <div className="space-y-4">
                                {pipeline.result.video_url && (
                                    <a
                                        href={pipeline.result.video_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center justify-center gap-2 p-3 bg-primary/10 text-primary rounded-md hover:bg-primary/20 transition"
                                    >
                                        <ExternalLink className="h-4 w-4" />
                                        View Video
                                    </a>
                                )}
                                {pipeline.result.script && (
                                    <div className="p-3 border rounded-md max-h-40 overflow-y-auto text-sm">
                                        <p className="font-medium mb-2">Script Preview:</p>
                                        <p className="text-muted-foreground whitespace-pre-wrap">
                                            {pipeline.result.script.slice(0, 200)}
                                            {pipeline.result.script.length > 200 && '...'}
                                        </p>
                                    </div>
                                )}
                                {pipeline.result.images && pipeline.result.images.length > 0 && (
                                    <div className="p-3 border rounded-md">
                                        <p className="font-medium mb-2">Generated Images</p>
                                        <p className="text-sm text-muted-foreground">
                                            {pipeline.result.images.length} image(s) generated
                                        </p>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="text-sm text-muted-foreground text-center py-4">
                                {pipeline.status === 'running' || pipeline.status === 'pending'
                                    ? 'Results will appear here when complete...'
                                    : 'No results available.'}
                            </div>
                        )}
                    </div>

                    {pipeline.status === 'failed' && (
                        <Button variant="outline" className="w-full" asChild>
                            <Link href="/pipelines/new">
                                <RotateCcw className="mr-2 h-4 w-4" /> Retry with Same Topic
                            </Link>
                        </Button>
                    )}
                </div>
            </div>
        </div>
    );
}
