export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
export const API_KEY_STORAGE_KEY = 'api_key';

export class ApiError extends Error {
    constructor(public status: number, message: string) {
        super(message);
        this.name = 'ApiError';
    }
}

export function getStoredApiKey(): string | null {
    if (typeof window === 'undefined') return null;

    const sessionKey = window.sessionStorage.getItem(API_KEY_STORAGE_KEY);
    if (sessionKey) {
        return sessionKey;
    }

    const legacyKey = window.localStorage.getItem(API_KEY_STORAGE_KEY);
    if (legacyKey) {
        window.sessionStorage.setItem(API_KEY_STORAGE_KEY, legacyKey);
        window.localStorage.removeItem(API_KEY_STORAGE_KEY);
        return legacyKey;
    }

    return null;
}

export function setStoredApiKey(apiKey: string): void {
    if (typeof window === 'undefined') return;
    window.sessionStorage.setItem(API_KEY_STORAGE_KEY, apiKey);
    window.localStorage.removeItem(API_KEY_STORAGE_KEY);
}

export function clearStoredApiKey(): void {
    if (typeof window === 'undefined') return;
    window.sessionStorage.removeItem(API_KEY_STORAGE_KEY);
    window.localStorage.removeItem(API_KEY_STORAGE_KEY);
}

async function fetchWithAuth<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const apiKey = getStoredApiKey();

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
