import { auth } from '@/lib/auth';
import { NextResponse } from 'next/server';

// 로그인 없이 접근 가능한 공개 경로
const PUBLIC_PATHS = ['/login', '/api/auth', '/terms', '/privacy', '/landing', '/pricing'];

export default auth((req) => {
    const { nextUrl } = req;
    const session = req.auth;
    const pathname = nextUrl.pathname;

    const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));
    if (isPublic) return NextResponse.next();

    if (!session) {
        const loginUrl = new URL('/login', nextUrl);
        loginUrl.searchParams.set('callbackUrl', pathname);
        return NextResponse.redirect(loginUrl);
    }

    return NextResponse.next();
});

export const config = {
    matcher: [
        '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
    ],
};
