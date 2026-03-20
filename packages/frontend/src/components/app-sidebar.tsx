"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Settings, Youtube, Activity, BookOpen, Rocket, TrendingUp } from "lucide-react";

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
    title: "Settings",
    url: "/settings",
    icon: Settings,
    tooltip: "API 키, 요금제, 계정 설정을 변경합니다",
  },
];

export function AppSidebar() {
  const pathname = usePathname();

  const isActive = (url: string) => {
    if (url === "/") {
      return pathname === "/";
    }
    return pathname === url || pathname.startsWith(url + "/");
  };

  return (
    <TooltipProvider delayDuration={300}>
      <Sidebar>
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
          </SidebarMenu>
        </SidebarFooter>
      </Sidebar>
    </TooltipProvider>
  );
}
