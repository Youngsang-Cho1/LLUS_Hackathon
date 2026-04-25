"use client";

import { Star, Clock, Calendar, Heart, Check, Plus } from "lucide-react";
import { useState } from "react";

export interface CourseData {
  id: string;
  code: string;
  title: string;
  department: string;
  professor: string;
  rating: number;
  difficulty: number;
  credits: number;
  schedule: string;
  term: string;
  description: string;
}

interface CourseCardProps {
  course: CourseData;
}

export default function CourseCard({ course }: CourseCardProps) {
  const [isSaved, setIsSaved] = useState(false);

  return (
    <div className={`glass-panel rounded-xl p-5 flex flex-col gap-4 relative group transition-all duration-300 ${isSaved ? 'border-[var(--color-nyu-violet)] shadow-[0_0_15px_rgba(87,6,140,0.3)]' : 'hover:border-[var(--color-nyu-violet-light)]'}`}>
      
      {/* Top Header */}
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-lg font-bold text-white group-hover:text-[var(--color-nyu-violet-light)] transition-colors">
            <span className="text-[var(--color-nyu-violet)] mr-2">{course.code}:</span>
            {course.title}
          </h3>
          <p className="text-xs text-gray-400 mt-1">{course.department}</p>
        </div>
        <button 
          onClick={() => setIsSaved(!isSaved)}
          className={`transition-colors ${isSaved ? 'text-red-500' : 'text-gray-500 hover:text-red-400'}`}
        >
          <Heart size={18} fill={isSaved ? "currentColor" : "none"} />
        </button>
      </div>

      {/* Professor & Rating */}
      <div className="flex justify-between items-center bg-[var(--color-dark-card)] rounded-lg p-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[var(--color-nyu-violet)] to-purple-400 flex items-center justify-center text-white font-bold text-xs">
            {course.professor.charAt(0)}
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider text-gray-500">Professor</p>
            <p className="text-sm font-medium text-gray-200">{course.professor}</p>
          </div>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1 text-[var(--color-nyu-violet-light)] font-bold">
            <Star size={14} fill="currentColor" />
            <span>{course.rating.toFixed(1)} <span className="text-xs text-gray-500 font-normal">/ 5</span></span>
          </div>
          <p className="text-[10px] text-gray-500 mt-0.5">RMP Score</p>
        </div>
      </div>

      {/* Difficulty Bar */}
      <div>
        <div className="flex justify-between text-xs mb-1.5">
          <span className="text-gray-400">Difficulty</span>
          <span className="text-gray-300 font-medium">{course.difficulty.toFixed(1)} / 5</span>
        </div>
        <div className="w-full bg-[var(--color-dark-card)] h-1.5 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-green-400 via-yellow-400 to-red-500 rounded-full" 
            style={{ width: `${(course.difficulty / 5) * 100}%` }}
          ></div>
        </div>
        <p className="text-[10px] text-gray-500 mt-1.5">
          {course.difficulty < 2.5 ? "Relatively Easy" : course.difficulty < 3.8 ? "Moderate" : "Challenging"}
        </p>
      </div>

      {/* Meta Info */}
      <div className="grid grid-cols-3 gap-2 text-xs text-gray-300 border-t border-[var(--color-glass-border)] pt-4 mt-2">
        <div>
          <p className="text-gray-500 text-[10px] uppercase mb-1">Credits</p>
          <p>{course.credits} Credits</p>
        </div>
        <div>
          <p className="text-gray-500 text-[10px] uppercase mb-1">Schedule</p>
          <p className="flex items-center gap-1"><Clock size={10} /> {course.schedule}</p>
        </div>
        <div>
          <p className="text-gray-500 text-[10px] uppercase mb-1">Term</p>
          <p className="flex items-center gap-1"><Calendar size={10} /> {course.term}</p>
        </div>
      </div>

      <p className="text-xs text-gray-400 line-clamp-2 mt-2 leading-relaxed">
        {course.description}
      </p>

      {/* Action Buttons */}
      <div className="flex gap-3 mt-2">
        <button className="flex-1 py-2 rounded-lg border border-[var(--color-glass-border)] text-sm font-medium hover:bg-[var(--color-glass)] transition-colors text-gray-300">
          View Details
        </button>
        <button 
          onClick={() => setIsSaved(!isSaved)}
          className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all duration-300 flex items-center justify-center gap-2 ${
            isSaved 
              ? 'bg-green-500/20 text-green-400 border border-green-500/50' 
              : 'bg-[var(--color-nyu-violet)] hover:bg-[var(--color-nyu-violet-light)] text-white shadow-[0_0_10px_rgba(87,6,140,0.4)]'
          }`}
        >
          {isSaved ? (
            <>
              <Check size={16} />
              Saved to List
            </>
          ) : (
            <>
              <Plus size={16} />
              Add to List
            </>
          )}
        </button>
      </div>
    </div>
  );
}
