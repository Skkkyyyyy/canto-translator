export const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000'

/** When true, every call is served by src/api/mock.ts and nothing hits the network. */
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

export class ApiError extends Error {
    /** 0 means the request never reached the server. */
    readonly status: number

    constructor(message: string, status: number) {
        super(message)
        this.name = 'ApiError'
        this.status = status
    }

    /**
     * The endpoint isn't there yet (or the backend is down). Callers use this to
     * hide optional features instead of showing the user an error.
     */
    get isUnavailable() {
        return this.status === 0 || this.status === 404 || this.status === 501
    }
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    let response: Response
    try {
        response = await fetch(`${API_BASE}${path}`, {
            ...init,
            headers: {
                'Content-Type': 'application/json',
                ...init.headers,
            },
        })
    } catch (error) {
        throw new ApiError(error instanceof Error ? error.message : 'Network error', 0)
    }

    if (!response.ok) {
        throw new ApiError(`${init.method ?? 'GET'} ${path} failed`, response.status)
    }

    return response.json() as Promise<T>
}
