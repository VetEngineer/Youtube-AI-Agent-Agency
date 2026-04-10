import { useCallback, useEffect, useRef, useState, type JSX } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { AlertCircle, CheckCircle2, Circle, Cloud, Loader2, Server } from 'lucide-react'
import { useBackend } from '@/providers/BackendProvider'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

// ─── Types ────────────────────────────────────────────────────────────────────

type DockerStatus = 'running' | 'starting' | 'stopped' | 'error'

interface StatusResponse {
  status: DockerStatus
  message: string
}

// ─── Status Indicator ─────────────────────────────────────────────────────────

function StatusIndicator({ status }: { status: DockerStatus }): JSX.Element {
  const config = {
    running: { icon: CheckCircle2, label: '실행 중', className: 'text-green-500' },
    starting: { icon: Loader2, label: '시작 중', className: 'text-amber-500 animate-spin' },
    stopped: { icon: Circle, label: '중지됨', className: 'text-muted-foreground' },
    error: { icon: AlertCircle, label: '오류', className: 'text-destructive' },
  } as const

  const { icon: Icon, label, className } = config[status]
  return (
    <span className={`flex items-center gap-1.5 text-sm ${className}`}>
      <Icon className="size-4" />
      {label}
    </span>
  )
}

// ─── BackendSection ───────────────────────────────────────────────────────────

export function BackendSection(): JSX.Element {
  const { mode, dockerAvailable, switchToRemote, switchToLocal, localBackendUrl, localPort } =
    useBackend()
  const [dockerStatus, setDockerStatus] = useState<DockerStatus>('stopped')
  const [statusMessage, setStatusMessage] = useState('')
  const [isActing, setIsActing] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const isMountedRef = useRef(false)

  const refreshStatus = useCallback(async () => {
    if (!dockerAvailable) return
    try {
      const res = await invoke<StatusResponse>('get_local_backend_status')
      if (!isMountedRef.current) return
      setDockerStatus(res.status)
      setStatusMessage(res.message)
    } catch {
      if (!isMountedRef.current) return
      setDockerStatus('error')
      setStatusMessage('상태 확인 실패')
    }
  }, [dockerAvailable])

  useEffect(() => {
    if (mode !== 'local') return

    isMountedRef.current = true
    let cancelled = false

    void refreshStatus()
    const timer = setInterval(() => {
      if (!cancelled) void refreshStatus()
    }, 5000)

    return () => {
      cancelled = true
      isMountedRef.current = false
      clearInterval(timer)
    }
  }, [mode, refreshStatus])

  const handleStart = async () => {
    setIsActing(true)
    setActionError(null)
    try {
      await invoke('start_local_backend')
      setDockerStatus('starting')
      setTimeout(() => {
        void refreshStatus()
      }, 3000)
    } catch (err) {
      setActionError(typeof err === 'string' ? err : String(err))
    } finally {
      setIsActing(false)
    }
  }

  const handleStop = async () => {
    setIsActing(true)
    setActionError(null)
    try {
      await invoke('stop_local_backend')
      setDockerStatus('stopped')
    } catch (err) {
      setActionError(typeof err === 'string' ? err : String(err))
    } finally {
      setIsActing(false)
    }
  }

  const handleSwitchToLocal = async () => {
    await switchToLocal()
    void refreshStatus()
  }

  const localDisplayPort = localBackendUrl.split(':')[2]?.split('/')[0] ?? String(localPort)

  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-sm font-medium text-balance">백엔드 연결</h4>
        <p className="text-sm text-muted-foreground text-pretty">
          Railway 원격 서버 또는 로컬 Docker 컨테이너 중 하나를 사용합니다.
        </p>
      </div>

      {/* 모드 선택 카드 */}
      <div className="grid grid-cols-2 gap-3" role="radiogroup" aria-label="백엔드 모드 선택">
        <button
          type="button"
          role="radio"
          aria-checked={mode === 'remote'}
          onClick={() => {
            void switchToRemote()
          }}
          className={`flex flex-col gap-2 rounded-lg border p-4 text-left transition-colors ${
            mode === 'remote'
              ? 'border-primary bg-primary/5'
              : 'border-border hover:border-muted-foreground/50'
          }`}
        >
          <Cloud className="size-5 text-muted-foreground" />
          <div>
            <p className="text-sm font-medium">원격 서버</p>
            <p className="text-xs text-muted-foreground text-pretty">Railway 클라우드 백엔드 사용</p>
          </div>
          {mode === 'remote' && (
            <Badge variant="secondary" className="w-fit text-xs">
              현재
            </Badge>
          )}
        </button>

        <button
          type="button"
          role="radio"
          aria-checked={mode === 'local'}
          onClick={() => {
            void handleSwitchToLocal()
          }}
          disabled={!dockerAvailable}
          className={`flex flex-col gap-2 rounded-lg border p-4 text-left transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
            mode === 'local'
              ? 'border-primary bg-primary/5'
              : 'border-border hover:border-muted-foreground/50'
          }`}
        >
          <Server className="size-5 text-muted-foreground" />
          <div>
            <p className="text-sm font-medium">로컬 Docker</p>
            <p className="text-xs text-muted-foreground text-pretty">
              {dockerAvailable ? `localhost:${localDisplayPort}` : 'Docker 미설치'}
            </p>
          </div>
          {mode === 'local' && (
            <Badge variant="secondary" className="w-fit text-xs">
              현재
            </Badge>
          )}
        </button>
      </div>

      {/* 로컬 모드 사용 전 필수 안내 */}
      {mode === 'local' && (
        <div className="flex items-start gap-2 rounded-lg border border-amber-500/20 bg-amber-500/10 p-3">
          <AlertCircle className="mt-0.5 size-4 shrink-0 text-amber-500" />
          <div className="space-y-1">
            <p className="text-sm font-medium text-amber-700 dark:text-amber-300">초기 설정 필요 (기술 사용자 전용)</p>
            <p className="text-xs text-amber-600 dark:text-amber-400 text-pretty">
              로컬 Docker 백엔드는 최초 실행 시 빈 데이터베이스로 시작합니다.
              API 키 및 관리자 계정을 수동으로 생성해야 합니다: 컨테이너 내부에서{' '}
              <code className="font-mono">uv run python -m yaa_app.cli create-admin</code>를 실행하거나,
              원격 서버 API를 통해 초기 설정을 완료하세요.
              백엔드 전환 시 재로그인이 필요합니다.
            </p>
          </div>
        </div>
      )}

      {/* 로컬 모드 제어 패널 */}
      {mode === 'local' && (
        <div className="space-y-3 rounded-lg border bg-muted/30 p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">컨테이너 상태</span>
            <StatusIndicator status={dockerStatus} />
          </div>
          {statusMessage && <p className="text-xs text-muted-foreground">{statusMessage}</p>}
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                void handleStart()
              }}
              disabled={isActing || dockerStatus === 'running' || dockerStatus === 'starting'}
            >
              {isActing && dockerStatus !== 'running' ? (
                <Loader2 className="mr-1.5 size-3.5 animate-spin" />
              ) : null}
              시작
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                void handleStop()
              }}
              disabled={isActing || dockerStatus === 'stopped'}
            >
              {isActing && dockerStatus === 'running' ? (
                <Loader2 className="mr-1.5 size-3.5 animate-spin" />
              ) : null}
              중지
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                void refreshStatus()
              }}
              aria-label="상태 새로고침"
            >
              새로고침
            </Button>
          </div>
          {actionError && (
            <p role="alert" className="rounded-md bg-destructive/10 px-2 py-1.5 text-xs text-destructive">
              {actionError}
            </p>
          )}
        </div>
      )}

      {!dockerAvailable && (
        <div className="flex items-start gap-2 rounded-lg border border-amber-500/20 bg-amber-500/10 p-3">
          <AlertCircle className="mt-0.5 size-4 shrink-0 text-amber-500" />
          <div className="space-y-1">
            <p className="text-sm font-medium text-amber-700 dark:text-amber-300">
              Docker가 설치되어 있지 않습니다
            </p>
            <p className="text-xs text-amber-600 dark:text-amber-400">
              로컬 백엔드를 사용하려면{' '}
              <a
                href="https://www.docker.com"
                target="_blank"
                rel="noreferrer"
                className="underline"
              >
                docker.com
              </a>
              에서 Docker Desktop을 설치하세요.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
