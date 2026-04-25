"use client";

import { BookOpen, Settings, LogOut } from "lucide-react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function Header() {
  const router = useRouter();
  const [user, setUser] = useState<{ first_name: string } | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      fetch("http://localhost:8000/api/user/me", {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      .then(res => {
        if (res.ok) return res.json();
        throw new Error("Invalid token");
      })
      .then(data => {
        setUser(data);
        setIsLoading(false);
      })
      .catch(() => {
        localStorage.removeItem("token");
        setUser(null);
        setIsLoading(false);
      });
    } else {
      setIsLoading(false);
    }
  }, []);

  const handleLogout = () => {
    if (window.confirm("Are you sure you want to log out?")) {
      localStorage.removeItem("token");
      setUser(null);
      window.location.href = "/";
    }
  };

  return (
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
          {isLoading ? (
            <div className="flex items-center gap-4">
              <div className="w-24 h-8 animate-pulse bg-[var(--color-glass-border)] rounded-md"></div>
              <div className="w-8 h-8 animate-pulse bg-[var(--color-glass-border)] rounded-full"></div>
            </div>
          ) : user ? (
            <>
              <span className="text-gray-300">Welcome, <strong className="text-white">{user.first_name}</strong></span>
              <button className="text-gray-400 hover:text-white transition-colors p-2 rounded-full hover:bg-[var(--color-glass)]">
                <Settings size={20} />
              </button>
              <button 
                onClick={handleLogout}
                className="text-gray-400 hover:text-red-400 transition-colors p-2 rounded-full hover:bg-red-500/10 ml-2"
                title="Log Out"
              >
                <LogOut size={18} />
              </button>
            </>
          ) : (
            <>
              <a href="/login" className="text-gray-300 hover:text-white transition-colors">Log In</a>
              <a href="/register" className="bg-[var(--color-nyu-violet)] text-white px-4 py-2 rounded-lg hover:bg-[var(--color-nyu-violet-light)] shadow-[0_0_10px_rgba(87,6,140,0.5)] transition-all">Sign Up</a>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
