"use client";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";

interface HeaderProps {
  title?: string;
}

export function Header({ title = "Youtube Agent Agency" }: HeaderProps) {
  return (
    <header className="flex h-16 shrink-0 items-center border-b border-border/50 px-4">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mx-4 h-6" />
      <h1 className="text-lg font-semibold tracking-tight">{title}</h1>
    </header>
  );
}
