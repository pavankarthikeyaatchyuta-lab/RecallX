import React, { useState } from 'react';
import { AppWindow, Database, Filter, Layers, RefreshCw, Trash2 } from 'lucide-react';
import { MemoryCard } from '../components/MemoryCard';
import { Memory, SearchResult } from '../types';

interface MemoriesPageProps {
  memories: Memory[];
  totalCount: number;
  uniqueApps: string[];
  selectedApp: string;
  onSelectApp: (app: string) => void;
  onRefresh: () => void;
  onOpenMemory: (item: Memory | SearchResult) => void;
  onDeleteMemory: (id: string, e: React.MouseEvent) => void;
  onDeleteAll: () => void;
  isRefreshing: boolean;
}

export const MemoriesPage: React.FC<MemoriesPageProps> = ({
  memories,
  totalCount,
  uniqueApps,
  selectedApp,
  onSelectApp,
  onRefresh,
  onOpenMemory,
  onDeleteMemory,
  onDeleteAll,
  isRefreshing,
}) => {
  const [showConfirmClear, setShowConfirmClear] = useState(false);

  return (
    <div className="space-y-6 pb-16 max-w-6xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Database size={22} className="text-blue-400" />
            <span>Memory Vault</span>
          </h1>
          <p className="text-xs text-slate-400">
            {totalCount.toLocaleString()} total memories captured and preserved locally.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#2d3248] bg-[#141722] text-xs font-medium text-slate-300 hover:text-white hover:bg-[#1e2232] transition-all"
          >
            <RefreshCw size={13} className={isRefreshing ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>

          {totalCount > 0 && (
            <button
              onClick={() => setShowConfirmClear(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rose-500/30 bg-rose-500/10 text-xs font-medium text-rose-300 hover:bg-rose-500/20 transition-all"
            >
              <Trash2 size={13} />
              <span>Clear All</span>
            </button>
          )}
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-2 pb-2 border-b border-[#222638]">
        <button
          onClick={() => onSelectApp('')}
          className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
            selectedApp === ''
              ? 'bg-blue-600 text-white'
              : 'bg-[#141722] text-slate-400 hover:text-slate-200'
          }`}
        >
          All ({totalCount})
        </button>
        {uniqueApps.map((app) => (
          <button
            key={app}
            onClick={() => onSelectApp(app)}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
              selectedApp === app
                ? 'bg-blue-600 text-white'
                : 'bg-[#141722] text-slate-400 hover:text-slate-200'
            }`}
          >
            {app}
          </button>
        ))}
      </div>

      {/* Memories Grid */}
      {memories.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[#282c3f] bg-[#10121a] p-16 text-center">
          <Database size={36} className="mx-auto text-slate-500 mb-2" />
          <h3 className="text-sm font-semibold text-slate-200">No Memories Found</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
            {selectedApp ? `No memories recorded under ${selectedApp}.` : 'Start capturing your screen to build your visual memory timeline.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {memories.map((mem) => (
            <MemoryCard
              key={mem.id}
              item={mem}
              onOpen={onOpenMemory}
              onDelete={onDeleteMemory}
            />
          ))}
        </div>
      )}

      {/* Clear All Confirmation Modal */}
      {showConfirmClear && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-rose-500/30 bg-[#12141c] p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Trash2 className="text-rose-400" size={18} />
              Confirm Permanent Memory Deletion
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              This will permanently delete all {totalCount} screenshots, SQLite metadata records, and local vector index entries. This action cannot be undone.
            </p>
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setShowConfirmClear(false)}
                className="px-4 py-2 rounded-xl text-xs font-medium text-slate-300 hover:bg-[#202434]"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowConfirmClear(false);
                  onDeleteAll();
                }}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/30"
              >
                Delete Everything
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
