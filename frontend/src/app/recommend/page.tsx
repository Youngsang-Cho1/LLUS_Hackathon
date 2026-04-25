"use client";

import { Search, Sparkles, BookOpen } from "lucide-react";
import { FormEvent, useState } from "react";

interface RecommendedCourse {
  course_code: string;
  subject_prefix: string;
  title: string;
  description: string;
  score: number;
}

export default function RecommendPage() {
  const [query, setQuery] = useState("");
  const [subject, setSubject] = useState("");
  const [results, setResults] = useState<RecommendedCourse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setError("");
    setIsLoading(true);
    setHasSearched(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const body: Record<string, unknown> = { query, k: 5 };
      if (subject.trim()) body.subject = subject.trim().toUpperCase();
      const res = await fetch(`${apiUrl}/api/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Recommendation failed");
      }
      const data = await res.json();
      setResults(data.results || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Recommendation failed");
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center min-h-[80vh] w-full">
      <div className="text-center mb-10 mt-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--color-nyu-violet-dark)] text-[var(--color-nyu-violet-light)] text-sm font-semibold mb-6 border border-[var(--color-nyu-violet)]">
          <Sparkles size={14} /> Semantic Course Search
        </div>
        <h1 className="text-4xl md:text-5xl font-bold mb-4 tracking-tight">
          Find courses by what you want to learn
        </h1>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
          Describe a topic in plain English. We&apos;ll match it against every CAS course description.
        </p>
      </div>

      <div className="w-full max-w-3xl glass-panel rounded-2xl p-8 mb-8">
        <form onSubmit={handleSearch} className="flex flex-col gap-4">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. machine learning applied to biology"
              className="w-full bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] rounded-lg pl-12 pr-4 py-4 text-base focus:outline-none focus:ring-2 focus:ring-[var(--color-nyu-violet)] placeholder:text-gray-500 text-white"
            />
            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
          </div>

          <div className="flex flex-col sm:flex-row gap-4 items-stretch sm:items-end">
            <div className="flex flex-col gap-2 flex-1">
              <label className="text-xs font-semibold text-gray-400 tracking-wider uppercase">Subject filter (optional)</label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="e.g. CSCI-UA"
                className="w-full bg-[var(--color-dark-card)] border border-[var(--color-glass-border)] rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-nyu-violet)] placeholder:text-gray-500 text-white"
              />
            </div>
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className={`px-8 py-3 rounded-lg font-semibold text-white transition-all
                ${isLoading || !query.trim()
                  ? 'bg-gray-600 cursor-not-allowed'
                  : 'bg-gradient-to-r from-[var(--color-nyu-violet-light)] to-[var(--color-nyu-violet)] shadow-[0_0_15px_rgba(87,6,140,0.5)] hover:shadow-[0_0_25px_rgba(87,6,140,0.7)]'}
              `}
            >
              {isLoading ? "Searching…" : "Search"}
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-4 bg-red-500/10 border border-red-500/50 text-red-400 text-sm px-4 py-3 rounded-lg">
            {error}
          </div>
        )}
      </div>

      <div className="w-full max-w-3xl space-y-4">
        {!hasSearched && (
          <p className="text-center text-gray-500 text-sm">Enter a description above to see top-5 matches.</p>
        )}
        {hasSearched && !isLoading && results.length === 0 && !error && (
          <p className="text-center text-gray-500 text-sm">No matches.</p>
        )}
        {results.map((c, i) => (
          <div
            key={c.course_code}
            className="glass-panel rounded-xl p-5 hover:border-[var(--color-nyu-violet-light)] transition-colors"
          >
            <div className="flex items-start justify-between gap-4 mb-2">
              <div className="flex items-center gap-3">
                <span className="text-xs font-bold text-gray-500 w-6">#{i + 1}</span>
                <BookOpen size={18} className="text-[var(--color-nyu-violet-light)] shrink-0" />
                <div>
                  <h3 className="text-base font-bold text-white">
                    <span className="text-[var(--color-nyu-violet-light)] mr-2">{c.course_code}</span>
                    {c.title}
                  </h3>
                  <p className="text-xs text-gray-500 mt-0.5">{c.subject_prefix}</p>
                </div>
              </div>
              <span className="shrink-0 text-xs font-mono bg-[var(--color-dark-bg)] border border-[var(--color-glass-border)] text-[var(--color-nyu-violet-light)] px-2 py-1 rounded">
                {c.score.toFixed(3)}
              </span>
            </div>
            {c.description && (
              <p className="text-sm text-gray-400 leading-relaxed mt-2 ml-9 line-clamp-3">
                {c.description}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
