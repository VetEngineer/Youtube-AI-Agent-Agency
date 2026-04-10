'use client';

import { Suspense, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { signIn } from 'next-auth/react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const AUTH_ERROR_MESSAGES: Record<string, string> = {
    Configuration: '서버 설정 오류입니다. 관리자에게 문의하세요.',
    AccessDenied: '접근이 거부되었습니다.',
    Verification: '인증 링크가 만료되었습니다.',
    OAuthSignin: '카카오 로그인 요청 중 오류가 발생했습니다.',
    OAuthCallback: '카카오 로그인 응답 처리 중 오류가 발생했습니다. Redirect URI 설정을 확인하세요.',
    OAuthCreateAccount: '계정 생성 중 오류가 발생했습니다.',
    EmailCreateAccount: '이메일 계정 생성 중 오류가 발생했습니다.',
    Callback: '로그인 콜백 처리 중 오류가 발생했습니다.',
    Default: '로그인 중 오류가 발생했습니다. 다시 시도해주세요.',
};

function AuthErrorBanner() {
    const searchParams = useSearchParams();
    const authError = searchParams.get('error');
    if (!authError) return null;
    return (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-xs text-destructive">
            {AUTH_ERROR_MESSAGES[authError] ?? AUTH_ERROR_MESSAGES.Default}
            {process.env.NODE_ENV === 'development' && (
                <span className="ml-1 font-mono opacity-70">[{authError}]</span>
            )}
        </div>
    );
}

export default function LoginPage() {
    const [bypassOpen, setBypassOpen] = useState(false);
    const [email, setEmail] = useState('');
    const [token, setToken] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleKakaoLogin = () => {
        signIn('kakao', { callbackUrl: '/' });
    };

    const handleBypassLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        const result = await signIn('bypass', {
            email,
            token,
            callbackUrl: '/',
            redirect: false,
        });

        setLoading(false);

        if (result?.error) {
            setError('접근 코드가 올바르지 않습니다.');
        } else if (result?.url) {
            window.location.href = result.url;
        }
    };

    return (
        <div className="flex min-h-dvh items-center justify-center bg-background px-4">
            <div className="w-full max-w-md space-y-4">
                <Card>
                    <CardHeader className="text-center pb-4">
                        <div className="flex justify-center mb-3">
                            <div className="flex size-10 items-center justify-center rounded-xl bg-primary">
                                <svg className="h-5 w-5 text-primary-foreground" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M23 12l-10.5-9.5v5c-8 0-12.5 5-12.5 13 2-5 6-7.5 12.5-7.5v5L23 12z" />
                                </svg>
                            </div>
                        </div>
                        <CardTitle className="text-2xl font-bold">YouTube AI Agent Agency</CardTitle>
                        <CardDescription>
                            AI 기반 YouTube 콘텐츠 자동화 플랫폼
                        </CardDescription>
                    </CardHeader>

                    <CardContent className="space-y-3">
                        {/* OAuth 에러 표시 */}
                        <Suspense>
                            <AuthErrorBanner />
                        </Suspense>

                        {/* 카카오 로그인 */}
                        <Button
                            className="w-full font-semibold"
                            style={{ backgroundColor: '#FEE500', color: '#000000' }}
                            onClick={handleKakaoLogin}
                        >
                            <KakaoIcon className="mr-2 h-5 w-5" />
                            카카오로 시작하기
                        </Button>

                        {/* 구분선 */}
                        <div className="relative">
                            <div className="absolute inset-0 flex items-center">
                                <span className="w-full border-t border-border/50" />
                            </div>
                            <div className="relative flex justify-center">
                                <button
                                    type="button"
                                    className="bg-background px-3 text-xs text-muted-foreground hover:text-foreground transition-colors"
                                    onClick={() => setBypassOpen(!bypassOpen)}
                                >
                                    {bypassOpen ? '▲ 접기' : '베타 접근 코드 보유 시'}
                                </button>
                            </div>
                        </div>

                        {/* 우회 로그인 (베타 테스터 / 디버깅용) */}
                        {bypassOpen && (
                            <form onSubmit={handleBypassLogin} className="space-y-3 pt-1">
                                <div className="space-y-1.5">
                                    <Label htmlFor="bypass-email" className="text-xs text-muted-foreground">
                                        이메일 (선택)
                                    </Label>
                                    <Input
                                        id="bypass-email"
                                        type="email"
                                        placeholder="beta@ytai.dev"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="h-9 text-sm"
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <Label htmlFor="bypass-token" className="text-xs text-muted-foreground">
                                        접근 코드 <span className="text-destructive">*</span>
                                    </Label>
                                    <Input
                                        id="bypass-token"
                                        type="password"
                                        placeholder="접근 코드 입력"
                                        value={token}
                                        onChange={(e) => setToken(e.target.value)}
                                        required
                                        className="h-9 text-sm"
                                    />
                                </div>
                                {error && (
                                    <p className="text-xs text-destructive">{error}</p>
                                )}
                                <Button
                                    type="submit"
                                    variant="outline"
                                    className="w-full h-9 text-sm"
                                    disabled={loading || !token}
                                >
                                    {loading ? '확인 중...' : '베타 접근'}
                                </Button>
                            </form>
                        )}
                    </CardContent>
                </Card>

                <p className="text-center text-xs text-muted-foreground">
                    로그인 시{' '}
                    <Link href="/terms" className="underline hover:text-foreground transition-colors">이용약관</Link> 및{' '}
                    <Link href="/privacy" className="underline hover:text-foreground transition-colors">개인정보처리방침</Link>에 동의합니다.
                </p>

                <div className="rounded-lg border border-border bg-muted/50 px-4 py-3 text-xs text-foreground/75 space-y-1.5">
                    <p className="font-semibold text-foreground/90">사업자 정보</p>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                        <span>상호: 하캄솔루션</span>
                        <span>대표자: 강은구</span>
                        <span>사업자등록번호: 435-17-01222</span>
                        <span>통신판매업: 2020-대전유성-1677</span>
                    </div>
                    <p>주소: 대전광역시 유성구 은구비남로33번길 13-8, 3층 3043호</p>
                    <p>
                        문의:{' '}
                        <a
                            href="https://pf.kakao.com/_GxmxcTG/chat"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="underline hover:text-foreground transition-colors"
                        >
                            카카오톡 채널
                        </a>
                    </p>
                </div>
            </div>
        </div>
    );
}

function KakaoIcon({ className }: { className?: string }) {
    return (
        <svg className={className} viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 3C6.477 3 2 6.582 2 11c0 2.818 1.683 5.299 4.228 6.89L5.14 21.5l4.08-2.676A12.15 12.15 0 0 0 12 19c5.523 0 10-3.582 10-8s-4.477-8-10-8z" />
        </svg>
    );
}
