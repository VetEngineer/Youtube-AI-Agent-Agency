import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { SidebarProvider } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"
import { Header } from "@/components/layout/header"
import Providers from "./providers";

const pretendard = localFont({
  src: [
    { path: "../../public/fonts/pretendard-latin-400-normal.woff2", weight: "400" },
    { path: "../../public/fonts/pretendard-latin-500-normal.woff2", weight: "500" },
    { path: "../../public/fonts/pretendard-latin-600-normal.woff2", weight: "600" },
    { path: "../../public/fonts/pretendard-latin-700-normal.woff2", weight: "700" },
  ],
  variable: "--font-pretendard",
  display: "swap",
});

const inter = localFont({
  src: [
    { path: "../../public/fonts/inter-latin-400-normal.woff2", weight: "400" },
    { path: "../../public/fonts/inter-latin-500-normal.woff2", weight: "500" },
    { path: "../../public/fonts/inter-latin-600-normal.woff2", weight: "600" },
    { path: "../../public/fonts/inter-latin-700-normal.woff2", weight: "700" },
  ],
  variable: "--font-inter",
  display: "swap",
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
    <html lang="ko" className="dark">
      <body
        className={`${pretendard.variable} ${inter.variable} antialiased`}
      >
        <SidebarProvider>
          <Providers>
            <AppSidebar />
            <main className="flex flex-1 flex-col w-full">
              <Header />
              <div className="flex-1 overflow-auto p-6">
                {children}
              </div>
            </main>
          </Providers>
        </SidebarProvider>
      </body>
    </html>
  );
}
