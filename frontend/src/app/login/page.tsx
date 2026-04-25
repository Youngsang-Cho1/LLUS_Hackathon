"use client";

import { BookOpen } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      // FastAPI OAuth2PasswordRequestForm expects URL Encoded Form Data, not JSON
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData,
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Invalid email or password");
      }

      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      window.location.href = "/";

    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh]">
      <div className="w-full max-w-md glass-panel rounded-2xl p-8 relative overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[80%] h-1 bg-gradient-to-r from-transparent via-[var(--color-nyu-violet)] to-transparent opacity-50"></div>
        
        <div className="flex flex-col items-center mb-8">
          <div className="bg-[var(--color-nyu-violet)] p-3 rounded-xl shadow-[0_0_15px_rgba(87,6,140,0.8)] mb-4">
            <BookOpen size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Welcome Back</h1>
          <p className="text-gray-400 text-sm mt-1">Log in to manage your schedules</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-400 text-sm px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <label className="text-xs font-semibold text-gray-400 tracking-wider uppercase">Email Address</label>
            <input 
              type="email" 
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="netid@nyu.edu"
              className="w-full bg-[var(--color-dark-bg)] border border-[var(--color-glass-border)] rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-nyu-violet)] text-white placeholder:text-gray-600"
            />
          </div>
          
          <div className="flex flex-col gap-2 mb-2">
            <div className="flex justify-between items-center">
              <label className="text-xs font-semibold text-gray-400 tracking-wider uppercase">Password</label>
              <a href="#" className="text-xs text-[var(--color-nyu-violet-light)] hover:underline">Forgot password?</a>
            </div>
            <input 
              type="password" 
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-[var(--color-dark-bg)] border border-[var(--color-glass-border)] rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-nyu-violet)] text-white placeholder:text-gray-600"
            />
          </div>

          <button 
            type="submit" 
            disabled={isLoading}
            className={`w-full py-3 rounded-lg font-bold text-white transition-all mt-2
              ${isLoading ? 'bg-gray-600 cursor-not-allowed' : 'bg-gradient-to-r from-[var(--color-nyu-violet-light)] to-[var(--color-nyu-violet)] shadow-[0_0_15px_rgba(87,6,140,0.5)] hover:shadow-[0_0_25px_rgba(87,6,140,0.7)]'}
            `}
          >
            {isLoading ? 'Logging in...' : 'Log In'}
          </button>
        </form>



        <p className="text-center text-sm text-gray-400 mt-8">
          Don't have an account? <a href="/register" className="text-[var(--color-nyu-violet-light)] font-bold hover:underline">Sign up</a>
        </p>
      </div>
    </div>
  );
}
