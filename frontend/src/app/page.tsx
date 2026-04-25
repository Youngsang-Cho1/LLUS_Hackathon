"use client";

import { Sparkles, CalendarDays, Search, X, ArrowRight, UploadCloud, Cpu, GraduationCap, ChevronDown } from "lucide-react";
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
  "Africana Studies",
  "American Studies",
  "Anthropology",
  "Art History",
  "Asian/Pacific/American Studies",
  "Biochemistry",
  "Biology",
  "Chemistry",
  "Cinema Studies",
  "Classics",
  "Comparative Literature",
  "Computer Science",
  "Computer Science and Data Science",
  "Computer Science and Mathematics",
  "Data Science",
  "Data Science and Mathematics",
  "Dramatic Literature",
  "East Asian Studies",
  "Economics",
  "Economics and Computer Science",
  "Economics and Mathematics",
  "Engineering",
  "English",
  "Environmental Studies",
  "European and Mediterranean Studies",
  "French",
  "Gender and Sexuality Studies",
  "German",
  "Global Public Health",
  "Hebrew and Judaic Studies",
  "History",
  "Iberian Studies",
  "International Relations",
  "Italian",
  "Journalism",
  "Language and Mind",
  "Latin American and Caribbean Studies",
  "Latino Studies",
  "Linguistics",
  "Mathematics",
  "Mathematics and Physics",
  "Metropolitan Studies",
  "Middle Eastern and Islamic Studies",
  "Music",
  "Neural Science",
  "Philosophy",
  "Physics",
  "Politics",
  "Psychology",
  "Public Policy",
  "Religion",
  "Romance Languages",
  "Russian and Slavic Studies",
  "Social and Cultural Analysis",
  "Sociology",
  "Spanish",
  "Urban Design and Architecture Studies"
];

const MINOR_DICTIONARY = [
  "Africana Studies",
  "American Studies",
  "Anthropology",
  "Art History",
  "Asian/Pacific/American Studies",
  "Biochemistry",
  "Biology",
  "Chemistry",
  "Cinema Studies",
  "Classics",
  "Comparative Literature",
  "Computer Science",
  "Computer Science and Data Science",
  "Computer Science and Mathematics",
  "Data Science",
  "Data Science and Mathematics",
  "Dramatic Literature",
  "East Asian Studies",
  "Economics",
  "Economics and Computer Science",
  "Economics and Mathematics",
  "Engineering",
  "English",
  "Environmental Studies",
  "European and Mediterranean Studies",
  "French",
  "Gender and Sexuality Studies",
  "German",
  "Global Public Health",
  "Hebrew and Judaic Studies",
  "History",
  "Iberian Studies",
  "International Relations",
  "Italian",
  "Journalism",
  "Language and Mind",
  "Latin American and Caribbean Studies",
  "Latino Studies",
  "Linguistics",
  "Mathematics",
  "Mathematics and Physics",
  "Metropolitan Studies",
  "Middle Eastern and Islamic Studies",
  "Music",
  "Neural Science",
  "Philosophy",
  "Physics",
  "Politics",
  "Psychology",
  "Public Policy",
  "Religion",
  "Romance Languages",
  "Russian and Slavic Studies",
  "Social and Cultural Analysis",
  "Sociology",
  "Spanish",
  "Urban Design and Architecture Studies",
  "Astronomy",
  "Business Studies",
  "Child and Adolescent Mental Health Studies",
  "Creative Writing",
  "Game Design",
  "Producing",
  "Studio Art",
  "Web Programming and Applications"
];

// --- 1. LANDING PAGE COMPONENT (Unauthenticated) ---
function LandingPage() {
  const router = useRouter();
  
  return (
    <div className="flex flex-col items-center justify-center min-h-[85vh] relative w-full">
      {/* Background Floating Elements */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[20%] left-[10%] w-32 h-10 bg-[var(--color-nyu-violet)]/20 rounded-full blur-xl animate-pulse"></div>
        <div className="absolute top-[60%] right-[15%] w-40 h-10 bg-blue-500/20 rounded-full blur-xl animate-pulse delay-1000"></div>
        
        {/* Floating chips to simulate courses */}
        <div className="absolute top-[15%] left-[20%] px-4 py-2 bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] rounded-full text-xs text-gray-400 opacity-60 transform -rotate-6 animate-bounce" style={{animationDuration: '4s'}}>
          CSCI-UA 101
        </div>
        <div className="absolute bottom-[25%] right-[25%] px-4 py-2 bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] rounded-full text-xs text-gray-400 opacity-60 transform rotate-12 animate-bounce" style={{animationDuration: '5s', animationDelay: '1s'}}>
          MATH-UA 120
        </div>
      </div>

      <div className="text-center z-10 max-w-4xl mx-auto px-4 mt-12 mb-20">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--color-nyu-violet-dark)] text-[var(--color-nyu-violet-light)] text-xs font-bold mb-8 border border-[var(--color-nyu-violet)]/50 tracking-wide uppercase shadow-[0_0_15px_rgba(87,6,140,0.5)]">
          <Sparkles size={14} /> The Future of Registration
        </div>
        
        <h1 className="text-5xl md:text-7xl font-extrabold mb-6 tracking-tighter text-white leading-tight">
          Smarter Scheduling,<br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-[var(--color-nyu-violet-light)] to-purple-400">
            Less Stress.
          </span>
        </h1>
        
        <p className="text-gray-400 text-lg md:text-xl max-w-2xl mx-auto mb-10 leading-relaxed">
          Upload your transcript and let our engine instantly map out your prerequisites. Generate the perfect, conflict-free schedule in seconds.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button 
            onClick={() => router.push("/login")}
            className="group flex items-center gap-2 bg-gradient-to-r from-[var(--color-nyu-violet-light)] to-[var(--color-nyu-violet)] px-10 py-4 rounded-full font-bold text-white shadow-[0_0_20px_rgba(87,6,140,0.6)] hover:shadow-[0_0_30px_rgba(87,6,140,0.8)] transition-all duration-300 hover:scale-105"
          >
            <span>Log In</span>
            <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </div>

      {/* Feature Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl w-full px-6 z-10">
        <div className="glass-panel p-8 rounded-2xl border-t border-t-[var(--color-nyu-violet)]/30 hover:-translate-y-2 transition-transform duration-300">
          <div className="bg-[var(--color-nyu-violet)]/20 w-12 h-12 rounded-xl flex items-center justify-center mb-6">
            <UploadCloud size={24} className="text-[var(--color-nyu-violet-light)]" />
          </div>
          <h3 className="text-xl font-bold text-white mb-3">Transcript Parsing</h3>
          <p className="text-sm text-gray-400 leading-relaxed">
            Drag and drop your unofficial transcript. Our system automatically extracts completed courses and clears prerequisites for you.
          </p>
        </div>

        <div className="glass-panel p-8 rounded-2xl border-t border-t-[var(--color-nyu-violet)]/30 hover:-translate-y-2 transition-transform duration-300 delay-100">
          <div className="bg-[var(--color-nyu-violet)]/20 w-12 h-12 rounded-xl flex items-center justify-center mb-6">
            <Cpu size={24} className="text-[var(--color-nyu-violet-light)]" />
          </div>
          <h3 className="text-xl font-bold text-white mb-3">Smart Engine</h3>
          <p className="text-sm text-gray-400 leading-relaxed">
            Specify your desired major, target credits, and must-have classes. We'll cross-reference Albert to build a conflict-free semester.
          </p>
        </div>

        <div className="glass-panel p-8 rounded-2xl border-t border-t-[var(--color-nyu-violet)]/30 hover:-translate-y-2 transition-transform duration-300 delay-200">
          <div className="bg-[var(--color-nyu-violet)]/20 w-12 h-12 rounded-xl flex items-center justify-center mb-6">
            <GraduationCap size={24} className="text-[var(--color-nyu-violet-light)]" />
          </div>
          <h3 className="text-xl font-bold text-white mb-3">Degree Tracking</h3>
          <p className="text-sm text-gray-400 leading-relaxed">
            Visually track your progress across Core Curriculum, Major, and Minor requirements all in one intuitive dashboard.
          </p>
        </div>
      </div>
    </div>
  );
}

// --- 2. SCHEDULE GENERATOR COMPONENT (Authenticated) ---
function ScheduleGenerator() {
  const router = useRouter();
  const [academicYear, setAcademicYear] = useState("Fall 2024");
  const [graduation, setGraduation] = useState("Spring 2026");
  const [targetCredits, setTargetCredits] = useState("16");

  const [majorInput, setMajorInput] = useState("");
  const [selectedMajor, setSelectedMajor] = useState("Computer Science");
  const [majorSuggestions, setMajorSuggestions] = useState<string[]>([]);
  const [showMajorDrop, setShowMajorDrop] = useState(false);

  const [minorInput, setMinorInput] = useState("");
  const [selectedMinor, setSelectedMinor] = useState("");
  const [minorSuggestions, setMinorSuggestions] = useState<string[]>([]);
  const [showMinorDrop, setShowMinorDrop] = useState(false);

  const [courseDescription, setCourseDescription] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [recommendedCourses, setRecommendedCourses] = useState<any[]>([]);
  const [wantedCourses, setWantedCourses] = useState<any[]>([]);

  useEffect(() => {
    if (majorInput.trim() === "") {
      setMajorSuggestions(MAJOR_DICTIONARY);
    } else {
      const lower = majorInput.toLowerCase();
      setMajorSuggestions(MAJOR_DICTIONARY.filter(m => m.toLowerCase().includes(lower)));
    }
  }, [majorInput]);

  useEffect(() => {
    if (minorInput.trim() === "") {
      setMinorSuggestions(MINOR_DICTIONARY);
    } else {
      const lower = minorInput.toLowerCase();
      setMinorSuggestions(MINOR_DICTIONARY.filter(m => m.toLowerCase().includes(lower)));
    }
  }, [minorInput]);

  const handleDiscoverCourses = async () => {
    if (!courseDescription.trim()) return;
    setIsSearching(true);
    try {
      const payload = {
        query: courseDescription,
        k: 10
      };

      const res = await fetch("http://localhost:8000/api/recommend", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      
      const mappedResults = (data.results || []).map((r: any) => ({
        code: r.course_code,
        title: r.title,
        description: r.description,
        score: r.score,
        timeSlot: { days: ["TBA"], startHour: 10, duration: 1.5, room: "TBA" },
        credits: 4
      }));
      setRecommendedCourses(mappedResults);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSearching(false);
    }
  };

  const addWantedCourse = (course: any) => {
    if (wantedCourses.length < 3 && !wantedCourses.find(c => c.code === course.code)) {
      setWantedCourses([...wantedCourses, course]);
    }
  };

  const removeWantedCourse = (code: string) => {
    setWantedCourses(wantedCourses.filter(c => c.code !== code));
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
      params.append("wanted", wantedCourses.map(c => c.code).join(","));
    }
    router.push(`/results?${params.toString()}`);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] w-full animate-in fade-in duration-500 mt-10">
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--color-nyu-violet-dark)] text-[var(--color-nyu-violet-light)] text-sm font-semibold mb-6 border border-[var(--color-nyu-violet)]">
          <Sparkles size={14} /> Semantic Course Search
        </div>
        <h1 className="text-4xl md:text-5xl font-bold mb-4 tracking-tight">
          Craft Your Perfect Semester
        </h1>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
          Tell us what you want to learn, and our system will recommend the best courses based on semantic similarity and fit them into a conflict-free schedule.
        </p>
      </div>

      <div className="w-full max-w-4xl glass-panel rounded-2xl p-8 md:p-12 relative overflow-visible shadow-2xl">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[80%] h-1 bg-gradient-to-r from-transparent via-[var(--color-nyu-violet)] to-transparent opacity-50"></div>
        
        <form onSubmit={handleGenerate}>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
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
                        <div className="flex flex-col gap-2 relative">
              <label className="text-xs font-semibold text-gray-400 tracking-wider uppercase">Academic Year</label>
              <div className="relative">
                <select 
                  value={academicYear}
                  onChange={(e) => setAcademicYear(e.target.value)}
                  className="w-full bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-nyu-violet)] appearance-none cursor-pointer"
                >
                  <option value="Fall 2024">Fall 2024</option>
                  <option value="Spring 2025">Spring 2025</option>
                  <option value="Fall 2025">Fall 2025</option>
                </select>
                <ChevronDown size={16} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
              </div>
            </div>

                        <div className="flex flex-col gap-2 relative">
              <label className="text-xs font-semibold text-gray-400 tracking-wider uppercase">Graduation</label>
              <div className="relative">
                <select 
                  value={graduation}
                  onChange={(e) => setGraduation(e.target.value)}
                  className="w-full bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-nyu-violet)] appearance-none cursor-pointer"
                >
                  <option value="Spring 2025">Spring 2025</option>
                  <option value="Fall 2025">Fall 2025</option>
                  <option value="Spring 2026">Spring 2026</option>
                  <option value="Fall 2026">Fall 2026</option>
                  <option value="Spring 2027">Spring 2027</option>
                  <option value="Spring 2028">Spring 2028</option>
                </select>
                <ChevronDown size={16} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
              </div>
            </div>

                        <div className="flex flex-col gap-2 relative">
              <label className="text-xs font-semibold text-gray-400 tracking-wider uppercase">Target Credits</label>
              <div className="relative">
                <select 
                  value={targetCredits}
                  onChange={(e) => setTargetCredits(e.target.value)}
                  className="w-full bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-nyu-violet)] appearance-none cursor-pointer"
                >
                  <option value="12">12 Credits</option>
                  <option value="14">14 Credits</option>
                  <option value="16">16 Credits</option>
                  <option value="18">18 Credits</option>
                </select>
                <ChevronDown size={16} className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
              </div>
            </div>
          </div>

          {/* Semantic Search Section */}
          <div className="mb-10 bg-[var(--color-dark-bg)] border border-[var(--color-glass-border)] p-6 rounded-xl">
            <label className="text-xs font-semibold text-[var(--color-nyu-violet-light)] tracking-wider uppercase mb-3 block flex items-center gap-2">
              <Sparkles size={14} /> Describe Your Interests
            </label>
            <p className="text-sm text-gray-400 mb-4">
              Not sure what to take? Just type what you want to learn (e.g., "I want to learn python, data analysis, and finance"). Our model will find the best matches.
            </p>
            
            <div className="flex flex-col gap-3">
              <textarea 
                value={courseDescription}
                onChange={(e) => setCourseDescription(e.target.value)}
                rows={3}
                placeholder="I want to learn about..."
                className="w-full bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-nyu-violet)] resize-none"
              />
              <button 
                type="button"
                onClick={handleDiscoverCourses}
                disabled={isSearching || !courseDescription.trim()}
                className="self-end bg-[var(--color-nyu-violet)] hover:bg-[var(--color-nyu-violet-light)] text-white px-6 py-2 rounded-lg text-sm font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isSearching ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div> : <Search size={16} />}
                Discover Courses
              </button>
            </div>

            {/* Recommendations Results */}
            {recommendedCourses.length > 0 && (
              <div className="mt-6 pt-6 border-t border-[var(--color-glass-border)]">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">Recommended Matches</h3>
                <div className="space-y-3">
                  {recommendedCourses.map((course) => {
                    const isAdded = wantedCourses.find(c => c.code === course.code);
                    return (
                      <div key={course.code} className="bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] p-4 rounded-lg flex flex-col md:flex-row justify-between items-start md:items-center gap-4 hover:border-[var(--color-nyu-violet)] transition-colors">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-bold text-white">{course.code}</span>
                            <span className="text-xs text-[var(--color-nyu-violet-light)] bg-[var(--color-nyu-violet)]/10 px-2 py-0.5 rounded-full border border-[var(--color-nyu-violet)]/30 font-bold">
                              {(course.score * 100).toFixed(0)}% Match
                            </span>
                          </div>
                          <p className="text-sm font-semibold text-gray-300 mb-1">{course.title}</p>
                          <p className="text-xs text-gray-500 line-clamp-2">{course.description}</p>
                        </div>
                        <button 
                          type="button"
                          onClick={() => isAdded ? removeWantedCourse(course.code) : addWantedCourse(course)}
                          className={`shrink-0 px-4 py-2 rounded-lg text-sm font-bold transition-all ${isAdded ? 'bg-[var(--color-glass)] text-gray-400 hover:text-red-400 border border-[var(--color-glass-border)]' : 'bg-transparent border border-[var(--color-nyu-violet-light)] text-[var(--color-nyu-violet-light)] hover:bg-[var(--color-nyu-violet)]/20'}`}
                        >
                          {isAdded ? "Remove" : "Add to Schedule"}
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {wantedCourses.length > 0 && (
              <div className="flex flex-wrap gap-3 mt-6">
                {wantedCourses.map(course => (
                  <div key={course.code} className="flex items-center gap-2 bg-[var(--color-nyu-violet)]/20 border border-[var(--color-nyu-violet)] text-[var(--color-nyu-violet-light)] px-3 py-1.5 rounded-full text-sm font-medium">
                    {course.code}
                    <button type="button" onClick={() => removeWantedCourse(course.code)} className="hover:text-white transition-colors">
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
    </div>
  );
}

// --- 3. MAIN PAGE ROUTER ---
export default function Home() {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      // Could also ping the backend here, but just checking token existence is fine for routing.
      // Header.tsx handles invalidating it if it's expired.
      setIsAuthenticated(true);
    } else {
      setIsAuthenticated(false);
    }
    setIsLoading(false);
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[80vh]">
        <div className="w-10 h-10 border-4 border-[var(--color-glass-border)] border-t-[var(--color-nyu-violet-light)] rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <>
      {isAuthenticated ? <ScheduleGenerator /> : <LandingPage />}
      
      {/* Universal Footer */}
      <footer className="mt-20 flex justify-center gap-6 text-sm text-gray-500 pb-10">
        <a href="#" className="hover:text-white transition-colors">About</a>
        <a href="#" className="hover:text-white transition-colors">Terms</a>
        <a href="#" className="hover:text-white transition-colors">Support</a>
        <span>© 2024 NYUSEARCH</span>
      </footer>
    </>
  );
}
