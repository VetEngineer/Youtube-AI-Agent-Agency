'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useCreatePipeline } from '@/hooks/use-pipeline';
import { useChannels } from '@/hooks/use-channels';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { AlertCircle, ArrowLeft, Loader2 } from 'lucide-react';

export default function PipelineNewPage() {
    const router = useRouter();
    const createPipeline = useCreatePipeline();
    const { data: channelsData, isLoading: channelsLoading, error: channelsError } = useChannels();

    const [formData, setFormData] = useState({
        topic: '',
        channel_id: '',
        brand_name: '',
        dry_run: false,
    });
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!formData.topic.trim()) {
            setError('Topic is required');
            return;
        }
        if (!formData.channel_id) {
            setError('Please select a channel');
            return;
        }

        try {
            const result = await createPipeline.mutateAsync({
                channel_id: formData.channel_id,
                topic: formData.topic.trim(),
                brand_name: formData.brand_name.trim() || undefined,
                dry_run: formData.dry_run,
            });
            router.push(`/pipelines/${result.run_id}`);
        } catch (err) {
            if (err instanceof Error) {
                setError(err.message);
            } else {
                setError('Failed to create pipeline. Please try again.');
            }
        }
    };

    const channels = channelsData?.channels || [];

    return (
        <div className="max-w-2xl mx-auto space-y-6">
            <div className="flex items-center gap-4">
                <Button variant="ghost" size="icon" asChild>
                    <Link href="/">
                        <ArrowLeft className="h-4 w-4" />
                    </Link>
                </Button>
                <div>
                    <h3 className="text-lg font-medium">Create New Pipeline</h3>
                    <p className="text-sm text-muted-foreground">
                        Start a new AI content generation process.
                    </p>
                </div>
            </div>

            {error && (
                <div className="flex items-center gap-2 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    <span className="text-sm">{error}</span>
                </div>
            )}

            <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-2">
                        <Label htmlFor="topic">Topic / Keyword *</Label>
                        <Input
                            id="topic"
                            placeholder="e.g. Top 10 AI Tools in 2026"
                            value={formData.topic}
                            onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                            disabled={createPipeline.isPending}
                        />
                        <p className="text-xs text-muted-foreground">
                            The main subject of your video content
                        </p>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="channel">Channel *</Label>
                        {channelsLoading ? (
                            <div className="flex items-center gap-2 p-3 border rounded-md">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                <span className="text-sm text-muted-foreground">Loading channels...</span>
                            </div>
                        ) : channelsError ? (
                            <div className="flex items-center gap-2 p-3 border border-red-500/20 rounded-md bg-red-500/10">
                                <AlertCircle className="h-4 w-4 text-red-400" />
                                <span className="text-sm text-red-400">Failed to load channels</span>
                            </div>
                        ) : channels.length === 0 ? (
                            <div className="p-3 border rounded-md text-sm text-muted-foreground">
                                No channels available. Please add a channel first.
                            </div>
                        ) : (
                            <Select
                                value={formData.channel_id}
                                onValueChange={(val) => setFormData({ ...formData, channel_id: val })}
                                disabled={createPipeline.isPending}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select a channel" />
                                </SelectTrigger>
                                <SelectContent>
                                    {channels.map((channel) => (
                                        <SelectItem key={channel.channel_id} value={channel.channel_id}>
                                            <div className="flex items-center gap-2">
                                                <span>{channel.name}</span>
                                                <span className="text-xs text-muted-foreground">({channel.category})</span>
                                            </div>
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="brand_name">Brand Name (Optional)</Label>
                        <Input
                            id="brand_name"
                            placeholder="e.g. TechReview"
                            value={formData.brand_name}
                            onChange={(e) => setFormData({ ...formData, brand_name: e.target.value })}
                            disabled={createPipeline.isPending}
                        />
                        <p className="text-xs text-muted-foreground">
                            Brand identity for the content
                        </p>
                    </div>

                    <div className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            id="dry_run"
                            checked={formData.dry_run}
                            onChange={(e) => setFormData({ ...formData, dry_run: e.target.checked })}
                            disabled={createPipeline.isPending}
                            className="h-4 w-4 rounded border-gray-300"
                        />
                        <Label htmlFor="dry_run" className="text-sm font-normal">
                            Dry Run (skip actual upload)
                        </Label>
                    </div>

                    <div className="pt-4 flex justify-end gap-3">
                        <Button variant="outline" type="button" asChild disabled={createPipeline.isPending}>
                            <Link href="/">Cancel</Link>
                        </Button>
                        <Button
                            type="submit"
                            disabled={createPipeline.isPending || !formData.topic || !formData.channel_id}
                        >
                            {createPipeline.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {createPipeline.isPending ? 'Creating...' : 'Start Pipeline'}
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}
