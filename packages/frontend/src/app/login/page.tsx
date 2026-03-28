'use client';

import { useState } from 'react';
import { signIn } from 'next-auth/react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

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
        <div className="flex min-h-screen items-center justify-center bg-background px-4">
            <div className="w-full max-w-md space-y-4">
                <Card>
                    <CardHeader className="text-center pb-4">
                        <div className="flex justify-center mb-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary">
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
                    <span className="underline">이용약관</span> 및{' '}
                    <span className="underline">개인정보처리방침</span>에 동의합니다.
                </p>
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
