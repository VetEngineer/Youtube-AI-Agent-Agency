"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
    Card,
    CardContent,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import Link from "next/link"
import {
    Plus,
    TrendingUp,
    RefreshCw,
    Trash2,
    Loader2,
    AlertCircle,
    Eye,
    ThumbsUp,
    MessageSquare,
    Clock,
    Settings,
} from "lucide-react"
import {
    useCompetitors,
    useAddCompetitor,
    useDeleteCompetitor,
    useRefreshCompetitor,
    useCompetitor,
    useIntegrations,
    type CompetitorChannelInfo,
    type CompetitorVideoInfo,
} from "@/hooks/use-competitors"
import { ApiError } from "@/lib/api"

function formatNumber(n: number): string {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
    return n.toString()
}

function formatDate(dateStr: string): string {
    try {
        return new Date(dateStr).toLocaleDateString("ko-KR", {
            year: "numeric",
            month: "short",
            day: "numeric",
        })
    } catch {
        return dateStr
    }
}

function formatDuration(seconds: number | null): string {
    if (!seconds) return "-"
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`
    return `${m}:${String(s).padStart(2, "0")}`
}

function ChannelDetailModal({
    competitorId,
    open,
    onClose,
}: {
    competitorId: string
    open: boolean
    onClose: () => void
}) {
    const { data, isLoading } = useCompetitor(competitorId)
    const refreshMutation = useRefreshCompetitor()

    const handleRefresh = () => {
        refreshMutation.mutate(competitorId)
    }

    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                {isLoading && (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                )}
                {data && (
                    <>
                        <DialogHeader>
                            <div className="flex items-center gap-3">
                                {data.channel.thumbnail_url && (
                                    <img
                                        src={data.channel.thumbnail_url}
                                        alt={data.channel.name}
                                        className="h-12 w-12 rounded-full object-cover"
                                    />
                                )}
                                <div>
                                    <DialogTitle>{data.channel.name}</DialogTitle>
                                    <DialogDescription className="text-xs">
                                        {data.channel.youtube_channel_id}
                                    </DialogDescription>
                                </div>
                            </div>
                        </DialogHeader>

                        {/* 채널 통계 카드 */}
                        <div className="grid grid-cols-3 gap-3">
                            <div className="rounded-lg border p-3 text-center">
                                <p className="text-2xl font-bold">
                                    {formatNumber(data.channel.subscriber_count)}
                                </p>
                                <p className="text-xs text-muted-foreground mt-1">구독자</p>
                            </div>
                            <div className="rounded-lg border p-3 text-center">
                                <p className="text-2xl font-bold">
                                    {formatNumber(data.channel.video_count)}
                                </p>
                                <p className="text-xs text-muted-foreground mt-1">총 영상</p>
                            </div>
                            <div className="rounded-lg border p-3 text-center">
                                <p className="text-2xl font-bold">
                                    {data.channel.last_crawled_at
                                        ? formatDate(data.channel.last_crawled_at)
                                        : "-"}
                                </p>
                                <p className="text-xs text-muted-foreground mt-1">마지막 수집</p>
                            </div>
                        </div>

                        {/* 최근 영상 테이블 */}
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="font-semibold text-sm">최근 영상</h3>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={handleRefresh}
                                    disabled={refreshMutation.isPending}
                                >
                                    {refreshMutation.isPending ? (
                                        <Loader2 className="h-3 w-3 animate-spin mr-1" />
                                    ) : (
                                        <RefreshCw className="h-3 w-3 mr-1" />
                                    )}
                                    데이터 갱신
                                </Button>
                            </div>
                            {data.recent_videos.length === 0 ? (
                                <p className="text-sm text-muted-foreground text-center py-8">
                                    수집된 영상이 없습니다. 데이터 갱신 버튼을 눌러 수집하세요.
                                </p>
                            ) : (
                                <div className="rounded-md border overflow-hidden">
                                    <Table>
                                        <TableHeader>
                                            <TableRow>
                                                <TableHead>제목</TableHead>
                                                <TableHead className="w-[80px] text-right">
                                                    <Eye className="h-3 w-3 inline mr-1" />
                                                    조회수
                                                </TableHead>
                                                <TableHead className="w-[80px] text-right">
                                                    <ThumbsUp className="h-3 w-3 inline mr-1" />
                                                    좋아요
                                                </TableHead>
                                                <TableHead className="w-[80px] text-right">
                                                    <MessageSquare className="h-3 w-3 inline mr-1" />
                                                    댓글
                                                </TableHead>
                                                <TableHead className="w-[70px] text-right">
                                                    <Clock className="h-3 w-3 inline mr-1" />
                                                    길이
                                                </TableHead>
                                                <TableHead className="w-[90px]">게시일</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {data.recent_videos.map((video: CompetitorVideoInfo) => (
                                                <TableRow key={video.video_id}>
                                                    <TableCell className="max-w-[250px]">
                                                        <p className="truncate text-sm font-medium">
                                                            {video.title}
                                                        </p>
                                                        {video.tags.length > 0 && (
                                                            <div className="flex gap-1 mt-1 flex-wrap">
                                                                {video.tags.slice(0, 3).map((tag) => (
                                                                    <Badge
                                                                        key={tag}
                                                                        variant="secondary"
                                                                        className="text-xs px-1 py-0"
                                                                    >
                                                                        {tag}
                                                                    </Badge>
                                                                ))}
                                                                {video.tags.length > 3 && (
                                                                    <span className="text-xs text-muted-foreground">
                                                                        +{video.tags.length - 3}
                                                                    </span>
                                                                )}
                                                            </div>
                                                        )}
                                                    </TableCell>
                                                    <TableCell className="text-right text-sm">
                                                        {formatNumber(video.view_count)}
                                                    </TableCell>
                                                    <TableCell className="text-right text-sm">
                                                        {formatNumber(video.like_count)}
                                                    </TableCell>
                                                    <TableCell className="text-right text-sm">
                                                        {formatNumber(video.comment_count)}
                                                    </TableCell>
                                                    <TableCell className="text-right text-sm text-muted-foreground">
                                                        {formatDuration(video.duration_seconds)}
                                                    </TableCell>
                                                    <TableCell className="text-sm text-muted-foreground">
                                                        {formatDate(video.published_at)}
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </div>
                            )}
                        </div>
                    </>
                )}
            </DialogContent>
        </Dialog>
    )
}

function CompetitorCard({
    competitor,
    onDelete,
}: {
    competitor: CompetitorChannelInfo
    onDelete: (id: string) => void
}) {
    const [detailOpen, setDetailOpen] = useState(false)
    const refreshMutation = useRefreshCompetitor()

    return (
        <>
            <Card className="bg-card/50 backdrop-blur-sm border-primary/50 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-10">
                    <TrendingUp className="h-32 w-32" />
                </div>
                <CardHeader className="flex flex-row items-center gap-3 pb-2">
                    {competitor.thumbnail_url ? (
                        <img
                            src={competitor.thumbnail_url}
                            alt={competitor.name}
                            className="h-12 w-12 rounded-full object-cover shrink-0"
                        />
                    ) : (
                        <div className="h-12 w-12 rounded-full bg-primary/20 flex items-center justify-center text-lg font-bold shrink-0">
                            {competitor.name.charAt(0).toUpperCase()}
                        </div>
                    )}
                    <div className="min-w-0">
                        <CardTitle className="text-base truncate">{competitor.name}</CardTitle>
                        <p className="text-xs text-muted-foreground truncate">
                            {competitor.youtube_channel_id}
                        </p>
                    </div>
                </CardHeader>

                <CardContent className="space-y-3">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                        <div className="rounded border p-2 text-center">
                            <p className="font-semibold">
                                {formatNumber(competitor.subscriber_count)}
                            </p>
                            <p className="text-xs text-muted-foreground">구독자</p>
                        </div>
                        <div className="rounded border p-2 text-center">
                            <p className="font-semibold">
                                {formatNumber(competitor.video_count)}
                            </p>
                            <p className="text-xs text-muted-foreground">영상</p>
                        </div>
                    </div>
                    {competitor.last_crawled_at && (
                        <p className="text-xs text-muted-foreground">
                            마지막 수집: {formatDate(competitor.last_crawled_at)}
                        </p>
                    )}
                    <Badge
                        variant={competitor.is_active ? "default" : "secondary"}
                        className="text-xs"
                    >
                        {competitor.is_active ? "모니터링 중" : "비활성"}
                    </Badge>
                </CardContent>

                <CardFooter className="border-t border-white/5 pt-3 flex gap-2">
                    <Button
                        variant="ghost"
                        size="sm"
                        className="flex-1 text-xs"
                        onClick={() => setDetailOpen(true)}
                    >
                        상세 보기
                    </Button>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => refreshMutation.mutate(competitor.id)}
                        disabled={refreshMutation.isPending}
                    >
                        {refreshMutation.isPending ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                            <RefreshCw className="h-3 w-3" />
                        )}
                    </Button>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                        onClick={() => onDelete(competitor.id)}
                    >
                        <Trash2 className="h-3 w-3" />
                    </Button>
                </CardFooter>
            </Card>

            {detailOpen && (
                <ChannelDetailModal
                    competitorId={competitor.id}
                    open={detailOpen}
                    onClose={() => setDetailOpen(false)}
                />
            )}
        </>
    )
}

export default function CompetitorsPage() {
    const [addDialogOpen, setAddDialogOpen] = useState(false)
    const [channelIdInput, setChannelIdInput] = useState("")
    const [addError, setAddError] = useState<string | null>(null)

    const { data, isLoading, error } = useCompetitors()
    const { data: integrations } = useIntegrations()
    const addMutation = useAddCompetitor()
    const deleteMutation = useDeleteCompetitor()

    const handleAdd = async () => {
        if (!channelIdInput.trim()) return
        setAddError(null)
        try {
            await addMutation.mutateAsync({ youtube_channel_id: channelIdInput.trim() })
            setAddDialogOpen(false)
            setChannelIdInput("")
        } catch (err) {
            if (err instanceof ApiError) {
                if (err.status === 404) {
                    setAddError("채널을 찾을 수 없습니다. YouTube 채널 ID를 확인하세요.")
                } else if (err.status === 503) {
                    setAddError("YOUTUBE_API_KEY가 설정되지 않았습니다.")
                } else {
                    setAddError(`채널 등록에 실패했습니다. (${err.status})`)
                }
            } else {
                setAddError("채널 등록에 실패했습니다.")
            }
        }
    }

    const handleDelete = async (competitorId: string) => {
        if (!confirm("이 경쟁 채널을 제거하시겠습니까?")) return
        deleteMutation.mutate(competitorId)
    }

    return (
        <div className="space-y-6">
            {/* 헤더 */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Competitors</h2>
                    <p className="text-muted-foreground">
                        경쟁 채널의 업로드 현황과 영상 성과를 모니터링합니다.
                    </p>
                </div>
                <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
                    <DialogTrigger asChild>
                        <Button>
                            <Plus className="mr-2 h-4 w-4" /> 채널 추가
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>경쟁 채널 추가</DialogTitle>
                            <DialogDescription>
                                YouTube 채널 ID를 입력하세요. (UC로 시작하는 형식: UCxxxxxx)
                            </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-2 py-2">
                            <Label htmlFor="channelId">YouTube 채널 ID</Label>
                            <Input
                                id="channelId"
                                placeholder="UCxxxxxxxxxxxxxxxxxxxxxx"
                                value={channelIdInput}
                                onChange={(e) => setChannelIdInput(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                            />
                            <p className="text-xs text-muted-foreground">
                                채널 URL의 /channel/ 뒤에 있는 ID를 입력하세요.
                            </p>
                            {addError && (
                                <p className="text-sm text-destructive">{addError}</p>
                            )}
                        </div>
                        <DialogFooter>
                            <Button
                                variant="ghost"
                                onClick={() => {
                                    setAddDialogOpen(false)
                                    setAddError(null)
                                }}
                            >
                                취소
                            </Button>
                            <Button
                                onClick={handleAdd}
                                disabled={addMutation.isPending || !channelIdInput.trim()}
                            >
                                {addMutation.isPending && (
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                )}
                                추가
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>

            {/* YouTube API Key 미설정 경고 */}
            {integrations && !integrations.youtube_api_key_set && (
                <div className="flex items-center gap-3 rounded-md border border-yellow-500/40 bg-yellow-500/10 p-4 text-sm text-yellow-400">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    <span>
                        YouTube API Key가 설정되지 않았습니다. 채널 등록 및 데이터 수집을 위해 먼저 API Key를 입력하세요.
                    </span>
                    <Button variant="outline" size="sm" className="ml-auto shrink-0 border-yellow-500/40 text-yellow-400 hover:text-yellow-300" asChild>
                        <Link href="/settings?tab=integrations">
                            <Settings className="h-3 w-3 mr-1" />
                            설정하기
                        </Link>
                    </Button>
                </div>
            )}

            {/* 로딩 */}
            {isLoading && (
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            )}

            {/* 에러 */}
            {error && (
                <div className="flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    경쟁 채널을 불러오지 못했습니다.
                </div>
            )}

            {/* 빈 상태 */}
            {!isLoading && !error && data?.competitors.length === 0 && (
                <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
                    <TrendingUp className="mb-4 h-12 w-12 opacity-30" />
                    <p className="text-lg font-medium">등록된 경쟁 채널이 없습니다</p>
                    <p className="text-sm mt-1">
                        채널 추가 버튼으로 경쟁 채널을 등록하세요.
                    </p>
                </div>
            )}

            {/* 채널 그리드 */}
            {!isLoading && !error && data && data.competitors.length > 0 && (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {data.competitors.map((competitor) => (
                        <CompetitorCard
                            key={competitor.id}
                            competitor={competitor}
                            onDelete={handleDelete}
                        />
                    ))}
                </div>
            )}
        </div>
    )
}
