import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const plans = [
    {
        name: 'Free',
        price: '0',
        period: '',
        description: '개인 크리에이터를 위한 무료 플랜',
        features: [
            '월 3회 파이프라인 실행',
            '채널 1개',
            '기본 AI 모델 (GPT-4o mini)',
            '720p 영상 출력',
            '커뮤니티 지원',
        ],
        notIncluded: [
            'SEO 최적화',
            '고급 TTS 음성',
            '팀 멤버 초대',
            'API 접근',
        ],
        cta: '무료로 시작하기',
        variant: 'outline' as const,
        highlighted: false,
    },
    {
        name: 'Pro',
        price: '29,000',
        period: '/월',
        description: '본격적인 YouTube 운영을 위한 프로 플랜',
        features: [
            '월 30회 파이프라인 실행',
            '채널 5개',
            '고급 AI 모델 (Claude + GPT-4o)',
            '1080p 영상 출력',
            'SEO 최적화',
            '고급 TTS 음성',
            '우선 지원',
            'API 접근',
        ],
        notIncluded: [
            '팀 멤버 초대',
        ],
        cta: 'Pro 시작하기',
        variant: 'default' as const,
        highlighted: true,
    },
    {
        name: 'Enterprise',
        price: '99,000',
        period: '/월',
        description: '팀과 에이전시를 위한 엔터프라이즈 플랜',
        features: [
            '무제한 파이프라인 실행',
            '무제한 채널',
            '최고급 AI 모델',
            '4K 영상 출력',
            'SEO 최적화',
            '고급 TTS 음성',
            '팀 멤버 10명',
            'API 접근 (높은 Rate Limit)',
            '전담 지원',
            '커스텀 브랜딩',
        ],
        notIncluded: [],
        cta: '문의하기',
        variant: 'outline' as const,
        highlighted: false,
    },
];

export default function PricingPage() {
    return (
        <div className="py-20">
            <div className="mx-auto max-w-6xl px-6">
                {/* Header */}
                <div className="mb-16 text-center">
                    <Badge variant="secondary" className="mb-4">
                        요금제
                    </Badge>
                    <h1 className="mb-4 text-4xl font-bold tracking-tight">
                        필요에 맞는 플랜을 선택하세요
                    </h1>
                    <p className="mx-auto max-w-xl text-lg text-muted-foreground">
                        무료 플랜으로 시작하고, 필요할 때 업그레이드하세요.
                        모든 플랜에 14일 무료 체험이 포함됩니다.
                    </p>
                </div>

                {/* Pricing Cards */}
                <div className="grid gap-8 md:grid-cols-3">
                    {plans.map((plan) => (
                        <Card
                            key={plan.name}
                            className={
                                plan.highlighted
                                    ? 'relative border-primary shadow-lg shadow-primary/10'
                                    : ''
                            }
                        >
                            {plan.highlighted && (
                                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                                    <Badge>인기</Badge>
                                </div>
                            )}
                            <CardHeader>
                                <CardTitle className="text-xl">{plan.name}</CardTitle>
                                <CardDescription>{plan.description}</CardDescription>
                                <div className="mt-4">
                                    <span className="text-4xl font-bold">
                                        {plan.price === '0' ? '무료' : `\u20A9${plan.price}`}
                                    </span>
                                    {plan.period && (
                                        <span className="text-muted-foreground">{plan.period}</span>
                                    )}
                                </div>
                            </CardHeader>
                            <CardContent>
                                <ul className="space-y-3">
                                    {plan.features.map((feature) => (
                                        <li key={feature} className="flex items-start gap-2 text-sm">
                                            <svg
                                                className="mt-0.5 h-4 w-4 shrink-0 text-primary"
                                                fill="none"
                                                viewBox="0 0 24 24"
                                                stroke="currentColor"
                                                strokeWidth={2}
                                            >
                                                <path
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                    d="M4.5 12.75l6 6 9-13.5"
                                                />
                                            </svg>
                                            {feature}
                                        </li>
                                    ))}
                                    {plan.notIncluded.map((feature) => (
                                        <li
                                            key={feature}
                                            className="flex items-start gap-2 text-sm text-muted-foreground/50"
                                        >
                                            <svg
                                                className="mt-0.5 h-4 w-4 shrink-0"
                                                fill="none"
                                                viewBox="0 0 24 24"
                                                stroke="currentColor"
                                                strokeWidth={2}
                                            >
                                                <path
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                    d="M6 18L18 6M6 6l12 12"
                                                />
                                            </svg>
                                            {feature}
                                        </li>
                                    ))}
                                </ul>
                            </CardContent>
                            <CardFooter>
                                <Button
                                    asChild
                                    variant={plan.variant}
                                    className="w-full"
                                >
                                    <Link href="/login">{plan.cta}</Link>
                                </Button>
                            </CardFooter>
                        </Card>
                    ))}
                </div>

                {/* Feature Comparison Table */}
                <div className="mt-20">
                    <h2 className="mb-8 text-center text-2xl font-bold tracking-tight">
                        상세 기능 비교
                    </h2>
                    <div className="overflow-x-auto rounded-xl border">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b bg-muted/50">
                                    <th className="px-6 py-4 text-left font-medium">기능</th>
                                    <th className="px-6 py-4 text-center font-medium">Free</th>
                                    <th className="px-6 py-4 text-center font-medium text-primary">Pro</th>
                                    <th className="px-6 py-4 text-center font-medium">Enterprise</th>
                                </tr>
                            </thead>
                            <tbody>
                                {[
                                    ['파이프라인 실행', '3회/월', '30회/월', '무제한'],
                                    ['채널 수', '1개', '5개', '무제한'],
                                    ['AI 모델', 'GPT-4o mini', 'Claude + GPT-4o', '최고급'],
                                    ['영상 해상도', '720p', '1080p', '4K'],
                                    ['SEO 최적화', '-', 'O', 'O'],
                                    ['고급 TTS', '-', 'O', 'O'],
                                    ['팀 멤버', '-', '-', '10명'],
                                    ['API 접근', '-', 'O', 'O (높은 Rate Limit)'],
                                    ['지원', '커뮤니티', '우선', '전담'],
                                ].map(([feature, free, pro, enterprise]) => (
                                    <tr key={feature} className="border-b last:border-0">
                                        <td className="px-6 py-3 font-medium">{feature}</td>
                                        <td className="px-6 py-3 text-center text-muted-foreground">{free}</td>
                                        <td className="px-6 py-3 text-center">{pro}</td>
                                        <td className="px-6 py-3 text-center text-muted-foreground">{enterprise}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
