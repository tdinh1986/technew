import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { FetchButton } from "@/components/FetchButton";

export const metadata: Metadata = {
  title: "TechNew — Tech Digest",
  description: "AI-powered daily technical news digest with actionable insights",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100">
        <nav className="sticky top-0 z-10 border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-950/80 backdrop-blur">
          <div className="max-w-2xl mx-auto px-4 h-14 flex items-center justify-between">
            <Link href="/" className="font-bold text-lg tracking-tight hover:opacity-80">TechNew</Link>
            <div className="flex items-center gap-4">
              <Link href="/summarize" className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100">
                Summarize URLs
              </Link>
              <Link href="/settings" className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100">
                Settings
              </Link>
              <FetchButton />
            </div>
          </div>
        </nav>
        <main>{children}</main>
      </body>
    </html>
  );
}
