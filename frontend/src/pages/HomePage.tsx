import React, { useState } from 'react';
import { ArrowRight, Compass, Search, Shield, Sparkles } from 'lucide-react';
import { CaptureControl } from '../components/CaptureControl';
import { MemoryCard } from '../components/MemoryCard';
import { CaptureStatus, Memory, PageId, SearchResult } from '../types';

interface HomePageProps {
  onSearchSubmit: (query: string) => void;
  onNavigate: (page: PageId) => void;
  onOpenMemory: (item: Memory | SearchResult) => void;
  onDeleteMemory: (id: string, e: React.MouseEvent) => void;
  captureStatus: CaptureStatus | null;
  onToggleCapture: () => void;
  isTogglingCapture: boolean;
  recentMemories: Memory[];
  searchRef?: React.RefObject<HTMLInputElement | null>;
}

export const HomePage: React.FC<HomePageProps> = ({
  onSearchSubmit,
  onNavigate,
  onOpenMemory,
  onDeleteMemory,
  captureStatus,
  onToggleCapture,
  isTogglingCapture,
  recentMemories,
  searchRef,
}) => {
  const [query, setQuery] = useState('');

  const quickPrompts = [
    'Find the internship application with the September deadline',
    'Where did I see the Qualcomm AI Hub documentation?',
    'Find the document with the ₹50,000 amount',
    'Show me what I was looking at regarding Snapdragon NPU',
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearchSubmit(query.trim());
    }
  };

  const handleChipClick = (prompt: string) => {
    setQuery(prompt);
    onSearchSubmit(prompt);
  };

  return (
    <div className="space-y-10 pb-16">
      {/* Hero Section */}
      <section className="text-center pt-8 pb-4 max-w-3xl mx-auto space-y-4">
        <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-3 py-1 text-xs font-medium text-blue-300">
          <Sparkles size={13} className="text-blue-400" />
          <span>Snapdragon AI Lab Challenge 2026</span>
          <span className="text-slate-500">•</span>
          <span className="text-emerald-400">100% Local Intelligence</span>
        </div>

        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
          Your PC remembers, <br />
          <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-rose-400 bg-clip-text text-transparent">
            so you don't have to.
          </span>
        </h1>

        <p className="text-sm sm:text-base text-slate-400 max-w-xl mx-auto">
          Privacy-first visual memory for Windows. Recall past screens, websites, and documents
          instantly with semantic search — without cloud AI.
        </p>

        {/* Central Search Bar */}
        <form onSubmit={handleSubmit} className="pt-3 max-w-2xl mx-auto">
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 group-focus-within:text-blue-400 transition-colors">
              <Search size={20} />
            </div>
            <input
              ref={searchRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What are you trying to remember? (Ctrl + Shift + Space)"
              className="w-full pl-12 pr-28 py-4 rounded-2xl border border-[#2d3248] bg-[#12141c] text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/15 transition-all text-sm sm:text-base shadow-xl"
            />
            <button
              type="submit"
              className="absolute right-2.5 top-2.5 bottom-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-blue-600/30 transition-all hover:scale-102"
            >
              <span>Search</span>
              <ArrowRight size={14} />
            </button>
          </div>
        </form>

        {/* Quick Suggestion Chips */}
        <div className="pt-2 text-left max-w-2xl mx-auto">
          <p className="text-[11px] uppercase tracking-wider font-semibold text-slate-500 mb-2">
            Try searching for:
          </p>
          <div className="flex flex-wrap gap-2">
            {quickPrompts.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleChipClick(prompt)}
                className="text-xs text-slate-300 bg-[#141722] hover:bg-[#1e2232] hover:text-white px-3 py-1.5 rounded-lg border border-[#262a3c] transition-all text-left truncate max-w-full"
              >
                "{prompt}"
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Capture Status Bar */}
      <section className="max-w-6xl mx-auto">
        <CaptureControl
          status={captureStatus}
          onToggleCapture={onToggleCapture}
          isLoading={isTogglingCapture}
        />
      </section>

      {/* Recent Memories Section */}
      <section className="max-w-6xl mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white">Recent Memories</h2>
            <p className="text-xs text-slate-400">Captured and indexed locally on your device</p>
          </div>
          <button
            onClick={() => onNavigate('memories')}
            className="flex items-center gap-1 text-xs font-medium text-blue-400 hover:text-blue-300 transition-colors"
          >
            <span>View All Memories</span>
            <ArrowRight size={14} />
          </button>
        </div>

        {recentMemories.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-[#282c3f] bg-[#10121a] p-12 text-center">
            <Compass size={36} className="mx-auto text-slate-500 mb-3" />
            <h3 className="text-sm font-semibold text-slate-200">No Memories Recorded Yet</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-4">
              Capture your first screen with "Capture Now" above or load the realistic 16-sample demo dataset.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentMemories.slice(0, 6).map((mem) => (
              <MemoryCard
                key={mem.id}
                item={mem}
                onOpen={onOpenMemory}
                onDelete={onDeleteMemory}
              />
            ))}
          </div>
        )}
      </section>

      {/* Privacy Banner Footer */}
      <section className="max-w-6xl mx-auto rounded-2xl border border-[#282c3f] bg-gradient-to-r from-[#12141c] via-[#141824] to-[#12141c] p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Shield size={20} />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white">Core Privacy Architecture</h4>
            <p className="text-xs text-slate-400">
              Your screen history stays on your device. Zero external API calls, zero telemetry, zero analytics.
            </p>
          </div>
        </div>
        <button
          onClick={() => onNavigate('privacy')}
          className="shrink-0 px-4 py-2 rounded-xl text-xs font-semibold bg-[#1a1e2d] hover:bg-[#22273a] text-slate-200 border border-[#2d3248] transition-all"
        >
          Privacy Details & Exclusion Rules
        </button>
      </section>
    </div>
  );
};
