"use client";

import { Sparkles, CalendarDays, Search, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState, useEffect } from "react";

// Mock Dictionary for Smart Search
const COURSE_DICTIONARY = [
  { code: "CSCI-UA 201", title: "Computer Systems Organization", tags: ["cso"] },
  { code: "CSCI-UA 310", title: "Basic Algorithms", tags: ["algo", "algorithms"] },
  { code: "CSCI-UA 480", title: "Special Topics: AI", tags: ["ai", "artificial intelligence"] },
  { code: "MATH-UA 120", title: "Discrete Mathematics", tags: ["discrete", "math"] },
];

const MAJOR_DICTIONARY = [
  "Computer Science",
  "Data Science",
  "Computer Science and Data Science",
  "Computer Science and Mathematics",
  "Biology",
  "Business",
  "Economics",
  "Mathematics",
  "Physics"
];

const MINOR_DICTIONARY = [
  "Web Programming and Applications",
  "Business Studies",
  "Mathematics",
  "Psychology",
  "Studio Art",
  "Data Science"
];

export default function Home() {
  const router = useRouter();
  
  // Basic settings
  const [academicYear, setAcademicYear] = useState("Fall 2024");
  const [graduation, setGraduation] = useState("Spring 2026");
  const [targetCredits, setTargetCredits] = useState("16");

  // Major Search State
  const [majorInput, setMajorInput] = useState("");
  const [selectedMajor, setSelectedMajor] = useState("Computer Science");
  const [majorSuggestions, setMajorSuggestions] = useState<string[]>([]);
  const [showMajorDrop, setShowMajorDrop] = useState(false);

  // Minor Search State
  const [minorInput, setMinorInput] = useState("");
  const [selectedMinor, setSelectedMinor] = useState("");
  const [minorSuggestions, setMinorSuggestions] = useState<string[]>([]);
  const [showMinorDrop, setShowMinorDrop] = useState(false);

  // Wanted Courses State
  const [wantedInput, setWantedInput] = useState("");
  const [wantedCourses, setWantedCourses] = useState<string[]>([]);
  const [courseSuggestions, setCourseSuggestions] = useState<typeof COURSE_DICTIONARY>([]);

  // Handle Major Search
  useEffect(() => {
    if (majorInput.trim() === "") {
      setMajorSuggestions(MAJOR_DICTIONARY);
    } else {
      const lower = majorInput.toLowerCase();
      setMajorSuggestions(MAJOR_DICTIONARY.filter(m => m.toLowerCase().includes(lower)));
    }
  }, [majorInput]);

  // Handle Minor Search
  useEffect(() => {
    if (minorInput.trim() === "") {
      setMinorSuggestions(MINOR_DICTIONARY);
    } else {
      const lower = minorInput.toLowerCase();
      setMinorSuggestions(MINOR_DICTIONARY.filter(m => m.toLowerCase().includes(lower)));
    }
  }, [minorInput]);

  // Handle Course Smart Search
  useEffect(() => {
    if (wantedInput.length > 1) {
      const lower = wantedInput.toLowerCase();
      const matches = COURSE_DICTIONARY.filter(c => 
        c.code.toLowerCase().includes(lower) || 
        c.title.toLowerCase().includes(lower) ||
        c.tags.some(tag => tag.includes(lower))
      );
      setCourseSuggestions(matches);
    } else {
      setCourseSuggestions([]);
    }
  }, [wantedInput]);

  const addWantedCourse = (code: string) => {
    if (wantedCourses.length < 2 && !wantedCourses.includes(code)) {
      setWantedCourses([...wantedCourses, code]);
    }
    setWantedInput("");
    setCourseSuggestions([]);
  };

  const removeWantedCourse = (code: string) => {
    setWantedCourses(wantedCourses.filter(c => c !== code));
  };

  const handleGenerate = (e: FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams({
      major: selectedMajor,
      minor: selectedMinor,
      academicYear,
      graduation,
      targetCredits,
    });
    if (wantedCourses.length > 0) {
      params.append("wanted", wantedCourses.join(","));
    }
    router.push(`/results?${params.toString()}`);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh]">
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--color-nyu-violet-dark)] text-[var(--color-nyu-violet-light)] text-sm font-semibold mb-6 border border-[var(--color-nyu-violet)]">
          <Sparkles size={14} /> AI-Powered Schedule Generator
        </div>
        <h1 className="text-4xl md:text-5xl font-bold mb-4 tracking-tight">
          Craft Your Perfect Semester
        </h1>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
          Let our intelligent engine resolve prerequisites and time conflicts to instantly generate the ultimate class schedule tailored just for you.
        </p>
      </div>

      <div className="w-full max-w-4xl glass-panel rounded-2xl p-8 md:p-12 relative overflow-visible">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[80%] h-1 bg-gradient-to-r from-transparent via-[var(--color-nyu-violet)] to-transparent opacity-50"></div>
        
        <form onSubmit={handleGenerate}>
          
          {/* Main Academics Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* Major Search */}
            <div className="flex flex-col gap-2 relative">
              <label className="text-xs font-semibold text-gray-400 tracking-wider uppercase">Major</label>
              <div className="relative">
                <input 
                  type="text" 
                  value={selectedMajor && !showMajorDrop ? selectedMajor : majorInput}
                  onChange={(e) => {
                    setMajorInput(e.target.value);
                    if (selectedMajor) setSelectedMajor("");
                    setShowMajorDrop(true);
                  }}
                  onFocus={() => setShowMajorDrop(true)}
                  onBlur={() => setTimeout(() => setShowMajorDrop(false), 200)}
                  placeholder="Search major..."
                  className="w-full bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-nyu-violet)] placeholder:text-gray-500"
                />
                {showMajorDrop && majorSuggestions.length > 0 && (
                  <div className="absolute top-full left-0 w-full mt-2 bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] rounded-lg shadow-xl z-50 max-h-48 overflow-y-auto">
                    {majorSuggestions.map(s => (
                      <div 
                        key={s} 
                        onClick={() => { setSelectedMajor(s); setMajorInput(""); setShowMajorDrop(false); }}
                        className="px-4 py-3 hover:bg-[var(--color-nyu-violet)]/20 cursor-pointer text-sm text-gray-300 transition-colors"
                      >
                        {s}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Minor Search */}
            <div className="flex flex-col gap-2 relative">
              <label className="text-xs font-semibold text-gray-400 tracking-wider uppercase">Minor (Optional)</label>
              <div className="relative">
                <input 
                  type="text" 
                  value={selectedMinor && !showMinorDrop ? selectedMinor : minorInput}
                  onChange={(e) => {
                    setMinorInput(e.target.value);
                    if (selectedMinor) setSelectedMinor("");
                    setShowMinorDrop(true);
                  }}
                  onFocus={() => setShowMinorDrop(true)}
                  onBlur={() => setTimeout(() => setShowMinorDrop(false), 200)}
                  placeholder="Search minor..."
                  className="w-full bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-nyu-violet)] placeholder:text-gray-500"
                />
                {showMinorDrop && minorSuggestions.length > 0 && (
                  <div className="absolute top-full left-0 w-full mt-2 bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] rounded-lg shadow-xl z-50 max-h-48 overflow-y-auto">
                    {minorSuggestions.map(s => (
                      <div 
                        key={s} 
                        onClick={() => { setSelectedMinor(s); setMinorInput(""); setShowMinorDrop(false); }}
                        className="px-4 py-3 hover:bg-[var(--color-nyu-violet)]/20 cursor-pointer text-sm text-gray-300 transition-colors"
                      >
                        {s}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold text-gray-400 tracking-wider uppercase">Academic Year</label>
              <select 
                value={academicYear}
                onChange={(e) => setAcademicYear(e.target.value)}
                className="bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-nyu-violet)] appearance-none cursor-pointer"
              >
                <option value="Fall 2024">Fall 2024</option>
                <option value="Spring 2025">Spring 2025</option>
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold text-gray-400 tracking-wider uppercase">Graduation</label>
              <select 
                value={graduation}
                onChange={(e) => setGraduation(e.target.value)}
                className="bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-nyu-violet)] appearance-none cursor-pointer"
              >
                <option value="Spring 2026">Spring 2026</option>
                <option value="Spring 2027">Spring 2027</option>
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold text-gray-400 tracking-wider uppercase">Target Credits</label>
              <select 
                value={targetCredits}
                onChange={(e) => setTargetCredits(e.target.value)}
                className="bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-nyu-violet)] appearance-none cursor-pointer text-white"
              >
                <option value="16">16 Credits (Standard)</option>
                <option value="18">18 Credits (Max)</option>
              </select>
            </div>
          </div>

          {/* Wanted Courses Section */}
          <div className="mb-10 bg-[var(--color-dark-bg)] border border-[var(--color-glass-border)] p-6 rounded-xl">
            <label className="text-xs font-semibold text-[var(--color-nyu-violet-light)] tracking-wider uppercase mb-3 block">
              Wanted Courses (Max 2)
            </label>
            <p className="text-xs text-gray-400 mb-4">Enter courses you absolutely must take. Try typing "cso" or "algo".</p>
            
            <div className="relative">
              <input 
                type="text" 
                value={wantedInput}
                onChange={(e) => setWantedInput(e.target.value)}
                disabled={wantedCourses.length >= 2}
                placeholder={wantedCourses.length >= 2 ? "Maximum 2 courses added." : "e.g. CSCI-UA 201 or 'cso'"}
                className="w-full bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] rounded-lg px-4 py-3 pl-10 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-nyu-violet)] disabled:opacity-50"
              />
              <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
              
              {/* Autocomplete Dropdown */}
              {courseSuggestions.length > 0 && (
                <div className="absolute top-full left-0 w-full mt-2 bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] rounded-lg shadow-xl z-50 overflow-hidden">
                  {courseSuggestions.map(s => (
                    <div 
                      key={s.code} 
                      onClick={() => addWantedCourse(s.code)}
                      className="px-4 py-3 hover:bg-[var(--color-nyu-violet)]/20 cursor-pointer text-sm text-gray-300 flex justify-between items-center transition-colors"
                    >
                      <span><strong className="text-white">{s.code}</strong>: {s.title}</span>
                      <span className="text-[10px] bg-gray-800 px-2 py-1 rounded text-gray-400">{s.tags[0]}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Selected Wanted Courses */}
            {wantedCourses.length > 0 && (
              <div className="flex gap-3 mt-4">
                {wantedCourses.map(course => (
                  <div key={course} className="flex items-center gap-2 bg-[var(--color-nyu-violet)]/20 border border-[var(--color-nyu-violet)] text-[var(--color-nyu-violet-light)] px-3 py-1.5 rounded-full text-sm font-medium">
                    {course}
                    <button type="button" onClick={() => removeWantedCourse(course)} className="hover:text-white transition-colors">
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex justify-center">
            <button 
              type="submit" 
              className="group relative flex items-center gap-2 bg-gradient-to-r from-[var(--color-nyu-violet-light)] to-[var(--color-nyu-violet)] px-8 py-4 rounded-full font-semibold text-white shadow-[0_0_20px_rgba(87,6,140,0.6)] hover:shadow-[0_0_30px_rgba(87,6,140,0.8)] transition-all duration-300 hover:scale-105"
            >
              <CalendarDays size={18} className="transition-transform group-hover:scale-110" />
              <span>Generate My Schedule</span>
            </button>
          </div>
        </form>
      </div>

      <footer className="absolute bottom-6 flex gap-6 text-sm text-gray-500">
        <a href="#" className="hover:text-white transition-colors">About</a>
        <a href="#" className="hover:text-white transition-colors">Terms</a>
        <a href="#" className="hover:text-white transition-colors">Support</a>
        <span>© 2024 NYUSched</span>
      </footer>
    </div>
  );
}
