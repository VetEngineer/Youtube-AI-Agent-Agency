export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

export class ApiError extends Error {
    constructor(public status: number, message: string) {
        super(message);
        this.name = 'ApiError';
    }
}

async function fetchWithAuth<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    // Client-side only
    const apiKey = typeof window !== 'undefined' ? localStorage.getItem('api_key') : null;

    const headers = {
        'Content-Type': 'application/json',
        ...(apiKey ? { 'X-API-Key': apiKey } : {}),
        ...options.headers,
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
    });

    if (!response.ok) {
        throw new ApiError(response.status, `API Error: ${response.statusText}`);
    }

    // Handle empty responses
    if (response.status === 204) {
        return {} as T;
    }

    return response.json();
}

export const api = {
    get: <T>(endpoint: string) => fetchWithAuth<T>(endpoint, { method: 'GET' }),
    post: <T>(endpoint: string, body: any) => fetchWithAuth<T>(endpoint, { method: 'POST', body: JSON.stringify(body) }),
    put: <T>(endpoint: string, body: any) => fetchWithAuth<T>(endpoint, { method: 'PUT', body: JSON.stringify(body) }),
    patch: <T>(endpoint: string, body: any) => fetchWithAuth<T>(endpoint, { method: 'PATCH', body: JSON.stringify(body) }),
    delete: <T>(endpoint: string) => fetchWithAuth<T>(endpoint, { method: 'DELETE' }),
};
