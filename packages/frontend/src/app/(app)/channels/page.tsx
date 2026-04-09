"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Skeleton } from "@/components/ui/skeleton"
import { Plus, AlertCircle, Inbox, Loader2 } from "lucide-react"
import { useChannels, useCreateChannel } from "@/hooks/use-channels"
import { ApiError } from "@/lib/api"

function slugify(name: string): string {
    return name
        .toLowerCase()
        .replace(/[^a-z0-9가-힣\s-]/g, '')
        .trim()
        .replace(/[\s]+/g, '-')
        .replace(/-+/g, '-')
        .slice(0, 50) || 'channel';
}

function getAvatarBg(category: string): string {
    const map: Record<string, string> = {
        tech: 'bg-blue-600',
        gaming: 'bg-purple-600',
        music: 'bg-pink-600',
        education: 'bg-green-600',
        news: 'bg-orange-600',
        general: 'bg-slate-600',
    };
    return map[category] ?? 'bg-slate-600';
}

export default function ChannelsPage() {
    const { data, isLoading, error } = useChannels()
    const createChannel = useCreateChannel()
    const [open, setOpen] = useState(false)
    const [name, setName] = useState('')
    const [category, setCategory] = useState('general')
    const [errorMsg, setErrorMsg] = useState('')

    const handleCreate = async () => {
        setErrorMsg('')
        try {
            await createChannel.mutateAsync({
                channel_id: slugify(name),
                name: name.trim(),
                category,
            })
            setOpen(false)
            setName('')
            setCategory('general')
        } catch (err) {
            if (err instanceof ApiError && err.status === 409) {
                setErrorMsg('같은 이름의 채널이 이미 존재합니다.')
            } else {
                setErrorMsg('채널 생성에 실패했습니다. 다시 시도해 주세요.')
            }
        }
    }

    const channels = data?.channels ?? []


    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold text-balance">Channels</h2>
                    <p className="text-muted-foreground text-pretty">Manage your YouTube channels.</p>
                </div>
                <Button onClick={() => setOpen(true)}>
                    <Plus className="mr-2 h-4 w-4" /> Connect Channel
                </Button>
            </div>

            {isLoading && (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {[1, 2, 3].map((i) => (
                        <Skeleton key={i} className="h-48 rounded-xl" />
                    ))}

                </div>
            )}

            {error && (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                    <AlertCircle className="h-10 w-10 text-red-400 mb-3" />
                    <p className="text-sm text-muted-foreground">채널 목록을 불러오지 못했습니다.</p>
                </div>
            )}

            {!isLoading && !error && channels.length === 0 && (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                    <Inbox className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-1">채널이 없습니다</h3>
                    <p className="text-sm text-muted-foreground mb-4">첫 번째 채널을 추가해 보세요.</p>
                    <Button onClick={() => setOpen(true)}>
                        <Plus className="mr-2 h-4 w-4" /> 채널 추가

                    </Button>
                </div>
            )}

            {!isLoading && !error && channels.length > 0 && (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {channels.map((channel) => (
                        <Card key={channel.channel_id} className="bg-card/50 backdrop-blur-sm border-white/5">
                            <CardHeader className="flex flex-row items-center gap-4 pb-2">
                                <div className={`h-12 w-12 rounded-full ${getAvatarBg(channel.category)} flex items-center justify-center text-white font-bold text-lg`}>
                                    {channel.name.charAt(0).toUpperCase()}
                                </div>
                                <div>
                                    <CardTitle className="text-base">{channel.name}</CardTitle>
                                    <CardDescription>{channel.category} · {channel.channel_id}</CardDescription>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <p className="text-xs text-muted-foreground">
                                    {channel.has_brand_guide ? '브랜드 가이드 설정됨' : '브랜드 가이드 없음'}
                                </p>
                            </CardContent>
                            <CardFooter className="border-t border-white/5 pt-4">
                                <Button variant="ghost" className="w-full text-xs" asChild>
                                    <a href={`/channels/${channel.channel_id}`}>상세 보기</a>

                                </Button>
                            </CardFooter>
                        </Card>
                    ))}
                </div>
            )}

            <Dialog open={open} onOpenChange={(v) => { setOpen(v); if (!v) { setErrorMsg(''); setName(''); setCategory('general'); } }}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>채널 추가</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-2">
                        <div className="space-y-2">
                            <Label htmlFor="ch-name">채널 이름 *</Label>
                            <Input
                                id="ch-name"
                                placeholder="예: 테크 인사이트"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="ch-category">카테고리</Label>
                            <Input
                                id="ch-category"
                                placeholder="예: tech, gaming, education"
                                value={category}
                                onChange={(e) => setCategory(e.target.value)}
                            />
                        </div>
                        {errorMsg && (
                            <div className="flex items-center gap-2 text-sm text-red-500">
                                <AlertCircle className="h-4 w-4 shrink-0" />
                                {errorMsg}
                            </div>
                        )}
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setOpen(false)} disabled={createChannel.isPending}>
                            취소
                        </Button>
                        <Button onClick={handleCreate} disabled={!name.trim() || createChannel.isPending}>
                            {createChannel.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            생성
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

        </div>
    )
}
