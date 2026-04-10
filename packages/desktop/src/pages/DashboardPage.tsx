import { type JSX } from 'react'
import { useAuth } from '@/providers/AuthProvider'
import { Button } from '@/components/ui/button'

export default function DashboardPage(): JSX.Element {
  const { userInfo, clearApiKey } = useAuth()

  return (
    <div className="flex min-h-dvh items-center justify-center bg-background">
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-semibold text-foreground text-balance">
          YouTube AI Agent Agency
        </h1>
        {userInfo && (
          <p className="text-muted-foreground">
            {userInfo.email}
          </p>
        )}
        <p className="text-sm text-muted-foreground">
          M3: 컴포넌트 이식 예정
        </p>
        <Button variant="outline" size="sm" onClick={() => { void clearApiKey() }}>
          로그아웃
        </Button>
      </div>
    </div>
  )
}
