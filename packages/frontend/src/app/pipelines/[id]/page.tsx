"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area" // Note: Need to add scroll-area if not present, otherwise use div
import { CheckCircle2, Circle, Clock, Loader2, PlayCircle, FileText, Image as ImageIcon, Video } from "lucide-react"

// Mock Data
const steps = [
    { id: 1, name: "Brand Research", status: "completed", duration: "2m 30s" },
    { id: 2, name: "Script Writing", status: "completed", duration: "1m 15s" },
    { id: 3, name: "SEO Optimization", status: "completed", duration: "45s" },
    { id: 4, name: "Media Generation", status: "in-progress", duration: "Running..." },
    { id: 5, name: "Video Editing", status: "pending", duration: "-" },
    { id: 6, name: "Youtube Upload", status: "pending", duration: "-" },
]

const logs = [
    "[10:00:01] [System] Pipeline started for 'Future of AI'",
    "[10:00:05] [Research] Searching for 'AI Trends 2026'...",
    "[10:01:20] [Research] Found 15 relevant articles.",
    "[10:02:30] [Research] Completed. Output saved.",
    "[10:02:35] [Script] Generating script with 'Informative' tone...",
    "[10:03:50] [Script] Draft v1 created.",
    "[10:04:35] [SEO] Keywords extracted: ['AI', 'Future', 'Tech'].",
    "[10:05:00] [Media] Generating TTS audio...",
]

export default function PipelineDetailsPage({ params }: { params: { id: string } }) {
    // In a real app, use params.id to fetch data

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Pipeline Details</h2>
                    <p className="text-muted-foreground">ID: PL-001 • Future of AI in 2030</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" className="border-red-500/50 hover:bg-red-500/10 text-red-500">Stop Pipeline</Button>
                    <Button>View on YouTube</Button>
                </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-3">
                {/* Left Column: Status Timeline */}
                <Card className="lg:col-span-1 bg-card/50 backdrop-blur-sm border-white/5 h-fit">
                    <CardHeader>
                        <CardTitle>Progress</CardTitle>
                        <CardDescription>Current stage of automation</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="relative border-l border-muted ml-3 space-y-8 pb-2">
                            {steps.map((step, index) => (
                                <div key={step.id} className="ml-6 relative">
                                    <div className={`absolute -left-[31px] -top-1 h-6 w-6 rounded-full border-2 flex items-center justify-center bg-background
                     ${step.status === 'completed' ? 'border-primary text-primary' :
                                            step.status === 'in-progress' ? 'border-blue-500 text-blue-500 animate-pulse' : 'border-muted text-muted-foreground'
                                        }`}>
                                        {step.status === 'completed' && <CheckCircle2 className="h-4 w-4" />}
                                        {step.status === 'in-progress' && <Loader2 className="h-4 w-4 animate-spin" />}
                                        {step.status === 'pending' && <Circle className="h-4 w-4" />}
                                    </div>
                                    <div className="flex flex-col">
                                        <span className={`font-medium ${step.status === 'in-progress' ? 'text-blue-400' : ''}`}>{step.name}</span>
                                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                                            <Clock className="h-3 w-3" /> {step.duration}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Right Column: Logs & Artifacts */}
                <div className="lg:col-span-2 space-y-6">
                    <Card className="bg-card/50 backdrop-blur-sm border-white/5">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <FileText className="h-5 w-5 text-primary" />
                                Generated Artifacts
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="grid grid-cols-2 md:grid-cols-3 gap-4">
                            <div className="p-4 border rounded-lg bg-background/50 hover:border-primary cursor-pointer transition-colors flex flex-col items-center gap-2 text-center">
                                <FileText className="h-8 w-8 text-muted-foreground" />
                                <span className="text-sm font-medium">Script.md</span>
                            </div>
                            <div className="p-4 border rounded-lg bg-background/50 hover:border-primary cursor-pointer transition-colors flex flex-col items-center gap-2 text-center">
                                <ImageIcon className="h-8 w-8 text-muted-foreground" />
                                <span className="text-sm font-medium">Thumbnails (4)</span>
                            </div>
                            <div className="p-4 border rounded-lg bg-background/50 hover:border-primary cursor-pointer transition-colors flex flex-col items-center gap-2 text-center opacity-50">
                                <Video className="h-8 w-8 text-muted-foreground" />
                                <span className="text-sm font-medium">Final Video (Pending)</span>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="bg-black/80 border-white/10 font-mono text-sm">
                        <CardHeader className="py-3 border-b border-white/10">
                            <CardTitle className="text-sm font-normal text-muted-foreground flex items-center gap-2">
                                <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                                Live Terminal Logs
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 h-[300px] overflow-y-auto space-y-1">
                            {logs.map((log, i) => (
                                <div key={i} className="text-green-500/80 break-all">{log}</div>
                            ))}
                            <div className="animate-pulse">_</div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    )
}
