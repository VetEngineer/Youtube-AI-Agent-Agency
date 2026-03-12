export { auth as proxy } from '@/lib/auth';

export const config = {
    matcher: [
        /*
         * 다음을 제외한 모든 경로에 인증 미들웨어 적용:
         * - /login (로그인 페이지)
         * - /landing (랜딩 페이지)
         * - /pricing (요금제 페이지)
         * - /api/auth (NextAuth API)
         * - /_next (Next.js 내부)
         * - /favicon.ico, /fonts, /images 등 정적 파일
         */
        '/((?!login|landing|pricing|api/auth|_next/static|_next/image|favicon.ico|fonts|images).*)',
    ],
};
