import { type JSX } from 'react'
import { Badge } from '@/components/ui/badge'

type PipelineStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export function StatusBadge({ status }: { status: PipelineStatus | string }): JSX.Element {
  switch (status) {
    case 'pending':
      return <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30">Pending</Badge>
    case 'running':
      return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">Running</Badge>
    case 'completed':
      return <Badge className="bg-green-500/20 text-green-400 border-green-500/30">Completed</Badge>
    case 'failed':
      return <Badge className="bg-red-500/20 text-red-400 border-red-500/30">Failed</Badge>
    case 'cancelled':
      return <Badge variant="secondary">취소됨</Badge>
    default:
      return <Badge variant="secondary">{status}</Badge>
  }
}
