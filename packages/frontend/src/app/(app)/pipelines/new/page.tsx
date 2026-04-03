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
import { AlertCircle, ArrowLeft, Loader2, HelpCircle, Plus } from 'lucide-react';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip';

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
    const [topicError, setTopicError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!formData.topic.trim()) {
            setError('주제를 입력해 주세요.');
            return;
        }
        if (!formData.channel_id) {
            setError('채널을 선택해 주세요.');
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
                setError('파이프라인 생성에 실패했습니다. 다시 시도해 주세요.');
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
                            placeholder="예: 2026년 AI 트렌드 전망"
                            value={formData.topic}
                            onChange={(e) => {
                                setFormData({ ...formData, topic: e.target.value });
                                if (topicError && e.target.value.trim()) setTopicError(null);
                            }}
                            onBlur={() => {
                                if (!formData.topic.trim()) setTopicError('주제를 입력해 주세요.');
                            }}
                            disabled={createPipeline.isPending}
                            className={topicError ? 'border-red-500/50' : ''}
                        />
                        {topicError ? (
                            <p className="text-xs text-red-400">{topicError}</p>
                        ) : (
                            <p className="text-xs text-muted-foreground">
                                AI가 이 주제를 기반으로 영상 콘텐츠를 생성합니다
                            </p>
                        )}
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
                            <div className="rounded-lg border border-border bg-muted/30 p-4 text-center">
                                <p className="text-sm text-muted-foreground mb-2">등록된 채널이 없습니다.</p>
                                <Button size="sm" variant="outline" asChild>
                                    <Link href="/channels">
                                        <Plus className="mr-1 h-3 w-3" /> 채널 등록하기
                                    </Link>
                                </Button>
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
                        <div className="flex items-center gap-1.5">
                            <Label htmlFor="brand_name">Brand Name (Optional)</Label>
                            <TooltipProvider delayDuration={200}>
                                <Tooltip>
                                    <TooltipTrigger type="button">
                                        <HelpCircle className="h-3.5 w-3.5 text-muted-foreground" />
                                    </TooltipTrigger>
                                    <TooltipContent side="right" className="max-w-[220px]">
                                        원고와 콘텐츠에 반영할 브랜드 이름입니다. 예: "TechReview"를 입력하면 해당 브랜드 스타일로 스크립트가 작성됩니다.
                                    </TooltipContent>
                                </Tooltip>
                            </TooltipProvider>
                        </div>
                        <Input
                            id="brand_name"
                            placeholder="e.g. TechReview"
                            value={formData.brand_name}
                            onChange={(e) => setFormData({ ...formData, brand_name: e.target.value })}
                            disabled={createPipeline.isPending}
                        />
                        <p className="text-xs text-muted-foreground">
                            입력하지 않으면 채널 이름이 사용됩니다
                        </p>
                    </div>

                    <div className="flex items-start gap-2">
                        <input
                            type="checkbox"
                            id="dry_run"
                            checked={formData.dry_run}
                            onChange={(e) => setFormData({ ...formData, dry_run: e.target.checked })}
                            disabled={createPipeline.isPending}
                            className="h-4 w-4 rounded border-gray-300 mt-0.5"
                        />
                        <div className="space-y-0.5">
                            <div className="flex items-center gap-1.5">
                                <Label htmlFor="dry_run" className="text-sm font-normal">
                                    Dry Run 모드
                                </Label>
                                <TooltipProvider delayDuration={200}>
                                    <Tooltip>
                                        <TooltipTrigger type="button">
                                            <HelpCircle className="h-3.5 w-3.5 text-muted-foreground" />
                                        </TooltipTrigger>
                                        <TooltipContent side="right" className="max-w-[240px]">
                                            실제 AI 모델을 호출하지 않고 파이프라인 흐름을 시뮬레이션합니다. 비용 없이 설정이 올바른지 확인할 때 사용하세요.
                                        </TooltipContent>
                                    </Tooltip>
                                </TooltipProvider>
                            </div>
                            <p className="text-xs text-muted-foreground">
                                실제 업로드 없이 파이프라인 전체 흐름을 테스트합니다
                            </p>
                        </div>
                    </div>

                    <div className="pt-4 flex justify-end gap-3">
                        <Button variant="outline" type="button" asChild disabled={createPipeline.isPending}>
                            <Link href="/">Cancel</Link>
                        </Button>
                        <Button
                            type="submit"
                            disabled={createPipeline.isPending || channelsLoading || !formData.topic || !formData.channel_id}
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
