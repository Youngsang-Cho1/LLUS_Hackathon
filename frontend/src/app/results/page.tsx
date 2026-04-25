"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useState, useMemo, useEffect } from "react";
import { Calendar, Info, RefreshCw, Star, X, AlertTriangle, ArrowLeftRight, Settings2 } from "lucide-react";

// --- MOCK DATA ---

interface TimeSlot {
  days: string[];
  startHour: number;
  duration: number;
  room: string;
}

interface SchedCourse {
  id: string;
  slotKey: string;
  code: string;
  section: string;
  title: string;
  credits: number;
  timeSlot: TimeSlot;
  color: string;
  isWanted?: boolean;
}



const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"];
const HOURS = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18];

// --- LOGIC ---

function checkTimeConflict(altCourse: SchedCourse, currentSchedule: SchedCourse[], courseToReplaceId: string): boolean {
  for (const course of currentSchedule) {
    if (course.id === courseToReplaceId) continue;
    const sharedDays = course.timeSlot.days.some(day => altCourse.timeSlot.days.includes(day));
    if (sharedDays) {
      const altStart = altCourse.timeSlot.startHour;
      const altEnd = altStart + altCourse.timeSlot.duration;
      const curStart = course.timeSlot.startHour;
      const curEnd = curStart + course.timeSlot.duration;
      if (altStart < curEnd && altEnd > curStart) return true; 
    }
  }
  return false;
}

// --- COMPONENT ---

function ResultsContent() {
  const searchParams = useSearchParams();
  const credits = searchParams.get("targetCredits") || "16";
  const wantedQuery = searchParams.get("wanted") || "";
  const wantedList = wantedQuery.toLowerCase().split(",").map(s => s.trim()).filter(s => s.length > 0);

  const [catalog, setCatalog] = useState<Record<string, SchedCourse[]>>({});

  const [schedule, setSchedule] = useState<SchedCourse[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCourseId, setSelectedCourseId] = useState<string | null>(null);

  useEffect(() => {
    if (wantedList.length === 0) {
        setSchedule([]);
        setLoading(false);
        return;
    }
    
    const fetchSchedule = async () => {
        try {
            const courseCodes = wantedList.map(c => c.toUpperCase());
            const res = await fetch("http://localhost:8000/api/schedule/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ course_codes: courseCodes })
            });
            const data = await res.json();
            if (data.courses) {
                const colors = [
                  "bg-[var(--color-nyu-violet)] border-[var(--color-nyu-violet-light)]",
                  "bg-purple-900 border-purple-500",
                  "bg-indigo-900 border-indigo-500",
                  "bg-teal-900 border-teal-500",
                  "bg-blue-900 border-blue-500"
                ];

                const groupedByCode: Record<string, any[]> = {};
                data.courses.forEach((c: any) => {
                    if (!groupedByCode[c.code]) groupedByCode[c.code] = [];
                    groupedByCode[c.code].push(c);
                });
                
                const initialSchedule: SchedCourse[] = [];
                const newCatalog: Record<string, SchedCourse[]> = {};
                
                let courseIdx = 0;
                for (const code in groupedByCode) {
                    const sections = groupedByCode[code];
                    const color = colors[courseIdx % colors.length];
                    const slotKey = `slot_${code.replace(/[^a-zA-Z0-9]/g, '_')}`;
                    
                    const mappedSections: SchedCourse[] = sections.map((c: any, secIdx: number) => ({
                        id: `gen_${courseIdx}_${secIdx}`,
                        slotKey: slotKey,
                        code: c.code,
                        section: c.section,
                        title: c.title,
                        credits: c.credits,
                        timeSlot: c.timeSlot,
                        color: color,
                        isWanted: true
                    }));
                    
                    if (mappedSections.length > 0) {
                        initialSchedule.push(mappedSections[0]);
                    }
                    newCatalog[slotKey] = mappedSections;
                    courseIdx++;
                }
                
                setSchedule(initialSchedule);
                setCatalog(newCatalog);
            }
        } catch (e) {
            console.error("Failed to generate schedule:", e);
        } finally {
            setLoading(false);
        }
    };
    fetchSchedule();
  }, [wantedQuery]);

  // Filters State
  const [excludeMorning, setExcludeMorning] = useState(false);
  const [excludeEvening, setExcludeEvening] = useState(false);

  // Auto-Optimization Logic (Time only now)
  useEffect(() => {
    if (!excludeMorning && !excludeEvening) return;

    setSchedule(currentSchedule => {
      let newSchedule = [...currentSchedule];
      let changed = false;

      newSchedule = newSchedule.map(course => {
        const isMorning = course.timeSlot.startHour < 11;
        const isEvening = course.timeSlot.startHour >= 17;
        
        let needsSwap = false;
        if (excludeMorning && isMorning) needsSwap = true;
        if (excludeEvening && isEvening) needsSwap = true;

        if (needsSwap) {
          const options = catalog[course.slotKey] || [];
          let validOptions = options.filter(alt => {
             if (excludeMorning && alt.timeSlot.startHour < 11) return false;
             if (excludeEvening && alt.timeSlot.startHour >= 17) return false;
             return !checkTimeConflict(alt, newSchedule, course.id);
          });

          if (validOptions.length > 0) {
            const bestOption = validOptions[0];
            if (bestOption.id !== course.id) {
              changed = true;
              return { ...bestOption, isWanted: course.isWanted };
            }
          }
        }
        return course;
      });

      return changed ? newSchedule : currentSchedule;
    });
  }, [excludeMorning, excludeEvening, catalog]);

  // Metrics
  const totalCredits = schedule.reduce((sum, c) => sum + c.credits, 0);

  const selectedCourse = schedule.find(c => c.id === selectedCourseId);
  const rawAlternatives = selectedCourse 
    ? (catalog[selectedCourse.slotKey] || []).filter(c => c.id !== selectedCourse.id)
    : [];

  const handleSwap = (newCourse: SchedCourse) => {
    const isWantedSlot = selectedCourse?.isWanted;
    const courseToInsert = { ...newCourse, isWanted: isWantedSlot };
    setSchedule(prev => prev.map(c => c.id === selectedCourseId ? courseToInsert : c));
    setSelectedCourseId(newCourse.id);
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-120px)]">
      
      {/* Main Timetable Area */}
      <div className="flex-1 glass-panel rounded-2xl flex flex-col overflow-hidden relative">
        {loading && (
          <div className="absolute inset-0 z-50 bg-[var(--color-dark-bg)]/80 backdrop-blur-sm flex flex-col items-center justify-center">
             <RefreshCw size={32} className="animate-spin text-[var(--color-nyu-violet-light)] mb-4" />
             <p className="text-white font-bold tracking-wider">Generating optimal schedule...</p>
          </div>
        )}
        <div className="p-5 border-b border-[var(--color-glass-border)] bg-[var(--color-dark-card)]/50">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
            <div>
              <h1 className="text-xl font-bold text-white flex items-center gap-2">
                <Calendar size={20} className="text-[var(--color-nyu-violet-light)]" />
                Generated Weekly Timetable
              </h1>
              <p className="text-sm text-gray-400 mt-1">Total: {totalCredits} Credits (Target: {credits})</p>
            </div>
            
            <div className="bg-[var(--color-dark-bg)] border border-[var(--color-glass-border)] rounded-lg px-4 py-2 flex flex-col items-end">
              <span className="text-xs text-gray-400 font-semibold uppercase tracking-wider">Status</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-green-400">Conflict-Free</span>
              </div>
            </div>
          </div>

          {/* Auto-Optimization Filter Bar */}
          <div className="flex flex-wrap items-center gap-3 pt-3 border-t border-[var(--color-glass-border)]/50">
            <Settings2 size={16} className="text-gray-400" />
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider mr-2">Time Preferences:</span>
            
            <label className="flex items-center gap-2 text-sm text-gray-300 bg-[var(--color-dark-bg)] border border-[var(--color-glass-border)] px-3 py-1.5 rounded-full cursor-pointer hover:bg-[var(--color-nyu-violet)]/10 transition-colors">
              <input 
                type="checkbox" 
                checked={excludeMorning}
                onChange={(e) => setExcludeMorning(e.target.checked)}
                className="accent-[var(--color-nyu-violet-light)]"
              />
              No Mornings (&lt; 11 AM)
            </label>

            <label className="flex items-center gap-2 text-sm text-gray-300 bg-[var(--color-dark-bg)] border border-[var(--color-glass-border)] px-3 py-1.5 rounded-full cursor-pointer hover:bg-[var(--color-nyu-violet)]/10 transition-colors">
              <input 
                type="checkbox" 
                checked={excludeEvening}
                onChange={(e) => setExcludeEvening(e.target.checked)}
                className="accent-[var(--color-nyu-violet-light)]"
              />
              No Evenings (&gt; 5 PM)
            </label>
            
            {wantedList[0] !== "" && (
              <div className="ml-auto text-xs text-[var(--color-nyu-violet-light)] border border-[var(--color-nyu-violet)] bg-[var(--color-nyu-violet)]/10 px-3 py-1.5 rounded-full flex items-center gap-1">
                <Star size={12} fill="currentColor" /> Includes Interests
              </div>
            )}
          </div>
        </div>

        {/* Grid Container */}
        <div className="flex-1 overflow-auto relative p-4">
          <div className="min-w-[700px] h-full relative">
            <div className="grid grid-cols-5 ml-12 mb-4">
              {DAYS.map(day => (
                <div key={day} className="text-center text-sm font-semibold text-gray-400">{day}</div>
              ))}
            </div>

            <div className="relative h-[800px]">
              {HOURS.map((hour, i) => (
                <div key={hour} className="absolute w-full flex items-start" style={{ top: `${(i / (HOURS.length - 1)) * 100}%` }}>
                  <div className="w-12 text-xs text-gray-500 text-right pr-4 -mt-2">
                    {hour === 12 ? '12 PM' : hour > 12 ? `${hour - 12} PM` : `${hour} AM`}
                  </div>
                  <div className="flex-1 border-t border-[var(--color-glass-border)]/50"></div>
                </div>
              ))}

              {schedule.map(course => {
                return course.timeSlot.days.map((day, idx) => {
                  const dayIndex = DAYS.indexOf(day);
                  const startPercent = ((course.timeSlot.startHour - 8) / (18 - 8)) * 100;
                  const heightPercent = (course.timeSlot.duration / (18 - 8)) * 100;
                  const isSelected = selectedCourseId === course.id;
                  const hasConflict = checkTimeConflict(course, schedule, course.id);

                  const violatesMorning = excludeMorning && course.timeSlot.startHour < 11;
                  const violatesEvening = excludeEvening && course.timeSlot.startHour >= 17;
                  const hasViolation = violatesMorning || violatesEvening;

                  return (
                    <div 
                      key={`${course.id}-${idx}`}
                      onClick={() => setSelectedCourseId(course.id)}
                      className={`absolute rounded-lg border p-2 cursor-pointer transition-all duration-300 flex flex-col gap-1 overflow-hidden
                        ${course.color} 
                        ${isSelected ? 'ring-2 ring-white scale-[1.02] shadow-[0_0_20px_rgba(255,255,255,0.2)] z-20' : 'opacity-80 hover:opacity-100 hover:scale-[1.01] z-10'}
                        ${hasConflict ? 'bg-[repeating-linear-gradient(45deg,rgba(0,0,0,0.2),rgba(0,0,0,0.2)_10px,transparent_10px,transparent_20px)] border-red-500' : ''}
                        ${hasViolation && !hasConflict ? 'opacity-50 grayscale border-yellow-500' : ''}
                      `}
                      style={{
                        left: `calc(3rem + ${dayIndex * 20}%)`,
                        width: 'calc(20% - 8px)',
                        top: `${startPercent}%`,
                        height: `${heightPercent}%`,
                        marginLeft: '4px'
                      }}
                    >
                      <div className="flex justify-between items-start">
                        <h3 className="font-bold text-xs text-white leading-tight">
                          {course.code}<span className="text-[10px] text-[var(--color-glass-border)] ml-0.5">{course.section}</span>
                        </h3>
                        {course.isWanted && <Star size={10} className="text-yellow-400" fill="currentColor" />}
                      </div>
                      <p className="text-[10px] text-gray-200 leading-tight truncate">{course.title}</p>
                      <p className="text-[9px] text-gray-300 mt-auto">{course.timeSlot.room}</p>
                      
                      {hasViolation && !hasConflict && (
                        <div className="absolute inset-0 bg-yellow-500/20 flex items-center justify-center backdrop-blur-[1px]">
                          <span className="bg-black/80 text-yellow-400 text-[8px] font-bold px-1 py-0.5 rounded">Filter Violation</span>
                        </div>
                      )}
                    </div>
                  );
                });
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Sidebar: Alternatives */}
      <aside className={`w-full lg:w-[340px] shrink-0 glass-panel rounded-2xl flex flex-col overflow-hidden transition-all duration-300 ${selectedCourseId ? 'opacity-100 translate-x-0' : 'opacity-50 pointer-events-none'}`}>
        {selectedCourse ? (
          <>
            <div className="p-5 border-b border-[var(--color-glass-border)] bg-[var(--color-dark-card)] relative">
              <button 
                onClick={() => setSelectedCourseId(null)}
                className="absolute top-4 right-4 text-gray-400 hover:text-white"
              >
                <X size={16} />
              </button>
              <div className="flex items-center gap-2 mb-1">
                <p className="text-xs text-[var(--color-nyu-violet-light)] font-bold tracking-wider uppercase">Selected</p>
                {selectedCourse.isWanted && <span className="text-[10px] bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded uppercase font-bold tracking-wider">Matched Interest</span>}
              </div>
              <h2 className="text-xl font-bold text-white leading-tight">
                {selectedCourse.code} <span className="text-sm font-normal text-gray-400">Sec {selectedCourse.section}</span>
              </h2>
              <p className="text-sm text-gray-300 truncate">{selectedCourse.title}</p>
            </div>

            <div className="p-5 flex-1 overflow-y-auto">
              <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
                <RefreshCw size={14} /> 
                {selectedCourse.isWanted ? "Alternative Times" : "Alternative Fulfilling Courses"}
              </h3>

              {rawAlternatives.length > 0 ? (
                <div className="space-y-4">
                  {rawAlternatives.map((alt, i) => {
                    const isConflict = checkTimeConflict(alt, schedule, selectedCourse.id);

                    return (
                      <div 
                        key={alt.id} 
                        className={`bg-[var(--color-dark-bg)] border rounded-xl p-4 relative group transition-colors
                          ${isConflict ? 'border-red-500/50 bg-[repeating-linear-gradient(45deg,rgba(255,0,0,0.05),rgba(255,0,0,0.05)_10px,transparent_10px,transparent_20px)]' : 'border-[var(--color-glass-border)]'}
                        `}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <span className="text-sm text-white font-bold">{alt.code} <span className="text-gray-500 text-xs font-normal">Sec {alt.section}</span></span>
                        </div>
                        <p className={`text-xs mb-4 ${isConflict ? 'text-red-400 font-medium flex items-center gap-1' : 'text-gray-400'}`}>
                          {alt.timeSlot.days.join("/")} • {alt.timeSlot.startHour > 12 ? alt.timeSlot.startHour - 12 + " PM" : alt.timeSlot.startHour + " AM"} • {alt.timeSlot.room}
                          {isConflict && <><AlertTriangle size={12} /> Conflict</>}
                        </p>
                        
                        <button 
                          onClick={() => handleSwap(alt)}
                          className={`w-full flex items-center justify-center gap-2 py-2 rounded-lg border text-sm font-medium transition-all
                            ${isConflict 
                              ? 'bg-red-500/10 hover:bg-red-500/20 border-red-500/30 text-red-400' 
                              : 'bg-[var(--color-glass)] hover:bg-[var(--color-nyu-violet)] border-[var(--color-glass-border)] text-white'}
                          `}
                        >
                          <ArrowLeftRight size={14} />
                          {isConflict ? 'Swap Anyway (Resolve later)' : 'Swap to this Course'}
                        </button>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-10">
                  <p className="text-gray-500 text-sm">No alternative options available for this specific requirement.</p>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-gray-500">
            <Info size={48} className="mb-4 opacity-50" />
            <p>Select a course block on the timetable to view its details and explore alternatives.</p>
          </div>
        )}
      </aside>

    </div>
  );
}

export default function ResultsPage() {
  return (
    <Suspense fallback={<div className="text-center text-white py-20">Loading Schedule...</div>}>
      <ResultsContent />
    </Suspense>
  );
}
