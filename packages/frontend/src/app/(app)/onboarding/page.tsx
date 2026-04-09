'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import { useCreateChannel } from '@/hooks/use-channels';
import { ApiError } from '@/lib/api';

function slugify(name: string): string {
    return name
        .toLowerCase()
        .replace(/[^a-z0-9가-힣\s-]/g, '')
        .trim()
        .replace(/[\s]+/g, '-')
        .replace(/-+/g, '-')
        .slice(0, 50) || 'channel';
}

const TOTAL_STEPS = 3;

function StepIndicator({ currentStep }: { currentStep: number }) {
    return (
        <div className="flex items-center justify-center gap-2 mb-8">
            {Array.from({ length: TOTAL_STEPS }, (_, i) => {
                const step = i + 1;
                const isActive = step === currentStep;
                const isCompleted = step < currentStep;

                return (
                    <div key={step} className="flex items-center gap-2">
                        <div
                            className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-colors ${
                                isActive
                                    ? 'bg-primary text-primary-foreground'
                                    : isCompleted
                                      ? 'bg-primary/20 text-primary'
                                      : 'bg-muted text-muted-foreground'
                            }`}
                        >
                            {isCompleted ? (
                                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                                </svg>
                            ) : (
                                step
                            )}
                        </div>
                        {step < TOTAL_STEPS && (
                            <div
                                className={`h-px w-12 transition-colors ${
                                    isCompleted ? 'bg-primary' : 'bg-muted'
                                }`}
                            />
                        )}
                    </div>
                );
            })}
        </div>
    );
}

function WelcomeStep({ onNext }: { onNext: () => void }) {
    return (
        <Card className="mx-auto max-w-lg">
            <CardHeader className="text-center">
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
                    <svg className="h-8 w-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
                    </svg>
                </div>
                <CardTitle className="text-2xl">환영합니다!</CardTitle>
                <CardDescription className="text-base">
                    YouTube AI Agent Agency에 가입해 주셔서 감사합니다.
                    AI가 YouTube 콘텐츠 제작을 자동화하는 과정을 안내해 드리겠습니다.
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="rounded-lg border border-border/50 p-4 space-y-3">
                    <h4 className="font-medium text-sm">시작하기 전에 알아두세요</h4>
                    <ul className="space-y-2 text-sm text-muted-foreground">
                        <li className="flex items-start gap-2">
                            <Badge variant="secondary" className="mt-0.5 shrink-0">1</Badge>
                            채널을 생성하고 브랜드 정보를 설정합니다
                        </li>
                        <li className="flex items-start gap-2">
                            <Badge variant="secondary" className="mt-0.5 shrink-0">2</Badge>
                            주제를 입력하면 AI가 6단계 파이프라인을 실행합니다
                        </li>
                        <li className="flex items-start gap-2">
                            <Badge variant="secondary" className="mt-0.5 shrink-0">3</Badge>
                            완성된 콘텐츠를 검토하고 YouTube에 업로드합니다
                        </li>
                    </ul>
                </div>
            </CardContent>
            <CardFooter>
                <Button onClick={onNext} className="w-full">
                    시작하기
                </Button>
            </CardFooter>
        </Card>
    );
}

function CreateChannelStep({
    onNext,
    onBack,
}: {
    onNext: () => void;
    onBack: () => void;
}) {
    const [channelName, setChannelName] = useState('');
    const [description, setDescription] = useState('');
    const [targetAudience, setTargetAudience] = useState('');
    const [errorMsg, setErrorMsg] = useState('');
    const [created, setCreated] = useState(false);
    const createChannel = useCreateChannel();
    const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        return () => {
            if (timerRef.current) clearTimeout(timerRef.current);
        };
    }, []);

    const isValid = channelName.trim().length > 0;

    const buildDescription = () => {
        const parts = [description.trim(), targetAudience.trim() ? `타겟: ${targetAudience.trim()}` : ''].filter(Boolean);
        return parts.join(' / ') || undefined;
    };

    const handleCreate = async () => {
        setErrorMsg('');
        try {
            await createChannel.mutateAsync({
                channel_id: slugify(channelName),
                name: channelName.trim(),
                category: 'general',
                description: buildDescription(),
            });
            setCreated(true);
            timerRef.current = setTimeout(() => onNext(), 800);
        } catch (err) {
            if (err instanceof ApiError && err.status === 409) {
                setErrorMsg('같은 이름의 채널이 이미 존재합니다. 다른 이름을 사용해 주세요.');
            } else {
                setErrorMsg('채널 생성에 실패했습니다. 다시 시도해 주세요.');
            }
        }
    };

    return (
        <Card className="mx-auto max-w-lg">
            <CardHeader>
                <CardTitle>첫 번째 채널 만들기</CardTitle>
                <CardDescription>
                    YouTube 채널 정보를 입력하세요. 나중에 언제든 수정할 수 있습니다.
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="space-y-2">
                    <Label htmlFor="channel-name">채널 이름 *</Label>
                    <Input
                        id="channel-name"
                        placeholder="예: 테크 인사이트"
                        value={channelName}
                        onChange={(e) => setChannelName(e.target.value)}
                    />
                </div>
                <div className="space-y-2">
                    <Label htmlFor="description">채널 설명</Label>
                    <Input
                        id="description"
                        placeholder="예: IT 기술 트렌드와 리뷰를 다루는 채널"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                    />
                </div>
                <div className="space-y-2">
                    <Label htmlFor="target-audience">타겟 시청자</Label>
                    <Input
                        id="target-audience"
                        placeholder="예: 20-30대 IT 종사자"
                        value={targetAudience}
                        onChange={(e) => setTargetAudience(e.target.value)}
                    />
                </div>
                {created && (
                    <div className="flex items-center gap-2 text-sm text-green-400">
                        <CheckCircle className="h-4 w-4 shrink-0" />
                        채널이 생성됐습니다! 다음 단계로 이동 중...
                    </div>
                )}
                {errorMsg && (
                    <div className="flex items-center gap-2 text-sm text-red-500">
                        <AlertCircle className="h-4 w-4 shrink-0" />
                        {errorMsg}
                    </div>
                )}
            </CardContent>
            <CardFooter className="flex gap-3">
                <Button variant="outline" onClick={onBack} disabled={createChannel.isPending} className="flex-1">
                    이전
                </Button>
                <Button onClick={handleCreate} disabled={!isValid || createChannel.isPending} className="flex-1">
                    {createChannel.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    채널 생성
                </Button>
            </CardFooter>
        </Card>
    );
}

function TryPipelineStep({ onBack }: { onBack: () => void }) {
    const router = useRouter();
    const [topic, setTopic] = useState('');

    const handleFinish = () => {
        localStorage.removeItem('onboarding_step');
        router.push('/pipelines');
    };

    const handleTryDryRun = () => {
        // In the future, this will trigger an actual dry run.
        // For now, navigate to pipelines/new with pre-filled topic.
        router.push(`/pipelines/new${topic ? `?topic=${encodeURIComponent(topic)}` : ''}`);
    };

    return (
        <Card className="mx-auto max-w-lg">
            <CardHeader>
                <CardTitle>샘플 파이프라인 실행</CardTitle>
                <CardDescription>
                    주제를 입력하고 AI 파이프라인을 테스트해 보세요.
                    Dry Run 모드로 실제 비용 없이 미리보기가 가능합니다.
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="space-y-2">
                    <Label htmlFor="topic">영상 주제</Label>
                    <Input
                        id="topic"
                        placeholder="예: 2026년 AI 트렌드 전망"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                    />
                </div>
                <div className="rounded-lg border border-border/50 bg-muted/30 p-4">
                    <h4 className="mb-2 text-sm font-medium">Dry Run 모드란?</h4>
                    <p className="text-xs text-muted-foreground">
                        실제 AI 모델을 호출하지 않고 파이프라인의 각 단계를 시뮬레이션합니다.
                        실행 흐름을 확인하고, 설정이 올바른지 검증할 수 있습니다.
                    </p>
                </div>
            </CardContent>
            <CardFooter className="flex flex-col gap-3">
                <div className="flex w-full gap-3">
                    <Button variant="outline" onClick={onBack} className="flex-1">
                        이전
                    </Button>
                    <Button onClick={handleTryDryRun} className="flex-1">
                        Dry Run 실행
                    </Button>
                </div>
                <Button
                    variant="ghost"
                    onClick={handleFinish}
                    className="w-full text-muted-foreground"
                >
                    건너뛰고 대시보드로 이동
                </Button>
            </CardFooter>
        </Card>
    );
}

export default function OnboardingPage() {
    const [currentStep, setCurrentStep] = useState<number>(1);

    useEffect(() => {
        const saved = parseInt(localStorage.getItem('onboarding_step') ?? '1', 10);
        const clamped = Math.min(Math.max(saved, 1), TOTAL_STEPS);
        setCurrentStep(clamped);
    }, []);

    useEffect(() => {
        localStorage.setItem('onboarding_step', String(currentStep));
    }, [currentStep]);

    const goNext = () => setCurrentStep((prev) => Math.min(prev + 1, TOTAL_STEPS));
    const goBack = () => setCurrentStep((prev) => Math.max(prev - 1, 1));

    return (
        <div className="flex min-h-[calc(100dvh-4rem)] flex-col items-center justify-center py-12">
            <StepIndicator currentStep={currentStep} />
            {currentStep === 1 && <WelcomeStep onNext={goNext} />}
            {currentStep === 2 && <CreateChannelStep onNext={goNext} onBack={goBack} />}
            {currentStep === 3 && <TryPipelineStep onBack={goBack} />}
        </div>
    );
}
