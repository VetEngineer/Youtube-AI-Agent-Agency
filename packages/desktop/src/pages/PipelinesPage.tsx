import { useState, type JSX } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Plus, XCircle, Inbox } from 'lucide-react'
import { usePipelineRuns } from '@/hooks/use-pipeline'
import { StatusBadge } from '@/components/pipeline/StatusBadge'

const STATUS_FILTERS = ['all', 'pending', 'running', 'completed', 'cancelled', 'failed'] as const
type StatusFilter = (typeof STATUS_FILTERS)[number]

function formatDuration(createdAt: string, completedAt: string | null): string {
  if (!completedAt) return '-'
  const ms = new Date(completedAt).getTime() - new Date(createdAt).getTime()
  const secs = Math.max(0, Math.floor(ms / 1000))
  const mins = Math.floor(secs / 60)
  const rem = secs % 60
  return mins > 0 ? `${mins}m ${rem}s` : `${secs}s`
}

export default function PipelinesPage(): JSX.Element {
  const [filter, setFilter] = useState<StatusFilter>('all')
  const { data, isLoading, error } = usePipelineRuns({ status: filter === 'all' ? undefined : filter })

  const runs = data?.runs ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-balance">Pipelines</h2>
          <p className="text-muted-foreground text-pretty">All pipeline executions.</p>
        </div>
        <Button asChild>
          <Link to="/pipelines/new">
            <Plus className="mr-2 h-4 w-4" /> New Pipeline
          </Link>
        </Button>
      </div>

      <div className="flex gap-2 flex-wrap">
        {STATUS_FILTERS.map((s) => (
          <Button
            key={s}
            variant={filter === s ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter(s)}
            className="capitalize"
          >
            {s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
          </Button>
        ))}
      </div>

      {isLoading && (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-14 w-full rounded-lg" />
          ))}
        </div>
      )}

      {error && (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <XCircle className="h-10 w-10 text-red-400 mb-3" />
          <p className="text-sm text-muted-foreground">파이프라인 목록을 불러오지 못했습니다.</p>
        </div>
      )}

      {!isLoading && !error && runs.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="mb-4">
            <div className="flex size-16 items-center justify-center rounded-full bg-primary/10 border border-primary/20">
              <Inbox className="size-7 text-primary" />
            </div>
          </div>
          <h3 className="text-lg font-semibold mb-1 text-balance">파이프라인이 없습니다</h3>
          <p className="text-sm text-muted-foreground mb-4 text-pretty">첫 번째 파이프라인을 실행해 보세요.</p>
          <Button asChild>
            <Link to="/pipelines/new">
              <Plus className="mr-2 h-4 w-4" /> New Pipeline
            </Link>
          </Button>
        </div>
      )}

      {!isLoading && !error && runs.length > 0 && (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {runs.map((run) => (
            <Link
              key={run.run_id}
              to={`/pipelines/${run.run_id}`}
              aria-label={`${run.topic} 파이프라인 상세 보기`}
              className="group rounded-xl border border-border bg-card p-4 cursor-pointer transition-all hover:border-primary/30 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-primary/5"
            >
              <div className="flex items-start justify-between gap-2 mb-3">
                <p className="text-sm font-medium leading-snug line-clamp-2 flex-1">{run.topic}</p>
                <StatusBadge status={run.status} />
              </div>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span className="truncate max-w-[120px]">{run.channel_id}</span>
                <div className="flex items-center gap-2 shrink-0">
                  <span>{formatDuration(run.created_at, run.completed_at)}</span>
                  <span>{new Date(run.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
