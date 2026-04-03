import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const pipelineSteps = [
    {
        step: '01',
        title: '브랜드 리서치',
        description: '채널 브랜드와 타겟 시청자를 AI가 분석하여 최적의 콘텐츠 전략을 수립합니다.',
        icon: (
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
            </svg>
        ),
    },
    {
        step: '02',
        title: '원고 생성',
        description: 'Claude AI가 리서치 결과를 기반으로 영상 스크립트를 자동으로 작성합니다.',
        icon: (
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
        ),
    },
    {
        step: '03',
        title: 'SEO 최적화',
        description: 'GPT-4o가 제목, 설명, 태그를 YouTube 알고리즘에 최적화합니다.',
        icon: (
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
            </svg>
        ),
    },
    {
        step: '04',
        title: '미디어 생성',
        description: 'TTS 음성과 AI 이미지를 자동으로 생성하여 영상 소재를 준비합니다.',
        icon: (
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0022.5 18.75V5.25A2.25 2.25 0 0020.25 3H3.75A2.25 2.25 0 001.5 5.25v13.5A2.25 2.25 0 003.75 21z" />
            </svg>
        ),
    },
    {
        step: '05',
        title: '영상 편집',
        description: 'FFmpeg 기반 자동 편집으로 음성, 이미지, 자막을 하나의 영상으로 합성합니다.',
        icon: (
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
            </svg>
        ),
    },
    {
        step: '06',
        title: 'YouTube 업로드',
        description: '완성된 영상을 YouTube에 자동으로 업로드하고 메타데이터를 설정합니다.',
        icon: (
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
        ),
    },
];

const howItWorks = [
    {
        title: '1. 채널 설정',
        description: '브랜드 정보와 타겟 시청자를 입력하세요.',
    },
    {
        title: '2. 주제 입력',
        description: '영상 주제를 입력하면 AI가 나머지를 처리합니다.',
    },
    {
        title: '3. 자동 생성',
        description: '6단계 AI 파이프라인이 콘텐츠를 자동으로 생성합니다.',
    },
    {
        title: '4. 검토 & 업로드',
        description: '결과를 검토하고 한 번의 클릭으로 업로드하세요.',
    },
];

export default function LandingPage() {
    return (
        <div>
            {/* Hero Section */}
            <section className="relative overflow-hidden py-24 md:py-32">
                {/* 멀티레이어 글로우 배경 */}
                <div className="absolute inset-0 -z-10">
                    <div className="absolute left-1/2 top-0 -translate-x-1/2 h-[600px] w-[900px] rounded-full bg-primary/15 blur-3xl" />
                    <div className="absolute left-0 top-1/4 h-[400px] w-[500px] rounded-full bg-secondary/10 blur-3xl" />
                    <div className="absolute inset-0 bg-[linear-gradient(to_right,hsl(var(--border)/0.3)_1px,transparent_1px),linear-gradient(to_bottom,hsl(var(--border)/0.3)_1px,transparent_1px)] bg-[size:60px_60px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />
                </div>
                <div className="mx-auto max-w-4xl px-6 text-center">
                    <Badge variant="secondary" className="mb-6 border-primary/30 gap-1.5">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
                        </span>
                        6단계 AI 파이프라인
                    </Badge>
                    <h1 className="mb-6 text-4xl font-bold tracking-tight md:text-6xl">
                        AI로 YouTube 콘텐츠를
                        <br />
                        <span className="text-gradient-brand">자동으로 생성</span>하세요
                    </h1>
                    <p className="mx-auto mb-10 max-w-2xl text-lg text-muted-foreground">
                        브랜드 리서치부터 원고 작성, SEO 최적화, 영상 편집, 업로드까지.
                        AI 에이전트가 YouTube 콘텐츠 제작의 전 과정을 자동화합니다.
                    </p>
                    <div className="flex items-center justify-center gap-4 flex-wrap">
                        <Button asChild size="lg" className="glow-red hover:scale-105 transition-transform">
                            <Link href="/login">무료로 시작하기</Link>
                        </Button>
                        <Button asChild variant="outline" size="lg" className="hover:border-primary/50 transition-colors">
                            <Link href="/pricing">요금제 보기</Link>
                        </Button>
                    </div>
                    <p className="mt-4 text-xs text-muted-foreground">신용카드 불필요 · 매월 3개 영상 무료</p>
                </div>
            </section>

            {/* Pipeline Steps Section */}
            <section className="border-t border-border/50 bg-muted/30 py-20">
                <div className="mx-auto max-w-6xl px-6">
                    <div className="mb-12 text-center">
                        <h2 className="mb-3 text-3xl font-bold tracking-tight">
                            6단계 자동화 파이프라인
                        </h2>
                        <p className="text-muted-foreground">
                            각 단계를 전문 AI 에이전트가 처리합니다
                        </p>
                    </div>
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                        {pipelineSteps.map((item) => (
                            <Card key={item.step} className="group relative overflow-hidden transition-all hover:border-primary/40 hover:shadow-lg hover:shadow-primary/10 hover:-translate-y-1 glass-card">
                                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                                <CardHeader>
                                    <div className="mb-2 flex items-center gap-3">
                                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:bg-primary/20 transition-colors">
                                            {item.icon}
                                        </div>
                                        <span className="text-xs font-bold text-muted-foreground">
                                            STEP {item.step}
                                        </span>
                                    </div>
                                    <CardTitle className="text-lg">{item.title}</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-muted-foreground">
                                        {item.description}
                                    </p>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            </section>

            {/* How It Works Section */}
            <section className="py-20">
                <div className="mx-auto max-w-4xl px-6">
                    <div className="mb-12 text-center">
                        <h2 className="mb-3 text-3xl font-bold tracking-tight">
                            사용 방법
                        </h2>
                        <p className="text-muted-foreground">
                            간단한 4단계로 YouTube 콘텐츠를 자동화하세요
                        </p>
                    </div>
                    <div className="grid gap-8 md:grid-cols-2">
                        {howItWorks.map((item) => (
                            <div
                                key={item.title}
                                className="flex gap-4 rounded-xl p-6 glass-card glass-card-hover"
                            >
                                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground">
                                    {item.title.charAt(0)}
                                </div>
                                <div>
                                    <h3 className="mb-1 font-semibold">{item.title}</h3>
                                    <p className="text-sm text-muted-foreground">
                                        {item.description}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="border-t border-border/50 bg-muted/30 py-20">
                <div className="mx-auto max-w-2xl px-6 text-center">
                    <h2 className="mb-4 text-3xl font-bold tracking-tight">
                        지금 바로 시작하세요
                    </h2>
                    <p className="mb-8 text-muted-foreground">
                        무료 플랜으로 매월 3개의 영상을 자동으로 생성할 수 있습니다.
                        신용카드 없이 바로 시작하세요.
                    </p>
                    <Button asChild size="lg">
                        <Link href="/login">무료로 시작하기</Link>
                    </Button>
                </div>
            </section>
        </div>
    );
}
