"use client";

import { BookOpen, Calendar, Settings, UploadCloud, CheckCircle, AlertCircle, X, FileText } from "lucide-react";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadState, setUploadState] = useState<"idle" | "uploading" | "success">("idle");
  const [uploadError, setUploadError] = useState("");
  const [extractedCount, setExtractedCount] = useState(0);
  const [completedCourses, setCompletedCourses] = useState<string[]>([]);
  const [classesToTake, setClassesToTake] = useState<string[]>([]);

  useEffect(() => {
    const fetchUserData = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        router.push("/login");
        return;
      }
      
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${apiUrl}/api/user/me`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setCompletedCourses(data.completed_courses || []);
          setClassesToTake(data.classes_to_take || []);
        }
      } catch (err) {
        console.error("Failed to fetch user data", err);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchUserData();
  }, [router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[80vh]">
        <div className="w-10 h-10 border-4 border-[var(--color-glass-border)] border-t-[var(--color-nyu-violet-light)] rounded-full animate-spin"></div>
      </div>
    );
  }

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
    setUploadError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const token = localStorage.getItem("token");
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/user/transcript`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) throw new Error("Upload failed");
      const data = await res.json();
      setExtractedCount(data.added_courses?.length || 0);
      
      if (data.added_courses && data.added_courses.length > 0) {
        setCompletedCourses(prev => {
          const combined = [...prev, ...data.added_courses];
          return Array.from(new Set(combined));
        });
        
        // Re-fetch user data to get updated classes_to_take
        try {
          const resMe = await fetch(`${apiUrl}/api/user/me`, {
            headers: { "Authorization": `Bearer ${token}` }
          });
          if (resMe.ok) {
            const dataMe = await resMe.json();
            setClassesToTake(dataMe.classes_to_take || []);
          }
        } catch (e) {
          console.error("Failed to refresh user data", e);
        }
      }
      
      setUploadState("success");
    } catch (err) {
      console.error(err);
      setUploadError("Failed to upload transcript.");
      setUploadState("idle");
    }
  };

  const closeModal = () => {
    setShowUploadModal(false);
    setTimeout(() => setUploadState("idle"), 300);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] relative">
      <div className="w-full max-w-5xl glass-panel rounded-2xl p-8 md:p-12 relative overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[80%] h-1 bg-gradient-to-r from-transparent via-[var(--color-nyu-violet)] to-transparent opacity-50"></div>
        
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 border-b border-[var(--color-glass-border)] pb-6 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">My Dashboard</h1>
            <p className="text-gray-400">Manage your saved schedules and academic progress.</p>
          </div>
          <button 
            onClick={() => setShowUploadModal(true)}
            className="bg-[var(--color-nyu-violet)] hover:bg-[var(--color-nyu-violet-light)] text-white px-5 py-2.5 rounded-lg font-semibold flex items-center gap-2 shadow-[0_0_15px_rgba(87,6,140,0.4)] hover:shadow-[0_0_25px_rgba(87,6,140,0.6)] transition-all"
          >
            <UploadCloud size={18} />
            Update Transcript
          </button>
        </div>
        

        {/* Classes Taken Section */}
        <div className="mt-8 bg-[var(--color-dark-bg)] border border-[var(--color-glass-border)] rounded-xl p-6 md:p-8">
          <div className="flex items-center gap-3 mb-6 border-b border-[var(--color-glass-border)] pb-4">
            <div className="bg-[var(--color-nyu-violet)]/20 p-2 rounded-lg">
              <BookOpen className="text-[var(--color-nyu-violet-light)]" size={20} />
            </div>
            <h2 className="text-xl font-bold text-white">Classes Taken</h2>
          </div>
          
          {completedCourses.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {completedCourses.map((course, idx) => (
                <div key={idx} className="bg-[var(--color-dark-bg)] border border-[var(--color-glass-border)] rounded-lg p-4 flex items-center justify-between hover:border-[var(--color-nyu-violet)] transition-colors">
                  <span className="font-bold text-gray-200">{course}</span>
                  <CheckCircle size={16} className="text-green-500 opacity-80" />
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-10 text-center border-2 border-dashed border-[var(--color-glass-border)] rounded-xl">
              <FileText className="text-gray-600 mb-3" size={32} />
              <p className="text-gray-400 mb-1">No completed classes found.</p>
              <p className="text-sm text-gray-500">Upload your transcript to see your progress.</p>
            </div>
          )}
        </div>

        {/* Classes To Take Section */}
        <div className="mt-8 bg-[var(--color-dark-bg)] border border-[var(--color-glass-border)] rounded-xl p-6 md:p-8">
          <div className="flex items-center gap-3 mb-6 border-b border-[var(--color-glass-border)] pb-4">
            <div className="bg-orange-500/20 p-2 rounded-lg">
              <AlertCircle className="text-orange-400" size={20} />
            </div>
            <h2 className="text-xl font-bold text-white">Classes To Take</h2>
          </div>
          
          {classesToTake.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {classesToTake.map((course, idx) => (
                <div key={idx} className="bg-[var(--color-dark-bg)] border border-[var(--color-glass-border)] rounded-lg p-4 flex items-center justify-between hover:border-orange-500/50 transition-colors">
                  <span className="font-bold text-gray-200">{course}</span>
                  <div className="w-4 h-4 rounded-full border-2 border-orange-500/50"></div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-10 text-center border-2 border-dashed border-[var(--color-glass-border)] rounded-xl">
              <FileText className="text-gray-600 mb-3" size={32} />
              <p className="text-gray-400 mb-1">You have completed all requirements!</p>
              <p className="text-sm text-gray-500">Or we couldn't find your program track.</p>
            </div>
          )}
        </div>
      </div>

      {/* Upload Modal Overlay */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] rounded-2xl w-full max-w-2xl p-8 relative shadow-[0_0_50px_rgba(0,0,0,0.5)] animate-in zoom-in-95 duration-300">
            <button 
              onClick={closeModal}
              className="absolute top-6 right-6 text-gray-400 hover:text-white bg-[var(--color-dark-bg)] p-2 rounded-full transition-colors"
            >
              <X size={20} />
            </button>
            
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold mb-2 text-white">Upload Latest Transcript</h2>
              <p className="text-gray-400 text-sm">Keep your prerequisite profile up to date by uploading your newest unofficial transcript.</p>
            </div>

            <div 
              className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center transition-all duration-300
                ${isDragging ? 'border-[var(--color-nyu-violet-light)] bg-[var(--color-nyu-violet)]/10 scale-[1.02]' : 'border-[var(--color-glass-border)] hover:border-gray-500 hover:bg-[var(--color-glass)]'}
                ${uploadState === 'success' ? 'border-green-500 bg-green-500/10' : ''}
              `}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              {uploadState === "idle" && (
                <>
                  <div className="bg-[var(--color-dark-bg)] p-4 rounded-full shadow-lg mb-4">
                    <FileText size={32} className="text-[var(--color-nyu-violet-light)]" />
                  </div>
                  <h3 className="text-lg font-bold text-white mb-1">Drag & Drop your file here</h3>
                  <p className="text-xs text-gray-400 mb-6">Supports PDF, PNG, JPG</p>
                  {uploadError && (
                    <p className="text-xs text-red-400 mb-4">{uploadError}</p>
                  )}
                  <label className="bg-[var(--color-nyu-violet)] hover:bg-[var(--color-nyu-violet-light)] text-white px-6 py-2 rounded-lg font-semibold cursor-pointer shadow-[0_0_15px_rgba(87,6,140,0.4)] transition-all">
                    Browse Files
                    <input type="file" className="hidden" accept=".pdf,image/*" onChange={handleFileChange} />
                  </label>
                </>
              )}

              {uploadState === "uploading" && (
                <div className="flex flex-col items-center py-6">
                  <div className="w-12 h-12 border-4 border-[var(--color-glass-border)] border-t-[var(--color-nyu-violet-light)] rounded-full animate-spin mb-4"></div>
                  <h3 className="text-lg font-bold text-white mb-1">Analyzing Data...</h3>
                  <p className="text-xs text-[var(--color-nyu-violet-light)]">Extracting new courses added since last upload</p>
                </div>
              )}

              {uploadState === "success" && (
                <div className="flex flex-col items-center py-6">
                  <div className="bg-green-500/20 p-3 rounded-full mb-4">
                    <CheckCircle size={32} className="text-green-400" />
                  </div>
                  <h3 className="text-lg font-bold text-white mb-1">Profile Updated!</h3>
                  <p className="text-xs text-gray-400 mb-6 text-center">Found {extractedCount} new completed courses.</p>
                  
                  <button 
                    onClick={closeModal}
                    className="bg-green-600 hover:bg-green-500 text-white px-8 py-2 rounded-lg font-bold transition-all"
                  >
                    Done
                  </button>
                </div>
              )}
            </div>

            <div className="mt-6 flex items-start gap-3 p-3 rounded-lg bg-[var(--color-dark-bg)] border border-[var(--color-glass-border)]">
              <AlertCircle className="text-[var(--color-nyu-violet-light)] shrink-0 mt-0.5" size={16} />
              <p className="text-[11px] text-gray-400 leading-relaxed">
                We only extract course codes (e.g. CSCI-UA 101) to verify prerequisites. We do not store or process your grades, GPA, or any sensitive personal information.
              </p>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
