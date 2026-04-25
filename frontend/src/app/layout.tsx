import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { BookOpen, User, Settings } from "lucide-react";
import "./globals.css";
import Header from "@/components/Header";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "NYU Course Search",
  description: "Find your perfect courses at NYU",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}>
      <body className="min-h-full flex flex-col relative overflow-x-hidden">
        
        {/* Abstract Background Effects */}
        <div className="fixed inset-0 pointer-events-none z-[-1]">
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-[var(--color-nyu-violet-dark)] blur-[150px] opacity-70"></div>
          <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-[#1a0033] blur-[150px] opacity-60"></div>
        </div>

        {/* Global Navigation Header */}
        <Header />

        {/* Main Content Area */}
        <main className="flex-1 max-w-7xl w-full mx-auto p-6">
          {children}
        </main>
        
      </body>
    </html>
  );
}
