import NextAuth from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import type { OAuthConfig, OAuthUserConfig } from 'next-auth/providers';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

// ============================================
// Kakao 커스텀 프로바이더
// ============================================

interface KakaoProfile {
    id: number;
    kakao_account?: {
        email?: string;
        profile?: {
            nickname?: string;
            profile_image_url?: string;
        };
    };
}

function KakaoProvider(options: OAuthUserConfig<KakaoProfile>): OAuthConfig<KakaoProfile> {
    return {
        id: 'kakao',
        name: 'Kakao',
        type: 'oauth',
        authorization: {
            url: 'https://kauth.kakao.com/oauth/authorize',
            params: { scope: 'profile_nickname account_email profile_image' },
        },
        token: 'https://kauth.kakao.com/oauth/token',
        userinfo: 'https://kapi.kakao.com/v2/user/me',
        profile(profile) {
            return {
                id: String(profile.id),
                name: profile.kakao_account?.profile?.nickname ?? null,
                email: profile.kakao_account?.email ?? null,
                image: profile.kakao_account?.profile?.profile_image_url ?? null,
            };
        },
        style: {
            logo: '/kakao-logo.svg',
            bg: '#FEE500',
            text: '#000000',
        },
        options,
    };
}

// ============================================
// NextAuth 설정
// ============================================

export const { handlers, signIn, signOut, auth } = NextAuth({
    providers: [
        KakaoProvider({
            clientId: process.env.KAKAO_CLIENT_ID!,
            clientSecret: process.env.KAKAO_CLIENT_SECRET!,
        }),

        // 베타 테스터 / 디버깅용 우회 로그인
        // BYPASS_LOGIN_SECRET 환경변수가 설정된 경우에만 활성화
        Credentials({
            id: 'bypass',
            name: '베타 접근',
            credentials: {
                email: { label: '이메일', type: 'email', placeholder: 'beta@ytai.dev' },
                token: { label: '접근 코드', type: 'password', placeholder: '베타 접근 코드 입력' },
            },
            authorize(credentials) {
                const bypassSecret = process.env.BYPASS_LOGIN_SECRET?.trim();
                if (!bypassSecret) return null;
                const inputToken = (credentials?.token as string | undefined)?.trim();
                if (!inputToken || inputToken !== bypassSecret) return null;

                const email = (credentials.email as string) || 'beta@ytai.dev';
                return {
                    id: `bypass-${email}`,
                    email,
                    name: `Beta[${email.split('@')[0]}]`,
                    image: null,
                };
            },
        }),
    ],

    pages: {
        signIn: '/login',
        error: '/login',
    },

    callbacks: {
        async signIn({ user, account }) {
            if (!user.email) return false;

            // 우회 로그인은 백엔드 연동 없이 허용
            if (account?.provider === 'bypass') return true;

            try {
                const headers: Record<string, string> = { 'Content-Type': 'application/json' };
                if (process.env.INTERNAL_API_SECRET) {
                    headers['X-Internal-Secret'] = process.env.INTERNAL_API_SECRET;
                }
                const res = await fetch(`${API_BASE_URL}/users/oauth/callback`, {
                    method: 'POST',
                    headers,
                    body: JSON.stringify({
                        email: user.email,
                        name: user.name,
                        image: user.image,
                        provider: account?.provider || 'unknown',
                        provider_account_id: account?.providerAccountId,
                    }),
                });
                if (res.ok) {
                    const data = await res.json();
                    (user as Record<string, unknown>).is_admin = data.is_admin ?? false;
                }
            } catch (err) {
                // 프로덕션에서 백엔드 연결 실패 시 경고 로그
                console.warn("Backend user sync failed:", err);
            }

            return true;
        },

        async jwt({ token, user, account }) {
            if (user) {
                token.email = user.email;
                token.name = user.name;
                token.picture = user.image;
                token.provider = account?.provider;
                token.isBypass = account?.provider === 'bypass';
                token.isAdmin = (user as Record<string, unknown>).is_admin ?? false;
            }
            return token;
        },

        async session({ session, token }) {
            if (session.user) {
                session.user.id = token.sub || '';
                session.user.email = token.email || '';
                session.user.name = token.name || '';
                session.user.image = token.picture as string | undefined;
                (session.user as Record<string, unknown>).isAdmin = token.isAdmin ?? false;
            }
            return session;
        },
    },

    session: {
        strategy: 'jwt',
    },

    secret: process.env.NEXTAUTH_SECRET,
});
