'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useCreatePipeline } from '@/hooks/use-pipeline';
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

export default function PipelineNewPage() {
    const router = useRouter();
    const createPipeline = useCreatePipeline();

    const [formData, setFormData] = useState({
        topic: '',
        channel_id: '',
        style: 'informative',
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const result = await createPipeline.mutateAsync(formData);
            router.push(`/pipelines/${result.run_id}`);
        } catch (error) {
            console.error('Failed to create pipeline:', error);
        }
    };

    return (
        <div className="max-w-2xl mx-auto space-y-6">
            <div>
                <h3 className="text-lg font-medium">Create New Pipeline</h3>
                <p className="text-sm text-muted-foreground">
                    Start a new AI content generation process.
                </p>
            </div>

            <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-2">
                        <Label htmlFor="topic">Topic / Keyword</Label>
                        <Input
                            id="topic"
                            placeholder="e.g. Top 10 AI Tools in 2026"
                            value={formData.topic}
                            onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                            required
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="channel">Channel</Label>
                        {/* TODO: Load channels dynamically from API */}
                        <Select
                            value={formData.channel_id}
                            onValueChange={(val) => setFormData({ ...formData, channel_id: val })}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="Select a channel" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="manual-test">Manual Test Channel</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="style">Content Style</Label>
                        <Select
                            value={formData.style}
                            onValueChange={(val) => setFormData({ ...formData, style: val })}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="Select style" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="informative">Informative</SelectItem>
                                <SelectItem value="entertaining">Entertaining</SelectItem>
                                <SelectItem value="tutorial">Tutorial</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="pt-4 flex justify-end">
                        <Button type="submit" disabled={createPipeline.isPending || !formData.topic || !formData.channel_id}>
                            {createPipeline.isPending ? 'Creating...' : 'Start Pipeline'}
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}
