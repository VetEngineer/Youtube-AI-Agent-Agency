"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Plus, Youtube, CheckCircle, ExternalLink, Loader2, AlertCircle, Trash2 } from "lucide-react"
import { api, ApiError } from "@/lib/api"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface Channel {
    channel_id: string
    name: string
    category: string
    has_brand_guide: boolean
}

interface ChannelListResponse {
    channels: Channel[]
    total: number
}

export default function ChannelsPage() {
    const [channels, setChannels] = useState<Channel[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [dialogOpen, setDialogOpen] = useState(false)
    const [newChannelId, setNewChannelId] = useState("")
    const [creating, setCreating] = useState(false)
    const [createError, setCreateError] = useState<string | null>(null)

    async function fetchChannels() {
        try {
            setLoading(true)
            setError(null)
            const data = await api.get<ChannelListResponse>("/channels/")
            setChannels(data.channels)
        } catch (err) {
            if (err instanceof ApiError) {
                setError(`채널을 불러오지 못했습니다. (${err.status})`)
            } else {
                setError("채널을 불러오지 못했습니다.")
            }
        } finally {
            setLoading(false)
        }
    }

    async function handleCreateChannel() {
        if (!newChannelId.trim()) return
        setCreating(true)
        setCreateError(null)
        try {
            await api.post<Channel>("/channels/", { channel_id: newChannelId.trim() })
            setDialogOpen(false)
            setNewChannelId("")
            await fetchChannels()
        } catch (err) {
            if (err instanceof ApiError) {
                if (err.status === 409) {
                    setCreateError("이미 존재하는 채널 ID입니다.")
                } else if (err.status === 403) {
                    setCreateError("채널 추가 권한이 없습니다.")
                } else {
                    setCreateError(`채널 생성에 실패했습니다. (${err.status})`)
                }
            } else {
                setCreateError("채널 생성에 실패했습니다.")
            }
        } finally {
            setCreating(false)
        }
    }

    async function handleDeleteChannel(channelId: string) {
        if (!confirm(`채널 "${channelId}"를 삭제하시겠습니까?`)) return
        try {
            await api.delete(`/channels/${channelId}`)
            await fetchChannels()
        } catch {
            // ignore
        }
    }

    useEffect(() => {
        fetchChannels()
    }, [])

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Channels</h2>
                    <p className="text-muted-foreground">Manage connected YouTube channels and quotas.</p>
                </div>
                <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                    <DialogTrigger asChild>
                        <Button className="bg-red-600 hover:bg-red-700 text-white">
                            <Plus className="mr-2 h-4 w-4" /> Connect Channel
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>새 채널 추가</DialogTitle>
                            <DialogDescription>
                                채널 ID를 입력하세요. 영문, 숫자, 하이픈(-), 언더스코어(_)만 사용 가능합니다.
                            </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-2 py-2">
                            <Label htmlFor="channelId">채널 ID</Label>
                            <Input
                                id="channelId"
                                placeholder="my-channel"
                                value={newChannelId}
                                onChange={(e) => setNewChannelId(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && handleCreateChannel()}
                            />
                            {createError && (
                                <p className="text-sm text-destructive">{createError}</p>
                            )}
                        </div>
                        <DialogFooter>
                            <Button variant="ghost" onClick={() => setDialogOpen(false)}>취소</Button>
                            <Button
                                onClick={handleCreateChannel}
                                disabled={creating || !newChannelId.trim()}
                                className="bg-red-600 hover:bg-red-700 text-white"
                            >
                                {creating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                추가
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>

            {loading && (
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            )}

            {error && (
                <div className="flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    {error}
                    <Button variant="ghost" size="sm" className="ml-auto" onClick={fetchChannels}>
                        재시도
                    </Button>
                </div>
            )}

            {!loading && !error && channels.length === 0 && (
                <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
                    <Youtube className="mb-4 h-12 w-12 opacity-30" />
                    <p className="text-lg font-medium">연결된 채널이 없습니다</p>
                    <p className="text-sm mt-1">Connect Channel 버튼으로 첫 채널을 추가하세요.</p>
                </div>
            )}

            {!loading && !error && channels.length > 0 && (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {channels.map((channel) => (
                        <Card
                            key={channel.channel_id}
                            className="bg-card/50 backdrop-blur-sm border-primary/50 relative overflow-hidden"
                        >
                            <div className="absolute top-0 right-0 p-4 opacity-10">
                                <Youtube className="h-32 w-32" />
                            </div>
                            <CardHeader className="flex flex-row items-center gap-4 pb-2">
                                <div className="h-12 w-12 rounded-full bg-red-600 flex items-center justify-center text-white font-bold text-lg">
                                    {channel.name.charAt(0).toUpperCase()}
                                </div>
                                <div>
                                    <CardTitle>{channel.name}</CardTitle>
                                    <CardDescription>{channel.category}</CardDescription>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex items-center gap-2 text-sm text-green-400">
                                    <CheckCircle className="h-4 w-4" />
                                    Active
                                </div>
                                <div className="flex gap-2 flex-wrap">
                                    <Badge variant="secondary">{channel.channel_id}</Badge>
                                    {channel.has_brand_guide && (
                                        <Badge variant="outline" className="border-blue-500/50 text-blue-400">
                                            Brand Guide
                                        </Badge>
                                    )}
                                </div>
                            </CardContent>
                            <CardFooter className="border-t border-white/5 pt-4 flex gap-2">
                                <Button variant="ghost" className="flex-1 text-xs" asChild>
                                    <a
                                        href={`https://studio.youtube.com`}
                                        target="_blank"
                                        rel="noreferrer"
                                    >
                                        Studio <ExternalLink className="ml-2 h-3 w-3" />
                                    </a>
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="text-destructive hover:text-destructive hover:bg-destructive/10"
                                    onClick={() => handleDeleteChannel(channel.channel_id)}
                                >
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </CardFooter>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    )
}
