import React, { useEffect, useState } from 'react';
import {
  Calendar,
  Clock,
  Filter,
  Layers,
  RotateCcw,
  Search,
  Sparkles,
} from 'lucide-react';
import { MemoryCard } from '../components/MemoryCard';
import { Memory, SearchResponse, SearchResult } from '../types';

interface SearchPageProps {
  initialQuery?: string;
  onExecuteSearch: (query: string, app?: string, dateFrom?: string, dateTo?: string) => Promise<SearchResponse>;
  uniqueApps: string[];
  onOpenMemory: (item: Memory | SearchResult) => void;
  onDeleteMemory: (id: string, e: React.MouseEvent) => void;
  searchRef?: React.RefObject<HTMLInputElement | null>;
}

export const SearchPage: React.FC<SearchPageProps> = ({
  initialQuery = '',
  onExecuteSearch,
  uniqueApps,
  onOpenMemory,
  onDeleteMemory,
  searchRef,
}) => {
  const [query, setQuery] = useState(initialQuery);
  const [selectedApp, setSelectedApp] = useState<string>('');
  const [dateFilter, setDateFilter] = useState<string>('all');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);

  const runSearch = async (targetQuery = query) => {
    if (!targetQuery.trim()) return;

    setIsSearching(true);
    let dateFrom: string | undefined;
    let dateTo: string | undefined;

    const today = new Date().toISOString().slice(0, 10);
    if (dateFilter === 'today') {
      dateFrom = today;
      dateTo = today;
    } else if (dateFilter === 'yesterday') {
      const y = new Date();
      y.setDate(y.getDate() - 1);
      const yStr = y.toISOString().slice(0, 10);
      dateFrom = yStr;
      dateTo = yStr;
    } else if (dateFilter === 'week') {
      const w = new Date();
      w.setDate(w.getDate() - 7);
      dateFrom = w.toISOString().slice(0, 10);
      dateTo = today;
    }

    try {
      const res = await onExecuteSearch(
        targetQuery.trim(),
        selectedApp || undefined,
        dateFrom,
        dateTo
      );
      setSearchResponse(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  };

  useEffect(() => {
    if (initialQuery) {
      setQuery(initialQuery);
      runSearch(initialQuery);
    }
  }, [initialQuery]);

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    runSearch();
  };

  return (
    <div className="space-y-6 pb-16 max-w-6xl mx-auto">
      {/* Search Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Semantic Memory Search</h1>
        <p className="text-xs text-slate-400">
          Query your captured screen history using natural language, topics, or exact text.
        </p>
      </div>

      {/* Main Search Controls */}
      <div className="rounded-2xl border border-[#282c3f] bg-[#12141c] p-4 sm:p-5 shadow-lg space-y-4">
        <form onSubmit={handleFormSubmit}>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400">
              <Search size={18} />
            </div>
            <input
              ref={searchRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. 'internship deadline', 'FastAPI endpoint', '₹50,000 expense', 'Qualcomm documentation'"
              className="w-full pl-11 pr-28 py-3 rounded-xl border border-[#2d3248] bg-[#0c0e15] text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 text-sm"
            />
            <button
              type="submit"
              disabled={isSearching}
              className="absolute right-2 top-2 bottom-2 px-4 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-all"
            >
              {isSearching ? (
                <>
                  <div className="h-3 w-3 rounded-full border-2 border-white border-t-transparent animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Sparkles size={13} />
                  <span>Find</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Filters Row */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-[#222638] text-xs">
          <div className="flex flex-wrap items-center gap-3">
            {/* App Filter */}
            <div className="flex items-center gap-1.5">
              <Layers size={14} className="text-slate-400" />
              <select
                value={selectedApp}
                onChange={(e) => {
                  setSelectedApp(e.target.value);
                  setTimeout(() => runSearch(), 50);
                }}
                className="rounded-lg border border-[#2d3248] bg-[#141722] px-2.5 py-1 text-slate-300 focus:outline-none focus:border-blue-500"
              >
                <option value="">All Applications</option>
                {uniqueApps.map((app) => (
                  <option key={app} value={app}>
                    {app}
                  </option>
                ))}
              </select>
            </div>

            {/* Date Filter */}
            <div className="flex items-center gap-1.5">
              <Calendar size={14} className="text-slate-400" />
              <select
                value={dateFilter}
                onChange={(e) => {
                  setDateFilter(e.target.value);
                  setTimeout(() => runSearch(), 50);
                }}
                className="rounded-lg border border-[#2d3248] bg-[#141722] px-2.5 py-1 text-slate-300 focus:outline-none focus:border-blue-500"
              >
                <option value="all">Any Date</option>
                <option value="today">Today</option>
                <option value="yesterday">Yesterday</option>
                <option value="week">Past 7 Days</option>
              </select>
            </div>
          </div>

          {/* Reset Filters */}
          {(selectedApp || dateFilter !== 'all') && (
            <button
              onClick={() => {
                setSelectedApp('');
                setDateFilter('all');
                setTimeout(() => runSearch(), 50);
              }}
              className="flex items-center gap-1 text-slate-400 hover:text-slate-200 transition-colors"
            >
              <RotateCcw size={12} />
              <span>Reset Filters</span>
            </button>
          )}
        </div>
      </div>

      {/* Results Section */}
      {searchResponse && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white">
                Found {searchResponse.total} matching memories
              </span>
              <span>for "{searchResponse.query}"</span>
            </div>
            <div className="flex items-center gap-1 rounded bg-[#141722] px-2 py-0.5 border border-[#242838]">
              <Clock size={11} />
              <span>Search Latency: <strong>{searchResponse.elapsed_ms} ms</strong></span>
            </div>
          </div>

          {searchResponse.results.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-[#282c3f] bg-[#10121a] p-12 text-center">
              <Search size={32} className="mx-auto text-slate-500 mb-2" />
              <h3 className="text-sm font-semibold text-slate-200">No Memories Matched Your Query</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
                Try broader keywords or clear application filters. RecallX performs hybrid semantic and keyword search.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {searchResponse.results.map((res) => (
                <MemoryCard
                  key={res.id}
                  item={res}
                  onOpen={onOpenMemory}
                  onDelete={onDeleteMemory}
                  isSearchMatch={true}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
