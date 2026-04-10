import { useState, useRef, useEffect, type JSX } from 'react'
import { useNavigate } from 'react-router-dom'
import { open } from '@tauri-apps/plugin-dialog'
import { useAuth } from '@/providers/AuthProvider'
import { setOutputDir, DEFAULT_BACKEND_URL } from '@/lib/tauri-store'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

type Step = 1 | 2 | 3

export default function OnboardingPage(): JSX.Element {
  const { setApiKey, backendUrl: contextBackendUrl } = useAuth()
  const navigate = useNavigate()

  const [step, setStep] = useState<Step>(1)
  const [backendUrl, setBackendUrl] = useState(contextBackendUrl)
  const [apiKey, setApiKeyInput] = useState('')

  // Tauri store init 완료 후 저장된 URL 동기화
  useEffect(() => {
    setBackendUrl(contextBackendUrl)
  }, [contextBackendUrl])
  const [outputDir, setOutputDirState] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const apiKeyInputRef = useRef<HTMLInputElement>(null)
  const finishBtnRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (step === 2) apiKeyInputRef.current?.focus()
    if (step === 3) finishBtnRef.current?.focus()
  }, [step])

  const handleUrlNext = () => {
    const url = backendUrl.trim() || DEFAULT_BACKEND_URL
    try {
      if (new URL(url).protocol !== 'https:') {
        setError('HTTPS 연결만 지원합니다.')
        return
      }
    } catch {
      setError('올바른 URL 형식이 아닙니다.')
      return
    }
    setError(null)
    setBackendUrl(url)
    setStep(2)
  }

  const handleKeyValidate = async () => {
    setError(null)
    setLoading(true)
    try {
      await setApiKey(apiKey.trim(), backendUrl)
      setStep(3)
    } catch (err) {
      setError(err instanceof Error ? err.message : '연결에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const handlePickDir = async () => {
    try {
      const selected = await open({ directory: true, multiple: false, title: '출력 디렉토리 선택' })
      if (typeof selected === 'string') {
        setOutputDirState(selected)
      }
    } catch {
      setError('폴더 선택 대화상자를 열 수 없습니다.')
    }
  }

  const handleFinish = async () => {
    try {
      if (outputDir) {
        await setOutputDir(outputDir)
      }
    } catch {
      setError('출력 폴더 저장에 실패했습니다. 다시 시도해 주세요.')
      return
    }
    // setOnboarded() is called inside AuthProvider.setApiKey() — no need to repeat here
    navigate('/')
  }

  const isCustomUrl = backendUrl.trim() !== DEFAULT_BACKEND_URL

  return (
    <div className="flex min-h-dvh items-center justify-center bg-background px-4">
      <div className="w-full max-w-md space-y-6">
        <div role="group" aria-label={`설정 ${step}단계 / 3단계`} className="flex items-center justify-center gap-2">
          {([1, 2, 3] as Step[]).map((s) => (
            <div
              key={s}
              aria-hidden="true"
              className={`size-2 rounded-full transition-[width,background-color] duration-200 ${
                s === step ? 'bg-primary w-6' : s < step ? 'bg-primary/40' : 'bg-muted'
              }`}
            />
          ))}
        </div>

        {step === 1 && (
          <Card>
            <CardHeader>
              <CardTitle asChild className="text-xl text-balance"><h1>YouTube AI Agent Agency에 오신 걸 환영합니다</h1></CardTitle>
              <CardDescription className="text-pretty">데스크톱 앱을 처음 설정합니다. 1분이면 완료됩니다.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="backend-url">백엔드 서버 URL</Label>
                <Input
                  id="backend-url"
                  type="url"
                  value={backendUrl}
                  onChange={(e) => setBackendUrl(e.target.value)}
                  placeholder={DEFAULT_BACKEND_URL}
                />
                {isCustomUrl && (
                  <p className="text-xs text-amber-700 dark:text-amber-300">
                    기본 서버와 다른 주소입니다.
                  </p>
                )}
                <p className="text-xs text-muted-foreground">
                  기본값을 사용하려면 그대로 두세요.
                </p>
              </div>
              {error && step === 1 && (
                <p role="alert" className="text-sm text-destructive rounded-md bg-destructive/10 px-3 py-2">
                  {error}
                </p>
              )}

              <Button className="w-full" onClick={handleUrlNext}>
                다음
              </Button>
            </CardContent>
          </Card>
        )}

        {step === 2 && (
          <Card>
            <CardHeader>
              <CardTitle asChild className="text-xl text-balance"><h1>API Key 입력</h1></CardTitle>
              <CardDescription className="text-pretty">
                웹앱 <span className="font-medium text-foreground">Settings › API Keys</span>에서
                발급한 키를 입력하세요. 키는 <span className="font-medium">admin</span> 스코프가
                필요합니다.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="api-key">API Key</Label>
                <Input
                  ref={apiKeyInputRef}
                  id="api-key"
                  type="password"
                  placeholder="yaa_xxxxxxxxxxxxxxxx"
                  value={apiKey}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  required
                />
              </div>

              {error && (
                <p role="alert" className="text-sm text-destructive rounded-md bg-destructive/10 px-3 py-2">
                  {error}
                </p>
              )}

              <div className="flex gap-2">
                <Button variant="outline" className="flex-1" onClick={() => { setError(null); setStep(1) }} disabled={loading}>
                  이전
                </Button>
                <Button
                  className="flex-1"
                  onClick={() => { void handleKeyValidate() }}
                  disabled={loading || !apiKey.trim()}
                  aria-busy={loading}
                >
                  {loading ? '검증 중...' : '연결 확인'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {step === 3 && (
          <Card>
            <CardHeader>
              <CardTitle asChild className="text-xl text-balance"><h1>출력 디렉토리 설정</h1></CardTitle>
              <CardDescription className="text-pretty">
                생성된 영상과 파일이 저장될 폴더를 선택하세요. 나중에 변경 가능합니다.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="output-dir">출력 폴더</Label>
                <div className="flex gap-2">
                  <Input
                    id="output-dir"
                    readOnly
                    value={outputDir}
                    placeholder="폴더를 선택하세요 (선택사항)"
                    className="flex-1"
                  />
                  <Button variant="outline" onClick={() => { void handlePickDir() }}>
                    찾아보기
                  </Button>
                </div>
              </div>

              {error && (
                <p role="alert" className="text-sm text-destructive rounded-md bg-destructive/10 px-3 py-2">
                  {error}
                </p>
              )}

              <Button ref={finishBtnRef} className="w-full" onClick={() => { void handleFinish() }}>
                시작하기
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
