import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { BookOpen, User, Settings } from "lucide-react";
import "./globals.css";

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
        <header className="sticky top-0 z-50 glass-panel border-b border-b-[var(--color-glass-border)]">
          <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <a href="/" className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity">
              <div className="bg-[var(--color-nyu-violet)] p-1.5 rounded-lg shadow-[0_0_15px_rgba(87,6,140,0.8)]">
                <BookOpen size={20} className="text-white" />
              </div>
              <span className="font-bold text-xl tracking-tight text-white">
                NYUSEARCH
              </span>
            </a>
            
            <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-300">
              <a href="/" className="hover:text-white transition-colors">Courses</a>
              <a href="/dashboard" className="hover:text-white transition-colors">Dashboard</a>
            </nav>

            <div className="flex items-center gap-4 text-sm font-medium">
              <a href="/login" className="text-gray-300 hover:text-white transition-colors">Log In</a>
              <a href="/register" className="bg-[var(--color-nyu-violet)] text-white px-4 py-2 rounded-lg hover:bg-[var(--color-nyu-violet-light)] shadow-[0_0_10px_rgba(87,6,140,0.5)] transition-all">Sign Up</a>
              <button className="text-gray-400 hover:text-white transition-colors p-2 rounded-full hover:bg-[var(--color-glass)] ml-2">
                <Settings size={20} />
              </button>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 max-w-7xl w-full mx-auto p-6">
          {children}
        </main>
        
      </body>
    </html>
  );
}
