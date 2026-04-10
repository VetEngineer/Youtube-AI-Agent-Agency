import { createContext, useContext, useEffect, useRef, useState, useCallback, type JSX } from 'react'
import * as tauriStore from '@/lib/tauri-store'
import {
  setInMemoryKey,
  clearInMemoryKey,
  register401Handler,
  unregister401Handler,
} from '@/lib/api'

interface UserInfo {
  id: string
  email: string
  name: string | null
}

interface AuthState {
  apiKey: string | null
  isAuthenticated: boolean
  isLoading: boolean
  userInfo: UserInfo | null
  // Loaded in the same init() waterfall so RootRedirect has a single source of truth
  hasOnboarded: boolean
}

interface AuthContextValue extends AuthState {
  setApiKey: (key: string, backendUrl?: string) => Promise<void>
  clearApiKey: () => Promise<void>
  backendUrl: string
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

interface MeResponse {
  id: string
  email: string
  name: string | null
}

function isSecureUrl(url: string): boolean {
  try {
    return new URL(url).protocol === 'https:'
  } catch {
    return false
  }
}

type FailReason = 'invalid' | 'network' | 'insecure' | 'server'
type ValidateResult =
  | { ok: true; user: UserInfo }
  | { ok: false; reason: FailReason }

async function validateKey(key: string, backendUrl: string): Promise<ValidateResult> {
  if (!isSecureUrl(backendUrl)) return { ok: false, reason: 'insecure' }
  if (!key.startsWith('yaa_') || key.length < 20) return { ok: false, reason: 'invalid' }
  const base = backendUrl.replace(/\/+$/, '')
  let response: Response
  try {
    response = await fetch(`${base}/users/me`, {
      headers: { 'Content-Type': 'application/json', 'X-API-Key': key },
    })
  } catch {
    return { ok: false, reason: 'network' }
  }
  if (response.status === 401 || response.status === 403) return { ok: false, reason: 'invalid' }
  if (!response.ok) return { ok: false, reason: 'server' }
  try {
    const data = await response.json() as MeResponse
    return { ok: true, user: { id: data.id, email: data.email, name: data.name } }
  } catch {
    return { ok: false, reason: 'server' }
  }
}

interface AuthProviderProps {
  children: React.ReactNode
}

export function AuthProvider({ children }: AuthProviderProps): JSX.Element {
  const [state, setState] = useState<AuthState>({
    apiKey: null,
    isAuthenticated: false,
    isLoading: true,
    userInfo: null,
    hasOnboarded: false,
  })
  const [backendUrl, setBackendUrl] = useState<string>(tauriStore.DEFAULT_BACKEND_URL)
  const _setApiKeyInFlight = useRef(false)
  const _authVersion = useRef(0)

  const clearApiKey = useCallback(async () => {
    _authVersion.current += 1
    await tauriStore.clearApiKey()
    await tauriStore.setBackendUrl(tauriStore.DEFAULT_BACKEND_URL)
    clearInMemoryKey()
    setBackendUrl(tauriStore.DEFAULT_BACKEND_URL)
    setState((prev) => ({
      ...prev,
      apiKey: null,
      isAuthenticated: false,
      isLoading: false,
      userInfo: null,
    }))
  }, [])

  const setApiKey = useCallback(async (key: string, url?: string) => {
    if (_setApiKeyInFlight.current) throw new Error('이미 처리 중입니다.')
    _setApiKeyInFlight.current = true
    const version = ++_authVersion.current
    try {
      const resolvedUrl = url ?? await tauriStore.getBackendUrl()
      const result = await validateKey(key, resolvedUrl)
      if (!result.ok) {
        const messages: Record<FailReason, string> = {
          insecure: 'HTTPS 연결만 지원합니다.',
          invalid: 'API Key가 유효하지 않습니다.',
          network: '서버에 연결할 수 없습니다. 네트워크를 확인하세요.',
          server: '서버 오류가 발생했습니다. 잠시 후 다시 시도하세요.',
        }
        throw new Error(messages[result.reason])
      }
      if (_authVersion.current !== version) return
      if (url) {
        await tauriStore.setBackendUrl(url)
        setBackendUrl(url)
      }
      await tauriStore.setApiKey(key)
      await tauriStore.setOnboarded()
      setInMemoryKey(key, resolvedUrl)
      setState((prev) => ({
        ...prev,
        apiKey: key,
        isAuthenticated: true,
        isLoading: false,
        userInfo: result.user,
        hasOnboarded: true,
      }))
    } finally {
      _setApiKeyInFlight.current = false
    }
  }, [])

  // Initialize on mount: single waterfall loads all store values
  useEffect(() => {
    let cancelled = false

    async function init() {
      try {
        const [storedKey, storedUrl, onboarded] = await Promise.all([
          tauriStore.getApiKey(),
          tauriStore.getBackendUrl(),
          tauriStore.hasOnboarded(),
        ])

        if (cancelled) return

        setBackendUrl(storedUrl)

        if (!storedKey) {
          setState({ apiKey: null, isAuthenticated: false, isLoading: false, userInfo: null, hasOnboarded: onboarded })
          return
        }

        const result = await validateKey(storedKey, storedUrl)
        if (cancelled) return

        if (result.ok) {
          setInMemoryKey(storedKey, storedUrl)
          setState({ apiKey: storedKey, isAuthenticated: true, isLoading: false, userInfo: result.user, hasOnboarded: onboarded })
        } else if (result.reason === 'invalid') {
          // Key expired/revoked — clear from store
          await tauriStore.clearApiKey()
          clearInMemoryKey()
          setState({ apiKey: null, isAuthenticated: false, isLoading: false, userInfo: null, hasOnboarded: onboarded })
        } else {
          // Network/server failure — keep stored key for retry on next launch
          setState({ apiKey: null, isAuthenticated: false, isLoading: false, userInfo: null, hasOnboarded: onboarded })
        }
      } catch {
        setState((prev) => ({ ...prev, isLoading: false }))
      }
    }

    void init()
    return () => { cancelled = true }
  }, [])

  const clearApiKeyRef = useRef(clearApiKey)
  clearApiKeyRef.current = clearApiKey

  useEffect(() => {
    register401Handler(() => { void clearApiKeyRef.current() })
    return () => unregister401Handler()
  }, [])

  return (
    <AuthContext.Provider value={{ ...state, setApiKey, clearApiKey, backendUrl }}>
      {children}
    </AuthContext.Provider>
  )
}
