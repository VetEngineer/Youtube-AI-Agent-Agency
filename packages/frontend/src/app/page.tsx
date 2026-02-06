'use client';

import { useDashboardSummary } from '@/hooks/use-dashboard';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Plus, Play, CheckCircle, XCircle, Clock } from 'lucide-react';

function formatDuration(seconds: number | null): string {
  if (seconds === null) return '-';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
}

function getStatusBadge(status: string) {
  switch (status) {
    case 'completed':
      return <Badge className="bg-green-500/20 text-green-400 border-green-500/30">Completed</Badge>;
    case 'running':
      return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">Running</Badge>;
    case 'failed':
      return <Badge className="bg-red-500/20 text-red-400 border-red-500/30">Failed</Badge>;
    case 'pending':
      return <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30">Pending</Badge>;
    default:
      return <Badge variant="secondary">{status}</Badge>;
  }
}

export default function Home() {
  const { data: summary, isLoading, error } = useDashboardSummary();

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div className="h-9 w-40 rounded bg-muted/20 animate-pulse" />
          <div className="h-10 w-36 rounded bg-muted/20 animate-pulse" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 rounded-xl bg-muted/20 animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <XCircle className="h-12 w-12 text-red-400 mb-4" />
        <h3 className="text-lg font-semibold">Failed to load dashboard</h3>
        <p className="text-sm text-muted-foreground mt-1">Please check your API connection and try again.</p>
      </div>
    );
  }

  const stats = summary || {
    total_runs: 0,
    active_runs: 0,
    success_runs: 0,
    failed_runs: 0,
    avg_duration_sec: null,
    recent_runs: [],
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <Button asChild>
          <Link href="/pipelines/new">
            <Plus className="mr-2 h-4 w-4" /> Create Pipeline
          </Link>
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border bg-card text-card-foreground shadow">
          <div className="p-6 flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Total Runs</h3>
            <Play className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="p-6 pt-0">
            <div className="text-2xl font-bold">{stats.total_runs}</div>
            <p className="text-xs text-muted-foreground">All pipeline executions</p>
          </div>
        </div>

        <div className="rounded-xl border bg-card text-card-foreground shadow">
          <div className="p-6 flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Active</h3>
            <div className="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
          </div>
          <div className="p-6 pt-0">
            <div className="text-2xl font-bold">{stats.active_runs}</div>
            <p className="text-xs text-muted-foreground">Running now</p>
          </div>
        </div>

        <div className="rounded-xl border bg-card text-card-foreground shadow">
          <div className="p-6 flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Successful</h3>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </div>
          <div className="p-6 pt-0">
            <div className="text-2xl font-bold">{stats.success_runs}</div>
            <p className="text-xs text-muted-foreground">Completed successfully</p>
          </div>
        </div>

        <div className="rounded-xl border bg-card text-card-foreground shadow">
          <div className="p-6 flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Failed</h3>
            <XCircle className="h-4 w-4 text-red-500" />
          </div>
          <div className="p-6 pt-0">
            <div className="text-2xl font-bold">{stats.failed_runs}</div>
            <p className="text-xs text-muted-foreground">Needs attention</p>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <div className="col-span-4 rounded-xl border bg-card text-card-foreground shadow">
          <div className="p-6">
            <h3 className="font-semibold leading-none tracking-tight">Recent Activity</h3>
            <p className="text-sm text-muted-foreground">Latest pipeline executions</p>
          </div>
          <div className="p-6 pt-0">
            <div className="space-y-4">
              {stats.recent_runs && stats.recent_runs.length > 0 ? (
                stats.recent_runs.map((run) => (
                  <Link
                    key={run.run_id}
                    href={`/pipelines/${run.run_id}`}
                    className="flex items-center p-3 rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex-1 space-y-1">
                      <p className="text-sm font-medium leading-none">{run.topic}</p>
                      <p className="text-xs text-muted-foreground">{run.channel_id}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      {getStatusBadge(run.status)}
                      <span className="text-xs text-muted-foreground">
                        {new Date(run.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </Link>
                ))
              ) : (
                <div className="text-sm text-muted-foreground text-center py-8">
                  No recent activity. Start your first pipeline!
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="col-span-3 rounded-xl border bg-card text-card-foreground shadow">
          <div className="p-6">
            <h3 className="font-semibold leading-none tracking-tight">Performance</h3>
            <p className="text-sm text-muted-foreground">Average execution metrics</p>
          </div>
          <div className="p-6 pt-0 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Avg. Duration</span>
              </div>
              <span className="text-sm font-medium">{formatDuration(stats.avg_duration_sec)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Success Rate</span>
              <span className="text-sm font-medium">
                {stats.total_runs > 0
                  ? `${Math.round((stats.success_runs / stats.total_runs) * 100)}%`
                  : '-'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
