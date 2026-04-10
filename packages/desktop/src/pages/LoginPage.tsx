import { useState, useEffect, type JSX } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/providers/AuthProvider'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { DEFAULT_BACKEND_URL } from '@/lib/tauri-store'

export default function LoginPage(): JSX.Element {
  const { setApiKey, backendUrl } = useAuth()
  const navigate = useNavigate()

  const [apiKey, setApiKeyInput] = useState('')
  const [customUrl, setCustomUrl] = useState(backendUrl)
  useEffect(() => { setCustomUrl(backendUrl) }, [backendUrl])
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isCustomUrl = customUrl.trim() !== DEFAULT_BACKEND_URL

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const url = customUrl.trim() || DEFAULT_BACKEND_URL
      await setApiKey(apiKey.trim(), url)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : '연결에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-dvh items-center justify-center bg-background px-4">
      <div className="w-full max-w-md space-y-4">
        <Card>
          <CardHeader className="text-center pb-2">
            <div className="flex justify-center mb-3">
              <div className="flex size-10 items-center justify-center rounded-xl bg-primary">
                <svg className="size-5 text-primary-foreground" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path d="M23 12l-10.5-9.5v5c-8 0-12.5 5-12.5 13 2-5 6-7.5 12.5-7.5v5L23 12z" />
                </svg>
              </div>
            </div>
            <CardTitle asChild className="text-2xl font-semibold text-balance"><h1>YouTube AI Agent Agency</h1></CardTitle>
            <CardDescription className="text-pretty">API Key로 로그인</CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={(e) => { void handleSubmit(e) }} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="api-key">API Key</Label>
                <Input
                  id="api-key"
                  type="password"
                  placeholder="yaa_xxxxxxxxxxxxxxxx"
                  value={apiKey}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  required
                  autoFocus
                />
                <p className="text-xs text-muted-foreground">
                  웹앱{' '}
                  <span className="font-medium text-foreground">Settings › API Keys</span>
                  에서 발급받은 키를 입력하세요.
                </p>
              </div>

              {error && (
                <p role="alert" className="text-sm text-destructive rounded-md bg-destructive/10 px-3 py-2">
                  {error}
                </p>
              )}

              <Button type="submit" className="w-full" disabled={loading || !apiKey.trim()} aria-busy={loading}>
                {loading ? '연결 중...' : '로그인'}
              </Button>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-border/50" />
                </div>
                <div className="relative flex justify-center">
                  <button
                    type="button"
                    className="bg-background px-3 text-xs text-muted-foreground hover:text-foreground transition-colors"
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    aria-expanded={showAdvanced}
                    aria-controls="advanced-settings"
                  >
                    {showAdvanced ? '▲ 고급 설정 접기' : '▼ 고급 설정'}
                  </button>
                </div>
              </div>

              <div id="advanced-settings" className="space-y-1.5" hidden={!showAdvanced}>
                <Label htmlFor="backend-url">백엔드 URL</Label>
                <Input
                  id="backend-url"
                  type="url"
                  value={customUrl}
                  onChange={(e) => setCustomUrl(e.target.value)}
                  placeholder={DEFAULT_BACKEND_URL}
                />
                {isCustomUrl && (
                  <p className="text-xs text-amber-700 dark:text-amber-300">
                    기본 서버와 다른 주소입니다. 올바른지 확인하세요.
                  </p>
                )}
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
