import { SidebarProvider } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"
import { Header } from "@/components/layout/header"

export default function AppLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <SidebarProvider>
            <AppSidebar />
            <main className="flex flex-1 flex-col w-full">
                <Header />
                <div className="flex-1 overflow-auto p-6">
                    {children}
                </div>
            </main>
        </SidebarProvider>
    );
}
