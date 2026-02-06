"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Plus, Youtube, AlertTriangle, CheckCircle, ExternalLink } from "lucide-react"

export default function ChannelsPage() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Channels</h2>
                    <p className="text-muted-foreground">Manage connected YouTube channels and quotas.</p>
                </div>
                <Button className="bg-red-600 hover:bg-red-700 text-white">
                    <Plus className="mr-2 h-4 w-4" /> Connect Channel
                </Button>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {/* Active Channel Card */}
                <Card className="bg-card/50 backdrop-blur-sm border-primary/50 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-10">
                        <Youtube className="h-32 w-32" />
                    </div>
                    <CardHeader className="flex flex-row items-center gap-4 pb-2">
                        <div className="h-12 w-12 rounded-full bg-red-600 flex items-center justify-center text-white font-bold text-lg">
                            T
                        </div>
                        <div>
                            <CardTitle>Tech Optimist</CardTitle>
                            <CardDescription>Tech • 1.2M Subs</CardDescription>
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center gap-2 text-sm text-green-400">
                            <CheckCircle className="h-4 w-4" /> Authenticated
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between text-xs text-muted-foreground">
                                <span>Daily Upload Quota</span>
                                <span>2 / 5 Used</span>
                            </div>
                            <Progress value={40} className="h-2" />
                        </div>
                    </CardContent>
                    <CardFooter className="border-t border-white/5 pt-4">
                        <Button variant="ghost" className="w-full text-xs" asChild>
                            <a href="#" target="_blank">Manage on Studio <ExternalLink className="ml-2 h-3 w-3" /></a>
                        </Button>
                    </CardFooter>
                </Card>

                {/* Expired Token Card */}
                <Card className="bg-card/50 backdrop-blur-sm border-white/5 opacity-80">
                    <CardHeader className="flex flex-row items-center gap-4 pb-2">
                        <div className="h-12 w-12 rounded-full bg-slate-700 flex items-center justify-center text-white font-bold text-lg">
                            G
                        </div>
                        <div>
                            <CardTitle>Gaming Highlights</CardTitle>
                            <CardDescription>Gaming • 45K Subs</CardDescription>
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center gap-2 text-sm text-yellow-500">
                            <AlertTriangle className="h-4 w-4" /> Token Expired
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between text-xs text-muted-foreground">
                                <span>Daily Upload Quota</span>
                                <span>0 / 5 Used</span>
                            </div>
                            <Progress value={0} className="h-2" />
                        </div>
                    </CardContent>
                    <CardFooter className="border-t border-white/5 pt-4">
                        <Button variant="outline" className="w-full border-yellow-500/50 text-yellow-500 hover:bg-yellow-500/10">
                            Reconnect
                        </Button>
                    </CardFooter>
                </Card>
            </div>
        </div>
    )
}
