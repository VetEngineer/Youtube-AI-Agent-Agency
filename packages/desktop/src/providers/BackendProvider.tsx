import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type JSX,
} from 'react'
import { invoke } from '@tauri-apps/api/core'
import * as tauriStore from '@/lib/tauri-store'

// ─── Types ────────────────────────────────────────────────────────────────────

export type BackendMode = 'remote' | 'local'

export interface BackendContextValue {
  mode: BackendMode
  localPort: number
  isLoading: boolean
  dockerAvailable: boolean
  switchToRemote: () => Promise<void>
  switchToLocal: () => Promise<void>
  localBackendUrl: string
}

// ─── Constants ────────────────────────────────────────────────────────────────

const DEFAULT_LOCAL_PORT = 8000

function buildLocalUrl(port: number): string {
  return `http://localhost:${port}/api/v1`
}

// ─── Context ──────────────────────────────────────────────────────────────────

const BackendContext = createContext<BackendContextValue | null>(null)

export function useBackend(): BackendContextValue {
  const ctx = useContext(BackendContext)
  if (!ctx) throw new Error('useBackend must be used within BackendProvider')
  return ctx
}

// ─── Provider ─────────────────────────────────────────────────────────────────

interface BackendProviderProps {
  children: React.ReactNode
  /** 기본 원격 백엔드 URL */
  remoteBackendUrl: string
  /** api.ts 인메모리 URL 주입 함수 */
  onUrlChange: (url: string) => void
}

export function BackendProvider({
  children,
  remoteBackendUrl,
  onUrlChange,
}: BackendProviderProps): JSX.Element {
  const [mode, setMode] = useState<BackendMode>('remote')
  const [localPort, setLocalPort] = useState<number>(DEFAULT_LOCAL_PORT)
  const [isLoading, setIsLoading] = useState(true)
  const [dockerAvailable, setDockerAvailable] = useState(false)
  const isMountedRef = useRef(false)

  const localBackendUrl = buildLocalUrl(localPort)

  // Use a ref so the init effect's closure always calls the latest onUrlChange without
  // making onUrlChange a dependency that triggers reinit on every render.
  const onUrlChangeRef = useRef(onUrlChange)
  onUrlChangeRef.current = onUrlChange

  useEffect(() => {
    isMountedRef.current = true

    async function init() {
      try {
        const [storedMode, storedPort, dockerOk] = await Promise.all([
          tauriStore.getBackendMode(),
          tauriStore.getLocalBackendPort(),
          invoke<boolean>('check_docker_available'),
        ])
        if (!isMountedRef.current) return
        // Fall back to remote if stored mode is local but Docker is unavailable
        const effectiveMode = storedMode === 'local' && !dockerOk ? 'remote' : storedMode
        setMode(effectiveMode)
        setLocalPort(storedPort)
        setDockerAvailable(dockerOk)
        // URL 전파 없음 — AuthProvider가 init에서 이미 storedUrl로 setInMemoryKey를 설정함.
        // 명시적 스위치(switchToLocal/switchToRemote)에서만 onUrlChange 호출.
      } catch {
        // store 실패 시 기본값(remote) 유지
      } finally {
        if (isMountedRef.current) setIsLoading(false)
      }
    }

    void init()
    return () => {
      isMountedRef.current = false
    }
  }, []) // runs once at mount — onUrlChangeRef keeps the callback current

  const switchToRemote = useCallback(async () => {
    await tauriStore.setBackendMode('remote')
    setMode('remote')
    onUrlChange(remoteBackendUrl)
  }, [remoteBackendUrl, onUrlChange])

  const switchToLocal = useCallback(async () => {
    await tauriStore.setBackendMode('local')
    setMode('local')
    onUrlChange(buildLocalUrl(localPort))
  }, [localPort, onUrlChange])

  return (
    <BackendContext.Provider
      value={{
        mode,
        localPort,
        isLoading,
        dockerAvailable,
        switchToRemote,
        switchToLocal,
        localBackendUrl,
      }}
    >
      {children}
    </BackendContext.Provider>
  )
}
