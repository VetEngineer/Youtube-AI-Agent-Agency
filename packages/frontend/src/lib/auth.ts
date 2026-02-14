import NextAuth from 'next-auth';
import Google from 'next-auth/providers/google';
import GitHub from 'next-auth/providers/github';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

export const { handlers, signIn, signOut, auth } = NextAuth({
    providers: [
        Google({
            clientId: process.env.GOOGLE_CLIENT_ID!,
            clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
        }),
        GitHub({
            clientId: process.env.GITHUB_CLIENT_ID!,
            clientSecret: process.env.GITHUB_CLIENT_SECRET!,
        }),
    ],
    pages: {
        signIn: '/login',
    },
    callbacks: {
        async signIn({ user, account }) {
            if (!user.email) return false;

            try {
                await fetch(`${API_BASE_URL}/users/oauth/callback`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        email: user.email,
                        name: user.name,
                        image: user.image,
                        provider: account?.provider || 'unknown',
                        provider_account_id: account?.providerAccountId,
                    }),
                });
            } catch {
                // 백엔드 연결 실패해도 로그인은 허용 (오프라인 개발)
            }

            return true;
        },
        async jwt({ token, user, account }) {
            if (user) {
                token.email = user.email;
                token.name = user.name;
                token.picture = user.image;
                token.provider = account?.provider;
            }
            return token;
        },
        async session({ session, token }) {
            if (session.user) {
                session.user.id = token.sub || '';
                session.user.email = token.email || '';
                session.user.name = token.name || '';
                session.user.image = token.picture as string | undefined;
            }
            return session;
        },
    },
    session: {
        strategy: 'jwt',
    },
    secret: process.env.NEXTAUTH_SECRET,
});
