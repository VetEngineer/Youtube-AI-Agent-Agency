import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"
import Providers from "./providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Youtube AI Agent Agency",
  description: "Automated YouTube Content Generation Dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <SidebarProvider>
          <Providers>
            <AppSidebar />
            <main className="w-full">
              <div className="flex h-16 items-center border-b px-4">
                <SidebarTrigger />
                <h1 className="ml-4 text-lg font-semibold">Youtube Agent Agency</h1>
              </div>
              <div className="p-4">
                {children}
              </div>
            </main>
          </Providers>
        </SidebarProvider>
      </body>
    </html>
  );
}
