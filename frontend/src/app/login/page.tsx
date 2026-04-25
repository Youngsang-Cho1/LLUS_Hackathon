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

        <div className="mt-6 flex items-center justify-between text-sm text-gray-500">
          <span className="w-1/3 border-b border-[var(--color-glass-border)]"></span>
          <span className="text-xs uppercase tracking-wider">or</span>
          <span className="w-1/3 border-b border-[var(--color-glass-border)]"></span>
        </div>

        <button className="w-full mt-6 flex items-center justify-center gap-3 bg-[var(--color-dark-bg)] border border-[var(--color-glass-border)] py-3 rounded-lg text-sm font-medium text-gray-300 hover:bg-[var(--color-glass)] transition-colors">
          <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" className="css-i6dzq1"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
          Continue with GitHub
        </button>

        <p className="text-center text-sm text-gray-400 mt-8">
          Don't have an account? <a href="/register" className="text-[var(--color-nyu-violet-light)] font-bold hover:underline">Sign up</a>
        </p>
      </div>
    </div>
  );
}
