import { Component, useEffect, useMemo, type JSX, type ReactNode, type ErrorInfo } from 'react'
import { createMemoryRouter, RouterProvider, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from '@/providers/AuthProvider'
import { Button } from '@/components/ui/button'
import AppLayout from '@/components/AppLayout'
import LoginPage from '@/pages/LoginPage'
import OnboardingPage from '@/pages/OnboardingPage'
import DashboardPage from '@/pages/DashboardPage'
import PipelinesPage from '@/pages/PipelinesPage'
import PipelineNewPage from '@/pages/PipelineNewPage'
import PipelineDetailPage from '@/pages/PipelineDetailPage'
import ChannelsPage from '@/pages/ChannelsPage'
import CompetitorsPage from '@/pages/CompetitorsPage'
import SettingsPage from '@/pages/SettingsPage'
import GuidePage from '@/pages/GuidePage'

// ─── Error boundary — prevents blank screen on render crash ─────────────────
interface ErrorBoundaryState { error: Error | null }

class ErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary] 렌더링 오류:', error, info)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-dvh items-center justify-center bg-background px-4">
          <div className="text-center space-y-4 max-w-md">
            <h1 className="text-xl font-semibold text-foreground text-balance">예기치 않은 오류가 발생했습니다</h1>
            <p className="text-sm text-muted-foreground text-pretty">{this.state.error.message}</p>
            <Button variant="outline" onClick={() => this.setState({ error: null })}>
              다시 시도
            </Button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

// ─── Auth-aware root redirect ─────────────────────────────────────────────────
// Reads all state from AuthProvider — single waterfall, no secondary store reads.
function RootRedirect(): JSX.Element {
  const { isAuthenticated, isLoading, hasOnboarded } = useAuth()

  if (isLoading) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-background">
        <div className="text-muted-foreground text-sm">로딩 중...</div>
      </div>
    )
  }

  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  if (!hasOnboarded) return <Navigate to="/onboarding" replace />
  return <Navigate to="/login" replace />
}

// ─── Protected route — blocks unauthenticated access ─────────────────────────
function RequireAuth({ children }: { children: JSX.Element }): JSX.Element {
  const { isAuthenticated, isLoading } = useAuth()
  if (isLoading) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-background">
        <div className="text-muted-foreground text-sm">로딩 중...</div>
      </div>
    )
  }
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

// ─── App ──────────────────────────────────────────────────────────────────────
// Router is created inside App so it is co-located with the component tree it serves.
function App(): JSX.Element {
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const apply = (dark: boolean) => {
      document.documentElement.classList.toggle('dark', dark)
    }
    const handler = (e: MediaQueryListEvent) => apply(e.matches)
    apply(mq.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  // useMemo ensures the router instance is stable across re-renders (e.g. dark-mode toggle).
  // A new router on every render would reset navigation state and history stack.
  const router = useMemo(() => createMemoryRouter([
    { path: '/', element: <RootRedirect /> },
    { path: '/onboarding', element: <OnboardingPage /> },
    { path: '/login', element: <LoginPage /> },
    {
      element: <RequireAuth><AppLayout /></RequireAuth>,
      children: [
        { path: '/dashboard', element: <DashboardPage /> },
        { path: '/pipelines', element: <PipelinesPage /> },
        { path: '/pipelines/new', element: <PipelineNewPage /> },
        { path: '/pipelines/:id', element: <PipelineDetailPage /> },
        { path: '/channels', element: <ChannelsPage /> },
        { path: '/competitors', element: <CompetitorsPage /> },
        { path: '/settings', element: <SettingsPage /> },
        { path: '/guide', element: <GuidePage /> },
      ],
    },
  ]), [])

  return (
    <AuthProvider>
      <ErrorBoundary>
        <RouterProvider router={router} />
      </ErrorBoundary>
    </AuthProvider>
  )
}

export default App
