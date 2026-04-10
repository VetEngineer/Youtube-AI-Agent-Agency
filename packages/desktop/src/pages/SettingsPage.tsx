import { useState, type JSX } from 'react'
import { BackendSection } from '@/pages/settings/BackendSection'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Progress } from '@/components/ui/progress'
import { useApiKeys, useCreateApiKey, useDeleteApiKey } from '@/hooks/use-api-keys'
import { useChannels, useCreateChannel, useUpdateChannel, useDeleteChannel } from '@/hooks/use-channels'
import { usePlans, usePlanUsage, type PlanInfo } from '@/hooks/use-plans'
import { useCheckout } from '@/hooks/use-billing'
import { useIntegrations, useUpdateIntegrations } from '@/hooks/use-competitors'
import { ApiError } from '@/lib/api'
import { useAuth } from '@/providers/AuthProvider'
import {
  Key,
  Plus,
  Trash2,
  Copy,
  Check,
  AlertCircle,
  Loader2,
  Settings2,
  Crown,
  Zap,
  Building2,
  PlaySquare,
  Eye,
  EyeOff,
  LogOut,
} from 'lucide-react'

// ─── ApiKeySection ─────────────────────────────────────────────────────────────

function ApiKeySection(): JSX.Element {
  const { data, isLoading, error, refetch } = useApiKeys()
  const createApiKey = useCreateApiKey(refetch)
  const deleteApiKey = useDeleteApiKey(refetch)

  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [deleteKeyId, setDeleteKeyId] = useState<string | null>(null)
  const [newKeyData, setNewKeyData] = useState({ name: '', scopes: ['read'], expires_days: 90 })
  const [createdKey, setCreatedKey] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const handleCreate = async () => {
    try {
      const result = await createApiKey.mutate({
        name: newKeyData.name,
        scopes: newKeyData.scopes,
        expires_days: newKeyData.expires_days,
      })
      setCreatedKey(result.key)
      setNewKeyData({ name: '', scopes: ['read'], expires_days: 90 })
    } catch {
      // error handled by local state in hook
    }
  }

  const handleCopy = async () => {
    if (createdKey) {
      await navigator.clipboard.writeText(createdKey)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleDelete = async () => {
    if (deleteKeyId) {
      try {
        await deleteApiKey.mutate(deleteKeyId)
        setDeleteKeyId(null)
      } catch {
        // error handled by local state in hook
      }
    }
  }

  if (error) {
    const isAuthError =
      error instanceof ApiError && (error.status === 401 || error.status === 403)
    return (
      <div className="flex items-center gap-2 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
        <AlertCircle className="h-4 w-4 text-red-400" />
        <span className="text-sm text-red-400">
          {isAuthError
            ? 'Admin access required. Please use an API key with admin scope.'
            : 'Failed to load API keys.'}
        </span>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-medium text-balance">API Keys</h4>
          <p className="text-sm text-muted-foreground text-pretty">Manage access keys for the API.</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={(open) => {
          setIsCreateOpen(open)
          if (!open) {
            setCreatedKey(null)
            setCopied(false)
          }
        }}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              New Key
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{createdKey ? 'API Key Created' : 'Create API Key'}</DialogTitle>
              <DialogDescription>
                {createdKey
                  ? 'Copy your new API key now. You will not be able to see it again.'
                  : 'Create a new API key for accessing the API.'}
              </DialogDescription>
            </DialogHeader>
            {createdKey ? (
              <div className="space-y-4">
                <div className="flex items-center gap-2 p-3 bg-muted rounded-lg font-mono text-sm">
                  <code className="flex-1 truncate">{createdKey}</code>
                  <Button variant="ghost" size="icon" onClick={() => void handleCopy()} aria-label="API 키 복사">
                    {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                  </Button>
                </div>
                <DialogFooter>
                  <Button onClick={() => {
                    setIsCreateOpen(false)
                    setCreatedKey(null)
                  }}>Done</Button>
                </DialogFooter>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="key-name">Name</Label>
                  <Input
                    id="key-name"
                    placeholder="My API Key"
                    value={newKeyData.name}
                    onChange={(e) => setNewKeyData({ ...newKeyData, name: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Scopes</Label>
                  <Select
                    value={newKeyData.scopes.includes('admin') ? 'admin' : 'read'}
                    onValueChange={(val) => setNewKeyData({
                      ...newKeyData,
                      scopes: val === 'admin' ? ['admin', 'read', 'write'] : ['read'],
                    })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="read">Read Only</SelectItem>
                      <SelectItem value="admin">Admin (Full Access)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="expires">Expires In (Days)</Label>
                  <Input
                    id="expires"
                    type="number"
                    value={newKeyData.expires_days}
                    onChange={(e) => {
                      const val = parseInt(e.target.value, 10)
                      setNewKeyData({ ...newKeyData, expires_days: isNaN(val) ? 90 : Math.max(1, val) })
                    }}
                  />
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
                  <Button onClick={() => void handleCreate()} disabled={!newKeyData.name || createApiKey.isLoading}>
                    {createApiKey.isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                    Create
                  </Button>
                </DialogFooter>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>

      <div className="border rounded-lg">
        {isLoading ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin inline mr-2" />
            Loading...
          </div>
        ) : data?.api_keys && data.api_keys.length > 0 ? (
          <div className="divide-y">
            {data.api_keys.map((key) => (
              <div key={key.key_id} className="p-4 flex items-center justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Key className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{key.name}</span>
                    <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{key.prefix}...</code>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>Created: {new Date(key.created_at).toLocaleDateString()}</span>
                    {key.expires_at && (
                      <span>Expires: {new Date(key.expires_at).toLocaleDateString()}</span>
                    )}
                  </div>
                  <div className="flex gap-1">
                    {key.scopes.map((scope) => (
                      <Badge key={scope} variant="secondary" className="text-xs">{scope}</Badge>
                    ))}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-red-400 hover:text-red-500 hover:bg-red-500/10"
                  onClick={() => setDeleteKeyId(key.key_id)}
                  aria-label={`API 키 삭제: ${key.name}`}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 text-center text-sm text-muted-foreground">
            No API keys found. Create one to get started.
          </div>
        )}
      </div>

      <AlertDialog open={!!deleteKeyId} onOpenChange={(open) => !open && setDeleteKeyId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete API Key?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. Applications using this key will no longer be able to access the API.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => void handleDelete()}
              className="bg-red-500 hover:bg-red-600"
            >
              {deleteApiKey.isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

// ─── ChannelSection ─────────────────────────────────────────────────────────────

function ChannelSection(): JSX.Element {
  const { data, isLoading, error, refetch } = useChannels()
  const createChannel = useCreateChannel(refetch)
  const updateChannel = useUpdateChannel(refetch)
  const deleteChannel = useDeleteChannel(refetch)

  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [editChannel, setEditChannel] = useState<{ channel_id: string; name: string; category: string } | null>(null)
  const [deleteChannelId, setDeleteChannelId] = useState<string | null>(null)
  const [newChannel, setNewChannel] = useState({ channel_id: '', name: '', category: 'general' })
  const [formError, setFormError] = useState<string | null>(null)

  const validateChannelId = (id: string) => /^[a-z0-9-]+$/.test(id)

  const handleCreate = async () => {
    setFormError(null)
    if (!validateChannelId(newChannel.channel_id)) {
      setFormError('Channel ID must contain only lowercase letters, numbers, and hyphens.')
      return
    }
    try {
      await createChannel.mutate(newChannel)
      setIsCreateOpen(false)
      setNewChannel({ channel_id: '', name: '', category: 'general' })
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setFormError('A channel with this ID already exists.')
      } else {
        setFormError('Failed to create channel.')
      }
    }
  }

  const handleUpdate = async () => {
    if (!editChannel) return
    try {
      await updateChannel.mutate({
        channelId: editChannel.channel_id,
        data: { name: editChannel.name, category: editChannel.category },
      })
      setEditChannel(null)
    } catch {
      // error handled by hook state
    }
  }

  const handleDelete = async () => {
    if (!deleteChannelId) return
    try {
      await deleteChannel.mutate(deleteChannelId)
      setDeleteChannelId(null)
    } catch {
      // error handled by hook state
    }
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
        <AlertCircle className="h-4 w-4 text-red-400" />
        <span className="text-sm text-red-400">Failed to load channels.</span>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-medium text-balance">Channels</h4>
          <p className="text-sm text-muted-foreground text-pretty">Manage YouTube channel configurations.</p>
        </div>
        <Dialog open={isCreateOpen} onOpenChange={(open) => {
          setIsCreateOpen(open)
          if (!open) {
            setFormError(null)
            setNewChannel({ channel_id: '', name: '', category: 'general' })
          }
        }}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              New Channel
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Channel</DialogTitle>
              <DialogDescription>Add a new channel configuration.</DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              {formError && (
                <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                  <AlertCircle className="h-4 w-4 text-red-400" />
                  <span className="text-sm text-red-400">{formError}</span>
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="channel-id">Channel ID</Label>
                <Input
                  id="channel-id"
                  placeholder="my-tech-channel"
                  value={newChannel.channel_id}
                  onChange={(e) => setNewChannel({ ...newChannel, channel_id: e.target.value.toLowerCase() })}
                />
                <p className="text-xs text-muted-foreground">Lowercase letters, numbers, and hyphens only.</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="channel-name">Display Name</Label>
                <Input
                  id="channel-name"
                  placeholder="My Tech Channel"
                  value={newChannel.name}
                  onChange={(e) => setNewChannel({ ...newChannel, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Category</Label>
                <Select
                  value={newChannel.category}
                  onValueChange={(val) => setNewChannel({ ...newChannel, category: val })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="general">General</SelectItem>
                    <SelectItem value="technology">Technology</SelectItem>
                    <SelectItem value="education">Education</SelectItem>
                    <SelectItem value="entertainment">Entertainment</SelectItem>
                    <SelectItem value="business">Business</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
                <Button
                  onClick={() => void handleCreate()}
                  disabled={!newChannel.channel_id || !newChannel.name || createChannel.isLoading}
                >
                  {createChannel.isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Create
                </Button>
              </DialogFooter>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="border rounded-lg">
        {isLoading ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin inline mr-2" />
            Loading...
          </div>
        ) : data?.channels && data.channels.length > 0 ? (
          <div className="divide-y">
            {data.channels.map((channel) => (
              <div key={channel.channel_id} className="p-4 flex items-center justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{channel.name}</span>
                    <Badge variant="secondary" className="text-xs">{channel.category}</Badge>
                  </div>
                  <code className="text-xs text-muted-foreground">{channel.channel_id}</code>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`채널 편집: ${channel.name}`}
                    onClick={() => setEditChannel({
                      channel_id: channel.channel_id,
                      name: channel.name,
                      category: channel.category,
                    })}
                  >
                    <Settings2 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-red-400 hover:text-red-500 hover:bg-red-500/10"
                    aria-label={`채널 삭제: ${channel.channel_id}`}
                    onClick={() => setDeleteChannelId(channel.channel_id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 text-center text-sm text-muted-foreground">
            No channels found. Create one to get started.
          </div>
        )}
      </div>

      <Dialog open={!!editChannel} onOpenChange={(open) => !open && setEditChannel(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Channel</DialogTitle>
            <DialogDescription>Update channel configuration.</DialogDescription>
          </DialogHeader>
          {editChannel && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Channel ID</Label>
                <Input value={editChannel.channel_id} disabled />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-name">Display Name</Label>
                <Input
                  id="edit-name"
                  value={editChannel.name}
                  onChange={(e) => setEditChannel({ ...editChannel, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Category</Label>
                <Select
                  value={editChannel.category}
                  onValueChange={(val) => setEditChannel({ ...editChannel, category: val })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="general">General</SelectItem>
                    <SelectItem value="technology">Technology</SelectItem>
                    <SelectItem value="education">Education</SelectItem>
                    <SelectItem value="entertainment">Entertainment</SelectItem>
                    <SelectItem value="business">Business</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setEditChannel(null)}>Cancel</Button>
                <Button onClick={() => void handleUpdate()} disabled={updateChannel.isLoading}>
                  {updateChannel.isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Save
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!deleteChannelId} onOpenChange={(open) => !open && setDeleteChannelId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Channel?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. All configurations for this channel will be permanently deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => void handleDelete()}
              className="bg-red-500 hover:bg-red-600"
            >
              {deleteChannel.isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

// ─── AccountSection — Desktop replaces browser-localStorage auth with AuthProvider ─

function AccountSection(): JSX.Element {
  const { userInfo, apiKey, clearApiKey } = useAuth()

  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-sm font-medium text-balance">계정</h4>
        <p className="text-sm text-muted-foreground text-pretty">현재 로그인된 계정 정보입니다.</p>
      </div>

      <div className="border rounded-lg p-4 space-y-4">
        {userInfo && (
          <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
              {(userInfo.name ?? userInfo.email).charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0">
              {userInfo.name && <p className="text-sm font-medium truncate">{userInfo.name}</p>}
              <p className="text-xs text-muted-foreground truncate">{userInfo.email}</p>
            </div>
          </div>
        )}
        {apiKey && (
          <div className="flex items-center gap-2 text-sm">
            <Key className="h-4 w-4 text-muted-foreground shrink-0" />
            <span className="text-muted-foreground">API Key:</span>
            <code className="bg-muted px-1.5 py-0.5 rounded text-xs">{apiKey.substring(0, 12)}...</code>
          </div>
        )}
        <Button
          variant="outline"
          size="sm"
          className="text-destructive hover:text-destructive hover:bg-destructive/10"
          onClick={() => void clearApiKey()}
        >
          <LogOut className="h-4 w-4 mr-2" />
          로그아웃
        </Button>
      </div>
    </div>
  )
}

// ─── PlansSection ─────────────────────────────────────────────────────────────

const PLAN_ICONS: Record<string, JSX.Element> = {
  free: <Zap className="h-5 w-5 text-muted-foreground" />,
  pro: <Crown className="h-5 w-5 text-yellow-500" />,
  enterprise: <Building2 className="h-5 w-5 text-purple-500" />,
}

const PLAN_LABELS: Record<string, string> = {
  free: 'Free',
  pro: 'Pro',
  enterprise: 'Enterprise',
}

function FeatureRow({ label, enabled }: { label: string; enabled: boolean }): JSX.Element {
  return (
    <div className="flex items-center justify-between text-sm">
      <span>{label}</span>
      {enabled ? (
        <Check className="h-4 w-4 text-green-500" />
      ) : (
        <span className="text-xs text-muted-foreground">-</span>
      )}
    </div>
  )
}

function PlanCard({
  plan,
  isCurrent,
  onUpgrade,
  isUpgrading,
}: {
  plan: PlanInfo
  isCurrent: boolean
  onUpgrade?: (planName: string) => void
  isUpgrading?: boolean
}): JSX.Element {
  const limit = plan.quotas.monthly_pipelines
  const channelLimit = plan.quotas.max_channels
  const canUpgrade = !isCurrent && plan.name !== 'free'

  return (
    <div className={`rounded-lg border p-4 space-y-3 ${isCurrent ? 'border-primary bg-primary/5' : ''}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {PLAN_ICONS[plan.name] ?? <Zap className="h-5 w-5" />}
          <span className="font-semibold">{PLAN_LABELS[plan.name] ?? plan.name}</span>
        </div>
        {isCurrent && (
          <Badge variant="secondary" className="text-xs">Current</Badge>
        )}
      </div>
      <div className="text-sm text-muted-foreground">
        {limit === -1 ? 'Unlimited' : limit} pipelines/month
      </div>
      <div className="text-sm text-muted-foreground">
        {channelLimit === -1 ? 'Unlimited' : channelLimit} channels
      </div>
      <div className="space-y-1.5 pt-2 border-t">
        <FeatureRow label="Media Generation" enabled={plan.quotas.media_generation} />
        <FeatureRow label="YouTube Upload" enabled={plan.quotas.youtube_upload} />
        <FeatureRow label="Priority Queue" enabled={plan.quotas.priority_queue} />
        <FeatureRow label="API Access" enabled={plan.quotas.api_access} />
      </div>
      {isCurrent ? (
        <Button variant="outline" className="w-full" disabled>현재 플랜</Button>
      ) : canUpgrade ? (
        <Button
          className="w-full"
          onClick={() => onUpgrade?.(plan.name)}
          disabled={isUpgrading}
        >
          {isUpgrading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
          업그레이드
        </Button>
      ) : null}
    </div>
  )
}

function PlansSection(): JSX.Element {
  const { data: plansData, isLoading: plansLoading, error: plansError } = usePlans()
  const { data: usage, isLoading: usageLoading } = usePlanUsage()
  const checkout = useCheckout()
  const [upgradeError, setUpgradeError] = useState<string | null>(null)

  const handleUpgrade = async (planName: string) => {
    setUpgradeError(null)
    try {
      const result = await checkout.mutate(planName)
      // TODO M4: @tauri-apps/plugin-shell의 open()으로 교체 필요
      // Tauri WebView에서 window.open은 새 WebView를 열 수 있음
      // window.open(result.checkout_url, '_blank')는 임시 방편
      window.open(result.checkout_url, '_blank', 'noopener,noreferrer')
    } catch (err) {
      const message = err instanceof Error ? err.message : '결제 처리 중 오류가 발생했습니다.'
      setUpgradeError(message)
    }
  }

  if (plansError) {
    return (
      <div className="flex items-center gap-2 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
        <AlertCircle className="h-4 w-4 text-red-400" />
        <span className="text-sm text-red-400">Failed to load plan information.</span>
      </div>
    )
  }

  const isLoading = plansLoading || usageLoading
  const isUpgrading = checkout.isLoading

  if (isLoading) {
    return (
      <div className="p-4 text-center text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin inline mr-2" />
        Loading...
      </div>
    )
  }

  const currentPlan = usage?.plan ?? 'free'
  const isUnlimited = usage ? usage.pipelines_limit === -1 : false
  const pipelinesPercent = isUnlimited
    ? 0
    : usage
      ? Math.min((usage.pipelines_used / usage.pipelines_limit) * 100, 100)
      : 0
  const channelsPercent =
    usage && usage.channels_limit !== -1
      ? Math.min((usage.channels_used / usage.channels_limit) * 100, 100)
      : 0

  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-sm font-medium text-balance">Plans & Usage</h4>
        <p className="text-sm text-muted-foreground text-pretty">View your current plan and usage statistics.</p>
      </div>

      {upgradeError && (
        <div className="flex items-center gap-2 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
          <AlertCircle className="h-4 w-4 text-red-400" />
          <span className="text-sm text-red-400">{upgradeError}</span>
        </div>
      )}

      {usage && (
        <div className="rounded-lg border p-4 space-y-4">
          <h5 className="text-sm font-medium text-balance">Current Usage</h5>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Pipelines this month</span>
                <span className="font-medium">
                  {isUnlimited
                    ? `${usage.pipelines_used} used`
                    : `${usage.pipelines_used} / ${usage.pipelines_limit}`}
                </span>
              </div>
              {!isUnlimited && <Progress value={pipelinesPercent} className="h-2" />}
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Channels</span>
                <span className="font-medium">
                  {usage.channels_limit === -1
                    ? `${usage.channels_used} used`
                    : `${usage.channels_used} / ${usage.channels_limit}`}
                </span>
              </div>
              {usage.channels_limit !== -1 && (
                <Progress value={channelsPercent} className="h-2" />
              )}
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        {plansData?.plans.map((plan) => (
          <PlanCard
            key={plan.name}
            plan={plan}
            isCurrent={plan.name === currentPlan}
            onUpgrade={(name) => void handleUpgrade(name)}
            isUpgrading={isUpgrading}
          />
        ))}
      </div>
    </div>
  )
}

// ─── IntegrationsSection ──────────────────────────────────────────────────────

function IntegrationsSection(): JSX.Element {
  const { data, isLoading, error, refetch } = useIntegrations()
  const updateIntegration = useUpdateIntegrations(refetch)

  const [integrationError, setIntegrationError] = useState<string | null>(null)

  const [ytKeyInput, setYtKeyInput] = useState('')
  const [showYtInput, setShowYtInput] = useState(false)
  const [showYtKey, setShowYtKey] = useState(false)
  const [ytSaved, setYtSaved] = useState(false)

  const [elKeyInput, setElKeyInput] = useState('')
  const [showElInput, setShowElInput] = useState(false)
  const [elSaved, setElSaved] = useState(false)

  const handleYtSave = async () => {
    if (!ytKeyInput.trim()) return
    try {
      await updateIntegration.mutate({ youtube_api_key: ytKeyInput.trim() })
      setYtKeyInput('')
      setShowYtInput(false)
      setYtSaved(true)
      setIntegrationError(null)
      setTimeout(() => setYtSaved(false), 2500)
    } catch {
      setIntegrationError('YouTube API 키 저장에 실패했습니다.')
    }
  }

  const handleYtRemove = async () => {
    try {
      await updateIntegration.mutate({ youtube_api_key: '' })
      setIntegrationError(null)
    } catch {
      setIntegrationError('YouTube API 키 삭제에 실패했습니다.')
    }
  }

  const handleElSave = async () => {
    if (!elKeyInput.trim()) return
    try {
      await updateIntegration.mutate({ elevenlabs_api_key: elKeyInput.trim() })
      setElKeyInput('')
      setShowElInput(false)
      setElSaved(true)
      setIntegrationError(null)
      setTimeout(() => setElSaved(false), 2500)
    } catch {
      setIntegrationError('ElevenLabs API 키 저장에 실패했습니다.')
    }
  }

  const handleElRemove = async () => {
    try {
      await updateIntegration.mutate({ elevenlabs_api_key: '' })
      setIntegrationError(null)
    } catch {
      setIntegrationError('ElevenLabs API 키 삭제에 실패했습니다.')
    }
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
        <AlertCircle className="h-4 w-4 text-red-400" />
        <span className="text-sm text-red-400">통합 설정을 불러오지 못했습니다.</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-sm font-medium text-balance">Integrations</h4>
        <p className="text-sm text-muted-foreground text-pretty">
          외부 서비스 연동에 필요한 API 키를 관리합니다.
        </p>
      </div>

      {integrationError && (
        <p role="alert" className="text-destructive text-sm">{integrationError}</p>
      )}

      {/* ElevenLabs */}
      <div className="rounded-lg border p-4 space-y-4">
        <div className="flex items-center gap-3">
          <div className="size-9 rounded-lg bg-purple-600/10 flex items-center justify-center">
            <Key className="h-5 w-5 text-purple-500" />
          </div>
          <div>
            <p className="text-sm font-medium">ElevenLabs API</p>
            <p className="text-xs text-muted-foreground">음성 생성(TTS)에 사용됩니다. elevenlabs.io에서 발급하세요.</p>
          </div>
          <div className="ml-auto">
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            ) : data?.elevenlabs_api_key_set ? (
              <span className="inline-flex items-center gap-1 text-xs text-green-500 bg-green-500/10 border border-green-500/20 rounded-full px-2 py-0.5">
                <Check className="h-3 w-3" /> 설정됨
              </span>
            ) : (
              <span className="text-xs text-muted-foreground">미설정 (서버 기본값 사용)</span>
            )}
          </div>
        </div>

        {data?.elevenlabs_api_key_set && data.elevenlabs_api_key_masked && (
          <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
            <div className="flex items-center gap-2">
              <Key className="h-4 w-4 text-muted-foreground" />
              <code className="text-sm">{data.elevenlabs_api_key_masked}</code>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-destructive hover:text-destructive"
              aria-label="ElevenLabs API 키 삭제"
              onClick={() => void handleElRemove()}
              disabled={updateIntegration.isLoading}
            >
              {updateIntegration.isLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3 w-3" />}
            </Button>
          </div>
        )}

        {!showElInput && (
          <Button variant="outline" size="sm" onClick={() => setShowElInput(true)}>
            <Plus className="h-3 w-3 mr-1" />
            {data?.elevenlabs_api_key_set ? '키 변경' : '키 입력'}
          </Button>
        )}

        {showElInput && (
          <div className="space-y-2">
            <div className="flex gap-2">
              <Input
                type="password"
                placeholder="sk_..."
                value={elKeyInput}
                onChange={(e) => setElKeyInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') void handleElSave() }}
                className="font-mono text-sm"
              />
              <Button onClick={() => void handleElSave()} disabled={!elKeyInput.trim() || updateIntegration.isLoading}>
                {updateIntegration.isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : elSaved ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  '저장'
                )}
              </Button>
              <Button variant="ghost" onClick={() => { setShowElInput(false); setElKeyInput('') }}>취소</Button>
            </div>
            <p className="text-xs text-muted-foreground">
              elevenlabs.io → Profile → API Keys에서 발급한 키를 입력하세요.
            </p>
          </div>
        )}
      </div>

      {/* YouTube Data API */}
      <div className="rounded-lg border p-4 space-y-4">
        <div className="flex items-center gap-3">
          <div className="size-9 rounded-lg bg-red-600/10 flex items-center justify-center">
            <PlaySquare className="h-5 w-5 text-red-500" />
          </div>
          <div>
            <p className="text-sm font-medium">YouTube Data API v3</p>
            <p className="text-xs text-muted-foreground">경쟁 채널 모니터링에 사용됩니다. Google Cloud Console에서 발급하세요.</p>
          </div>
          <div className="ml-auto">
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            ) : data?.youtube_api_key_set ? (
              <span className="inline-flex items-center gap-1 text-xs text-green-500 bg-green-500/10 border border-green-500/20 rounded-full px-2 py-0.5">
                <Check className="h-3 w-3" /> 설정됨
              </span>
            ) : (
              <span className="text-xs text-muted-foreground">미설정</span>
            )}
          </div>
        </div>

        {data?.youtube_api_key_set && data.youtube_api_key_masked && (
          <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
            <div className="flex items-center gap-2">
              <Key className="h-4 w-4 text-muted-foreground" />
              <code className="text-sm">{data.youtube_api_key_masked}</code>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-destructive hover:text-destructive"
              aria-label="YouTube API 키 삭제"
              onClick={() => void handleYtRemove()}
              disabled={updateIntegration.isLoading}
            >
              {updateIntegration.isLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3 w-3" />}
            </Button>
          </div>
        )}

        {!showYtInput && (
          <Button variant="outline" size="sm" onClick={() => setShowYtInput(true)}>
            <Plus className="h-3 w-3 mr-1" />
            {data?.youtube_api_key_set ? '키 변경' : '키 입력'}
          </Button>
        )}

        {showYtInput && (
          <div className="space-y-2">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Input
                  type={showYtKey ? 'text' : 'password'}
                  placeholder="AIzaSy..."
                  value={ytKeyInput}
                  onChange={(e) => setYtKeyInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') void handleYtSave() }}
                  className="pr-9 font-mono text-sm"
                />
                <button
                  type="button"
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  onClick={() => setShowYtKey((v) => !v)}
                >
                  {showYtKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <Button onClick={() => void handleYtSave()} disabled={!ytKeyInput.trim() || updateIntegration.isLoading}>
                {updateIntegration.isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : ytSaved ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  '저장'
                )}
              </Button>
              <Button variant="ghost" onClick={() => { setShowYtInput(false); setYtKeyInput('') }}>취소</Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Google Cloud Console → API 및 서비스 → 사용자 인증 정보에서 발급한 서버 키를 입력하세요.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── SettingsPage ──────────────────────────────────────────────────────────────

export default function SettingsPage(): JSX.Element {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-balance">프로필</h3>
        <p className="text-sm text-muted-foreground text-pretty">
          API 관리, 채널 설정, 요금제를 관리합니다.
        </p>
      </div>

      <Tabs defaultValue="account" className="space-y-4">
        <TabsList>
          <TabsTrigger value="account">계정</TabsTrigger>
          <TabsTrigger value="api-keys">API 관리</TabsTrigger>
          <TabsTrigger value="channels">채널</TabsTrigger>
          <TabsTrigger value="integrations">연동</TabsTrigger>
          <TabsTrigger value="plans">요금제</TabsTrigger>
          <TabsTrigger value="backend">백엔드 연결</TabsTrigger>
        </TabsList>

        <TabsContent value="account" className="rounded-xl border bg-card text-card-foreground shadow p-6">
          <AccountSection />
        </TabsContent>

        <TabsContent value="api-keys" className="rounded-xl border bg-card text-card-foreground shadow p-6">
          <ApiKeySection />
        </TabsContent>

        <TabsContent value="channels" className="rounded-xl border bg-card text-card-foreground shadow p-6">
          <ChannelSection />
        </TabsContent>

        <TabsContent value="integrations" className="rounded-xl border bg-card text-card-foreground shadow p-6">
          <IntegrationsSection />
        </TabsContent>

        <TabsContent value="plans" className="rounded-xl border bg-card text-card-foreground shadow p-6">
          <PlansSection />
        </TabsContent>

        <TabsContent value="backend" className="rounded-xl border bg-card text-card-foreground shadow p-6">
          <BackendSection />
        </TabsContent>
      </Tabs>
    </div>
  )
}
