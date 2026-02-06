'use client';

import { useDashboardSummary } from '@/hooks/use-dashboard';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

export default function Home() {
  const { data: summary, isLoading, error } = useDashboardSummary();

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-32 rounded-xl bg-muted/20 animate-pulse" />
        ))}
      </div>
    );
  }

  // Fallback if API fails or is empty
  const stats = summary || {
    total_runs: 0,
    active_runs: 0,
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
            <h3 className="tracking-tight text-sm font-medium">Total Videos</h3>
          </div>
          <div className="p-6 pt-0">
            <div className="text-2xl font-bold">{stats.total_runs}</div>
          </div>
        </div>
        <div className="rounded-xl border bg-card text-card-foreground shadow">
          <div className="p-6 flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Active Pipelines</h3>
          </div>
          <div className="p-6 pt-0">
            <div className="text-2xl font-bold">{stats.active_runs}</div>
            <p className="text-xs text-muted-foreground">Running now</p>
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
                  <div key={run.run_id} className="flex items-center">
                    <div className="ml-4 space-y-1">
                      <Link href={`/pipelines/${run.run_id}`} className="hover:underline">
                        <p className="text-sm font-medium leading-none">{run.topic}</p>
                      </Link>
                      <p className="text-sm text-muted-foreground capitalize">{run.status}</p>
                    </div>
                    <div className="ml-auto font-medium text-sm text-muted-foreground">
                      {new Date(run.created_at).toLocaleDateString()}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-sm text-muted-foreground text-center py-4">
                  No recent activity. Start a pipeline!
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
