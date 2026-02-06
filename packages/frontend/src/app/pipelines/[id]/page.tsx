'use client';

import { usePipeline } from '@/hooks/use-pipeline';
import { Badge } from '@/components/ui/badge';
import { useParams } from 'next/navigation';

export default function PipelineDetailPage() {
    const params = useParams();
    const id = params?.id as string;

    const { data: pipeline, isLoading, error } = usePipeline(id);

    if (isLoading) return <div>Loading pipeline details...</div>;
    if (error || !pipeline) return <div>Error loading pipeline.</div>;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight">{pipeline.topic}</h2>
                    <p className="text-sm text-muted-foreground">
                        Run ID: {pipeline.run_id}
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <Badge variant={pipeline.status === 'completed' ? 'default' : 'secondary'}>
                        {pipeline.status}
                    </Badge>
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
                <div className="md:col-span-2 space-y-6">
                    <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
                        <h3 className="font-semibold mb-4">Pipeline Progress</h3>
                        <div className="space-y-4">
                            <div className="flex items-center gap-4 p-4 border rounded-lg bg-muted/50">
                                <div className={`h-2 w-2 rounded-full ${pipeline.status === 'running' ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                                <div>
                                    <p className="font-medium">Current Agent: {pipeline.current_agent || 'Initializing...'}</p>
                                    <p className="text-sm text-muted-foreground capitalize">{pipeline.status}</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
                        <h3 className="font-semibold mb-4">Logs</h3>
                        <div className="bg-black text-white p-4 rounded-lg font-mono text-sm h-64 overflow-y-auto">
                            <div className="text-gray-500">[System] Pipeline initialized...</div>
                            {pipeline.errors && pipeline.errors.length > 0 && (
                                <div className="text-red-400">
                                    {pipeline.errors.map((e, i) => <div key={i}>[Error] {e}</div>)}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
                        <h3 className="font-semibold mb-4">Results</h3>
                        {pipeline.result ? (
                            <div className="space-y-4">
                                {pipeline.result.video_url && (
                                    <a
                                        href={pipeline.result.video_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="block p-3 bg-primary/10 text-primary rounded-md text-center hover:bg-primary/20 transition"
                                    >
                                        View Video
                                    </a>
                                )}
                                {pipeline.result.script && (
                                    <div className="p-3 border rounded-md max-h-40 overflow-y-auto text-sm">
                                        <p className="font-medium mb-1">Script Preview:</p>
                                        {pipeline.result.script.slice(0, 100)}...
                                    </div>
                                )}
                            </div>
                        ) : (
                            <p className="text-sm text-muted-foreground">No results yet.</p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
