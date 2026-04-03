import { auth } from '@/lib/auth';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export default auth((req: NextRequest & { auth: unknown }) => {
    const isLoggedIn = !!req.auth;
    const { pathname } = req.nextUrl;

    // 공개 경로는 통과
    const publicPaths = ['/login', '/landing', '/pricing', '/api/auth', '/terms', '/privacy'];
    const isPublic = publicPaths.some((p) => pathname.startsWith(p));
    if (isPublic) return NextResponse.next();

    // 비로그인 → /login 리디렉션
    if (!isLoggedIn) {
        const loginUrl = new URL('/login', req.url);
        loginUrl.searchParams.set('callbackUrl', pathname);
        return NextResponse.redirect(loginUrl);
    }

    // 루트 → 대시보드 리디렉션
    if (pathname === '/') {
        return NextResponse.redirect(new URL('/pipelines', req.url));
    }

    return NextResponse.next();
});

export const config = {
    matcher: [
        '/((?!_next/static|_next/image|favicon.ico|fonts|images|kakao-logo\\.svg).*)',
    ],
};
