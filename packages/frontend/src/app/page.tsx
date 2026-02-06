import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Plus, Video, Activity, DollarSign, Clock } from "lucide-react"

export default function Home() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <Button className="bg-primary hover:bg-primary/90 text-white shadow-lg shadow-primary/20">
          <Plus className="mr-2 h-4 w-4" /> Create New Video
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-card/50 backdrop-blur-sm border-white/5">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Videos</CardTitle>
            <Video className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">128</div>
            <p className="text-xs text-muted-foreground">
              +12% from last month
            </p>
          </CardContent>
        </Card>
        <Card className="bg-card/50 backdrop-blur-sm border-white/5">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Pipelines</CardTitle>
            <Activity className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-primary">3</div>
            <p className="text-xs text-muted-foreground">
              Processing right now
            </p>
          </CardContent>
        </Card>
        <Card className="bg-card/50 backdrop-blur-sm border-white/5">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Estimated Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$42.50</div>
            <p className="text-xs text-muted-foreground">
              This month
            </p>
          </CardContent>
        </Card>
        <Card className="bg-card/50 backdrop-blur-sm border-white/5">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg. Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12m</div>
            <p className="text-xs text-muted-foreground">
              Per video generation
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4 bg-card/50 backdrop-blur-sm border-white/5">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>
              Recent pipeline executions and their status.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow className="border-white/10 hover:bg-white/5">
                  <TableHead className="w-[100px]">ID</TableHead>
                  <TableHead>Topic</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[
                  { id: "PL-001", topic: "AI Trends 2026", status: "Running", date: "Just now" },
                  { id: "PL-002", topic: "Python Tutorial", status: "Success", date: "2 hours ago" },
                  { id: "PL-003", topic: "SpaceX Launch", status: "Failed", date: "5 hours ago" },
                  { id: "PL-004", topic: "Healthy Food", status: "Success", date: "Yesterday" },
                ].map((item) => (
                  <TableRow key={item.id} className="border-white/10 hover:bg-white/5">
                    <TableCell className="font-medium">{item.id}</TableCell>
                    <TableCell>{item.topic}</TableCell>
                    <TableCell>
                      <Badge
                        variant="secondary"
                        className={
                          item.status === "Running" ? "bg-primary/20 text-primary hover:bg-primary/30" :
                            item.status === "Success" ? "bg-green-500/20 text-green-400 hover:bg-green-500/30" :
                              "bg-red-500/20 text-red-400 hover:bg-red-500/30"
                        }
                      >
                        {item.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">{item.date}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card className="col-span-3 bg-card/50 backdrop-blur-sm border-white/5">
          <CardHeader>
            <CardTitle>System Health</CardTitle>
            <CardDescription>Status of individual agents</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              { name: "Brand Researcher", status: "Operational" },
              { name: "Script Writer (Claude)", status: "Operational" },
              { name: "SEO Optimizer (GPT-4)", status: "Operational" },
              { name: "Media Generator", status: "Operational" },
              { name: "Video Editor", status: "Maintenance" },
            ].map((agent, i) => (
              <div key={i} className="flex items-center justify-between">
                <span className="text-sm font-medium">{agent.name}</span>
                <div className="flex items-center gap-2">
                  <div className={`h-2 w-2 rounded-full ${agent.status === 'Operational' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-yellow-500'}`} />
                  <span className="text-xs text-muted-foreground">{agent.status}</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
