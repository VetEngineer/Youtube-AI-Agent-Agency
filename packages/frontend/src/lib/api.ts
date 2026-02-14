export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

export class ApiError extends Error {
    constructor(public status: number, message: string) {
        super(message);
        this.name = 'ApiError';
    }
}

async function getAuthToken(): Promise<string | null> {
    if (typeof window === 'undefined') return null;

    try {
        const res = await fetch('/api/auth/session');
        const session = await res.json();
        // NextAuth v5는 세션에 직접 접근. JWT를 백엔드에 전달하려면
        // 세션 쿠키를 사용하거나, 커스텀 토큰 엔드포인트 사용.
        // 여기서는 API 키 폴백도 지원.
        if (session?.user) {
            // NextAuth JWT를 직접 전달할 수 없으므로 세션 기반 프록시 사용
            // 또는 localStorage의 API 키 폴백
            const apiKey = localStorage.getItem('api_key');
            return apiKey;
        }
    } catch {
        // 세션 조회 실패 시 API 키 폴백
    }

    return localStorage.getItem('api_key');
}

async function fetchWithAuth<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const apiKey = typeof window !== 'undefined' ? localStorage.getItem('api_key') : null;

    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...((options.headers || {}) as Record<string, string>),
    };

    if (apiKey) {
        headers['X-API-Key'] = apiKey;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
    });

    if (!response.ok) {
        throw new ApiError(response.status, `API Error: ${response.statusText}`);
    }

    if (response.status === 204) {
        return {} as T;
    }

    return response.json();
}

export const api = {
    get: <T>(endpoint: string) => fetchWithAuth<T>(endpoint, { method: 'GET' }),
    post: <T>(endpoint: string, body: unknown) => fetchWithAuth<T>(endpoint, { method: 'POST', body: JSON.stringify(body) }),
    put: <T>(endpoint: string, body: unknown) => fetchWithAuth<T>(endpoint, { method: 'PUT', body: JSON.stringify(body) }),
    patch: <T>(endpoint: string, body: unknown) => fetchWithAuth<T>(endpoint, { method: 'PATCH', body: JSON.stringify(body) }),
    delete: <T>(endpoint: string) => fetchWithAuth<T>(endpoint, { method: 'DELETE' }),
};
