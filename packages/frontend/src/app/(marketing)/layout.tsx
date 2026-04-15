import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function MarketingLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex min-h-dvh flex-col bg-background">
            <header className="sticky top-0 z-50 border-b border-border/50 bg-background pt-[env(safe-area-inset-top)]">
                <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
                    <Link href="/landing" className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                            <svg
                                className="h-4 w-4 text-primary-foreground"
                                viewBox="0 0 24 24"
                                fill="currentColor"
                            >
                                <path d="M23 12l-10.5-9.5v5c-8 0-12.5 5-12.5 13 2-5 6-7.5 12.5-7.5v5L23 12z" />
                            </svg>
                        </div>
                        <span className="text-lg font-bold">YAA</span>
                    </Link>
                    <nav className="flex items-center gap-4">
                        <Link
                            href="/pricing"
                            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                        >
                            요금제
                        </Link>
                        <Link
                            href="/login"
                            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                        >
                            로그인
                        </Link>
                        <Button asChild size="sm">
                            <Link href="/login">무료로 시작하기</Link>
                        </Button>
                    </nav>
                </div>
            </header>

            <main className="flex-1">{children}</main>

            <footer className="border-t border-border/50 bg-background">
                <div className="mx-auto max-w-6xl px-6 py-12">
                    <div className="grid gap-8 md:grid-cols-3">
                        <div>
                            <div className="flex items-center gap-2 mb-3">
                                <div className="flex h-6 w-6 items-center justify-center rounded bg-primary">
                                    <svg
                                        className="h-3 w-3 text-primary-foreground"
                                        viewBox="0 0 24 24"
                                        fill="currentColor"
                                    >
                                        <path d="M23 12l-10.5-9.5v5c-8 0-12.5 5-12.5 13 2-5 6-7.5 12.5-7.5v5L23 12z" />
                                    </svg>
                                </div>
                                <span className="font-semibold">YouTube AI Agent Agency</span>
                            </div>
                            <p className="text-sm text-muted-foreground">
                                AI 기반 YouTube 콘텐츠 자동 생성 플랫폼
                            </p>
                        </div>
                        <div>
                            <h4 className="mb-3 text-sm font-semibold">제품</h4>
                            <ul className="space-y-2 text-sm text-muted-foreground">
                                <li>
                                    <Link href="/landing" className="hover:text-foreground transition-colors">
                                        기능 소개
                                    </Link>
                                </li>
                                <li>
                                    <Link href="/pricing" className="hover:text-foreground transition-colors">
                                        요금제
                                    </Link>
                                </li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="mb-3 text-sm font-semibold">지원 / 법률</h4>
                            <ul className="space-y-2 text-sm text-muted-foreground">
                                <li>
                                    <a
                                        href="https://github.com/VetEngineer/Youtube-AI-Agent-Agency"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="hover:text-foreground transition-colors"
                                    >
                                        GitHub
                                    </a>
                                </li>
                                <li>
                                    <Link href="/terms" className="hover:text-foreground transition-colors">
                                        이용약관
                                    </Link>
                                </li>
                                <li>
                                    <Link href="/privacy" className="hover:text-foreground transition-colors">
                                        개인정보처리방침
                                    </Link>
                                </li>
                            </ul>
                        </div>
                    </div>
                    <div className="mt-8 border-t border-border/50 pt-6">
                        <div className="mb-4 rounded-lg border border-border bg-muted/60 px-4 py-4 text-xs text-foreground/80">
                            <p className="mb-2 text-sm font-semibold text-foreground">사업자 정보</p>
                            <div className="grid gap-x-8 gap-y-1 sm:grid-cols-2">
                                <span>상호: 하캄솔루션</span>
                                <span>대표자: 강은구</span>
                                <span>사업자등록번호: 435-17-01222</span>
                                <span>개업일: 2020년 12월 21일</span>
                                <span>통신판매업 신고번호: 2020-대전유성-1677</span>
                                <span>
                                    문의:{' '}
                                    <a
                                        href="https://pf.kakao.com/_GxmxcTG/chat"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="underline hover:text-foreground transition-colors"
                                    >
                                        카카오톡 채널
                                    </a>
                                </span>
                                <span className="sm:col-span-2">
                                    사업장 소재지: 대전광역시 유성구 은구비남로33번길 13-8, 3층 3043호 (지족동, 양지빌딩)
                                </span>
                            </div>
                        </div>
                        <div className="text-center text-xs text-muted-foreground">
                            &copy; {new Date().getFullYear()} YouTube AI Agent Agency. MIT License.
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
}
