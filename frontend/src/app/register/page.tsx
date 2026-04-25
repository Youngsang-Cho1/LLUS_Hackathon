"use client";

import { BookOpen, UploadCloud, CheckCircle, AlertCircle } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function RegisterPage() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);

  // Form State
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Upload State
  const [isDragging, setIsDragging] = useState(false);
  const [uploadState, setUploadState] = useState<"idle" | "uploading" | "success">("idle");
  const [extractedCount, setExtractedCount] = useState(0);

  const handleCreateAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      // 1. Register
      const resReg = await fetch("http://localhost:8000/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          email: email,
          password: password,
        }),
      });

      if (!resReg.ok) {
        const data = await resReg.json();
        throw new Error(data.detail || "Registration failed");
      }

      // 2. Login immediately to get token
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const resLogin = await fetch("http://localhost:8000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
      });

      if (!resLogin.ok) throw new Error("Auto-login failed after registration");

      const data = await resLogin.json();
      localStorage.setItem("token", data.access_token);
      
      setStep(2);

    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await uploadTranscript(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      await uploadTranscript(e.target.files[0]);
    }
  };

  const uploadTranscript = async (file: File) => {
    setUploadState("uploading");
    
    try {
      const formData = new FormData();
      formData.append("file", file);

      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:8000/api/user/transcript", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData,
      });

      if (!res.ok) throw new Error("Upload failed");
      
      const data = await res.json();
      setExtractedCount(data.added_courses?.length || 0);
      setUploadState("success");

    } catch (err) {
      console.error(err);
      alert("Failed to upload transcript.");
      setUploadState("idle");
    }
  };

  const handleFinish = () => {
    window.location.href = "/";
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh]">
      <div className={`w-full glass-panel rounded-2xl p-8 md:p-12 relative overflow-hidden transition-all duration-500 ${step === 1 ? 'max-w-md' : 'max-w-2xl'}`}>
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[80%] h-1 bg-gradient-to-r from-transparent via-[var(--color-nyu-violet)] to-transparent opacity-50"></div>
        
        {/* Step Indicator */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <div className={`w-2.5 h-2.5 rounded-full ${step === 1 ? 'bg-[var(--color-nyu-violet-light)] shadow-[0_0_10px_rgba(138,43,226,0.8)]' : 'bg-[var(--color-nyu-violet-dark)]'}`}></div>
          <div className="w-8 h-1 rounded-full bg-[var(--color-glass-border)] overflow-hidden">
            <div className={`h-full bg-[var(--color-nyu-violet-light)] transition-all duration-500 ${step === 2 ? 'w-full' : 'w-0'}`}></div>
          </div>
          <div className={`w-2.5 h-2.5 rounded-full ${step === 2 ? 'bg-[var(--color-nyu-violet-light)] shadow-[0_0_10px_rgba(138,43,226,0.8)]' : 'bg-[var(--color-nyu-violet-dark)]'}`}></div>
        </div>

        {/* STEP 1: Account Info */}
        {step === 1 && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex flex-col items-center mb-8">
              <div className="bg-[var(--color-nyu-violet)] p-3 rounded-xl shadow-[0_0_15px_rgba(87,6,140,0.8)] mb-4">
                <BookOpen size={28} className="text-white" />
              </div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Create an Account</h1>
              <p className="text-gray-400 text-sm mt-1">Join NYUSearch and optimize your semester</p>
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/50 text-red-400 text-sm px-4 py-3 rounded-lg mb-6">
                {error}
              </div>
            )}

            <form onSubmit={handleCreateAccount} className="flex flex-col gap-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-semibold text-gray-400 tracking-wider uppercase">First Name</label>
                  <input 
                    type="text" 
                    required
                    value={firstName}
                    onChange={e => setFirstName(e.target.value)}
                    placeholder="John"
                    className="w-full bg-[var(--color-dark-bg)] border border-[var(--color-glass-border)] rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-nyu-violet)] text-white placeholder:text-gray-600"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-semibold text-gray-400 tracking-wider uppercase">Last Name</label>
                  <input 
                    type="text" 
                    required
                    value={lastName}
                    onChange={e => setLastName(e.target.value)}
                    placeholder="Doe"
                    className="w-full bg-[var(--color-dark-bg)] border border-[var(--color-glass-border)] rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-nyu-violet)] text-white placeholder:text-gray-600"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-xs font-semibold text-gray-400 tracking-wider uppercase">Email Address</label>
                <input 
                  type="email" 
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="netid@nyu.edu"
                  className="w-full bg-[var(--color-dark-bg)] border border-[var(--color-glass-border)] rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-nyu-violet)] text-white placeholder:text-gray-600"
                />
              </div>
              
              <div className="flex flex-col gap-2 mb-2">
                <label className="text-xs font-semibold text-gray-400 tracking-wider uppercase">Password</label>
                <input 
                  type="password" 
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
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
                {isLoading ? 'Creating Account...' : 'Continue to Step 2'}
              </button>
            </form>

            <p className="text-center text-sm text-gray-400 mt-8">
              Already have an account? <a href="/login" className="text-[var(--color-nyu-violet-light)] font-bold hover:underline">Log in</a>
            </p>
          </div>
        )}

        {/* STEP 2: Transcript Upload */}
        {step === 2 && (
          <div className="animate-in fade-in slide-in-from-right-8 duration-500">
            <div className="text-center mb-8">
              <h2 className="text-2xl md:text-3xl font-bold mb-3 tracking-tight text-white">
                Upload Your Transcript
              </h2>
              <p className="text-gray-400 max-w-lg mx-auto text-sm md:text-base">
                Drag and drop your unofficial transcript (PDF or Image). Our AI will instantly parse your course history and set up your prerequisite profile.
              </p>
            </div>

            <div 
              className={`border-2 border-dashed rounded-2xl p-10 md:p-12 flex flex-col items-center justify-center transition-all duration-300
                ${isDragging ? 'border-[var(--color-nyu-violet-light)] bg-[var(--color-nyu-violet)]/10 scale-[1.02]' : 'border-[var(--color-glass-border)] hover:border-gray-500 hover:bg-white/5'}
                ${uploadState === 'success' ? 'border-green-500 bg-green-500/10' : ''}
              `}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              {uploadState === "idle" && (
                <>
                  <div className="bg-[var(--color-dark-bg)] p-4 rounded-full shadow-lg mb-6">
                    <UploadCloud size={36} className="text-[var(--color-nyu-violet-light)]" />
                  </div>
                  <h3 className="text-lg font-bold text-white mb-2">Drag & Drop your file here</h3>
                  <p className="text-sm text-gray-400 mb-6">Supports PDF, PNG, JPG (Max 10MB)</p>
                  
                  <div className="flex gap-4">
                    <button 
                      onClick={handleFinish}
                      className="px-6 py-2.5 rounded-full font-medium border border-[var(--color-glass-border)] text-gray-300 hover:bg-[var(--color-glass)] transition-colors"
                    >
                      Skip for Now
                    </button>
                    <label className="bg-[var(--color-nyu-violet)] hover:bg-[var(--color-nyu-violet-light)] text-white px-6 py-2.5 rounded-full font-bold cursor-pointer shadow-[0_0_15px_rgba(87,6,140,0.5)] transition-all">
                      Browse Files
                      <input type="file" className="hidden" accept=".pdf,image/*" onChange={handleFileChange} />
                    </label>
                  </div>
                </>
              )}

              {uploadState === "uploading" && (
                <div className="flex flex-col items-center py-6">
                  <div className="w-14 h-14 border-4 border-[var(--color-glass-border)] border-t-[var(--color-nyu-violet-light)] rounded-full animate-spin mb-6"></div>
                  <h3 className="text-lg font-bold text-white mb-2">Extracting Course Data...</h3>
                  <p className="text-sm text-[var(--color-nyu-violet-light)]">Using Vision AI to parse your transcript</p>
                </div>
              )}

              {uploadState === "success" && (
                <div className="flex flex-col items-center py-6">
                  <div className="bg-green-500/20 p-4 rounded-full mb-6">
                    <CheckCircle size={36} className="text-green-400" />
                  </div>
                  <h3 className="text-lg font-bold text-white mb-2">Extraction Complete!</h3>
                  <p className="text-sm text-gray-400 mb-8 text-center max-w-sm">We successfully found {extractedCount} completed courses. Your prerequisite profile is now up to date.</p>
                  
                  <button 
                    onClick={handleFinish}
                    className="bg-[var(--color-nyu-violet)] hover:bg-[var(--color-nyu-violet-light)] text-white px-8 py-3 rounded-full font-bold shadow-[0_0_15px_rgba(87,6,140,0.5)] transition-all"
                  >
                    Go to Home
                  </button>
                </div>
              )}
            </div>

            <div className="mt-6 flex items-start gap-3 p-4 rounded-xl bg-blue-500/10 border border-[var(--color-nyu-violet)]/20">
              <AlertCircle className="text-[var(--color-nyu-violet-light)] shrink-0 mt-0.5" size={18} />
              <div>
                <h4 className="text-sm font-bold text-white mb-1">Privacy First</h4>
                <p className="text-xs text-gray-400 leading-relaxed">Your transcript data is processed locally and immediately discarded after extracting course codes. We never store your grades or personal identifying information.</p>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
