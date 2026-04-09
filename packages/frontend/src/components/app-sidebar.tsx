"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession, signOut } from "next-auth/react";
import { Home, Youtube, Activity, BookOpen, Rocket, TrendingUp, LogOut, ChevronUp, User, UserCircle } from "lucide-react";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
} from "@/components/ui/sidebar";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const items = [
  {
    title: "Dashboard",
    url: "/",
    icon: Home,
    tooltip: "전체 파이프라인 실행 현황과 통계를 확인합니다",
  },
  {
    title: "Pipelines",
    url: "/pipelines",
    icon: Activity,
    tooltip: "AI가 영상 원고 → SEO → 편집 → 업로드를 자동으로 처리하는 작업 목록",
  },
  {
    title: "Channels",
    url: "/channels",
    icon: Youtube,
    tooltip: "파이프라인과 연결할 YouTube 채널을 등록하고 관리합니다",
  },
  {
    title: "Competitors",
    url: "/competitors",
    icon: TrendingUp,
    tooltip: "경쟁 채널 업로드 현황과 영상 성과를 모니터링합니다",
  },
  {
    title: "프로필",
    url: "/settings",
    icon: UserCircle,
    tooltip: "API 관리, 요금제, 계정 설정을 변경합니다",
  },
];

export function AppSidebar() {
  const pathname = usePathname();
  const { data: session } = useSession();

  const isActive = (url: string) => {
    if (url === "/") {
      return pathname === "/";
    }
    return pathname === url || pathname.startsWith(url + "/");
  };

  const displayName = session?.user?.name || session?.user?.email?.split("@")[0] || "사용자";
  const displayEmail = session?.user?.email || "";
  const avatarFallback = displayName.charAt(0).toUpperCase();

  return (
    <TooltipProvider delayDuration={300}>
      <Sidebar>
        {/* 브랜딩 헤더 */}
        <div className="flex h-16 items-center gap-3 border-b border-sidebar-border px-4 shrink-0">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary shadow-[0_0_12px_hsl(0_90%_60%/0.4)]">
            <Youtube className="h-4 w-4 text-white" />
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-sm font-bold tracking-tight truncate">YAA Studio</span>
            <span className="text-[10px] text-muted-foreground truncate">AI Agent Agency</span>
          </div>
        </div>

        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>Youtube Agent</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {items.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <SidebarMenuButton asChild isActive={isActive(item.url)}>
                          <Link href={item.url}>
                            <item.icon />
                            <span>{item.title}</span>
                          </Link>
                        </SidebarMenuButton>
                      </TooltipTrigger>
                      <TooltipContent side="right" className="max-w-[200px]">
                        {item.tooltip}
                      </TooltipContent>
                    </Tooltip>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>

        <SidebarFooter>
          <SidebarMenu>
            <SidebarMenuItem>
              <Tooltip>
                <TooltipTrigger asChild>
                  <SidebarMenuButton asChild isActive={pathname === "/guide"}>
                    <Link href="/guide">
                      <BookOpen />
                      <span>사용 가이드</span>
                    </Link>
                  </SidebarMenuButton>
                </TooltipTrigger>
                <TooltipContent side="right">
                  처음 사용하시나요? 빠른 시작 가이드를 확인하세요
                </TooltipContent>
              </Tooltip>
            </SidebarMenuItem>
            <SidebarMenuItem>
              <Tooltip>
                <TooltipTrigger asChild>
                  <SidebarMenuButton asChild isActive={pathname === "/onboarding"}>
                    <Link href="/onboarding">
                      <Rocket />
                      <span>시작하기</span>
                    </Link>
                  </SidebarMenuButton>
                </TooltipTrigger>
                <TooltipContent side="right">
                  온보딩 마법사로 첫 채널과 파이프라인을 설정합니다
                </TooltipContent>
              </Tooltip>
            </SidebarMenuItem>

            {/* 프로필 / 로그아웃 */}
            <SidebarMenuItem>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <SidebarMenuButton className="h-10">
                    <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
                      {session?.user?.image ? (
                        <img
                          src={session.user.image}
                          alt={displayName}
                          className="h-6 w-6 rounded-full object-cover"
                        />
                      ) : (
                        avatarFallback
                      )}
                    </div>
                    <div className="flex min-w-0 flex-col text-left">
                      <span className="truncate text-sm font-medium">{displayName}</span>
                      {displayEmail && (
                        <span className="truncate text-xs text-muted-foreground">{displayEmail}</span>
                      )}
                    </div>
                    <ChevronUp className="ml-auto h-4 w-4 shrink-0 opacity-50" />
                  </SidebarMenuButton>
                </DropdownMenuTrigger>
                <DropdownMenuContent side="top" align="start" className="w-56">
                  <div className="px-2 py-1.5">
                    <p className="text-sm font-medium">{displayName}</p>
                    {displayEmail && (
                      <p className="text-xs text-muted-foreground truncate">{displayEmail}</p>
                    )}
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link href="/settings" className="cursor-pointer">
                      <User className="mr-2 h-4 w-4" />
                      프로필
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    className="text-destructive focus:text-destructive cursor-pointer"
                    onClick={() => signOut({ callbackUrl: "/login" })}
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    로그아웃
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarFooter>
      </Sidebar>
    </TooltipProvider>
  );
}
