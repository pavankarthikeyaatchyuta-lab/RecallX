import React from 'react';
import { Camera, Cpu, Database, Eye, Gauge, Home, Lock, Search, Sparkles } from 'lucide-react';
import { PageId } from '../types';

interface NavbarProps {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
  onQuickCapture: () => void;
  onSeedDemo: () => void;
  isCapturingManual: boolean;
  totalMemories: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  activePage,
  onNavigate,
  onQuickCapture,
  onSeedDemo,
  isCapturingManual,
  totalMemories,
}) => {
  const navItems: { id: PageId; label: string; icon: React.ReactNode }[] = [
    { id: 'home', label: 'Home', icon: <Home size={16} /> },
    { id: 'search', label: 'Search', icon: <Search size={16} /> },
    { id: 'memories', label: `Memories (${totalMemories})`, icon: <Database size={16} /> },
    { id: 'runtime', label: 'AI Runtime', icon: <Cpu size={16} /> },
    { id: 'benchmarks', label: 'Benchmarks', icon: <Gauge size={16} /> },
    { id: 'privacy', label: 'Privacy & Settings', icon: <Lock size={16} /> },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-[#282c3f] bg-[#0c0e15]/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div
            onClick={() => onNavigate('home')}
            className="flex cursor-pointer items-center gap-2 group"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-rose-500 shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform">
              <Eye size={20} className="text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold tracking-tight text-white">RecallX</span>
                <span className="flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-semibold text-emerald-400 border border-emerald-500/20">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  LOCAL
                </span>
              </div>
              <p className="text-[10px] text-slate-400">Zero-Cloud Visual Memory</p>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center gap-1 bg-[#141722] p-1 rounded-xl border border-[#282c3f]/80">
          {navItems.map((item) => {
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#1c202e]'
                }`}
              >
                {item.icon}
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={onSeedDemo}
            title="Seed 16 realistic demo scenarios"
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-purple-500/30 bg-purple-500/10 text-xs font-medium text-purple-300 hover:bg-purple-500/20 transition-all"
          >
            <Sparkles size={14} />
            Demo Dataset
          </button>

          <button
            onClick={onQuickCapture}
            disabled={isCapturingManual}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold shadow-md transition-all ${
              isCapturingManual
                ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:brightness-110 active:scale-95 shadow-blue-500/25'
            }`}
          >
            <Camera size={14} className={isCapturingManual ? 'animate-spin' : ''} />
            {isCapturingManual ? 'Capturing...' : 'Capture Now'}
          </button>
        </div>
      </div>
    </header>
  );
};
