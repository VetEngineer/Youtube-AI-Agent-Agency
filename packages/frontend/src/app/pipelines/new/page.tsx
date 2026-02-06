"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { ArrowRight, Sparkles, Youtube } from "lucide-react"

export default function NewPipelinePage() {
    return (
        <div className="max-w-3xl mx-auto space-y-8 py-8">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Create New Video</h2>
                <p className="text-muted-foreground">Start a new AI automation pipeline.</p>
            </div>

            <div className="grid gap-6">
                <Card className="border-primary/20 bg-card/50 backdrop-blur-sm">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Sparkles className="h-5 w-5 text-primary" />
                            Core Concept
                        </CardTitle>
                        <CardDescription>
                            What is this video about?
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="topic">Topic / Keyword</Label>
                            <Input id="topic" placeholder="e.g. 'Future of AI in 2030'" className="bg-background/50" />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Tone</Label>
                                <div className="flex gap-2">
                                    <Badge variant="outline" className="cursor-pointer hover:bg-primary hover:text-white">Informative</Badge>
                                    <Badge variant="outline" className="cursor-pointer hover:bg-primary hover:text-white">Funny</Badge>
                                    <Badge variant="outline" className="cursor-pointer hover:bg-primary hover:text-white">Dramatic</Badge>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label>Duration</Label>
                                <div className="flex gap-2">
                                    <Badge variant="outline" className="cursor-pointer hover:bg-primary hover:text-white">Shorts</Badge>
                                    <Badge variant="outline" className="cursor-pointer bg-primary text-white">10min+</Badge>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-card/50 backdrop-blur-sm">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Youtube className="h-5 w-5 text-red-500" />
                            Channel Target
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="p-4 border rounded-lg bg-background/50 flex justify-between items-center cursor-pointer hover:border-primary transition-colors">
                            <div>
                                <div className="font-semibold">Tech Optimist</div>
                                <div className="text-xs text-muted-foreground">Main Channel • 1.2M Subs</div>
                            </div>
                            <div className="h-4 w-4 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
                        </div>
                    </CardContent>
                    <CardFooter className="flex justify-end">
                        <Button size="lg" className="bg-gradient-to-r from-primary to-secondary w-full sm:w-auto">
                            Start Generation <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                    </CardFooter>
                </Card>
            </div>
        </div>
    )
}
