import React from 'react';
import { AppWindow, Calendar, ExternalLink, Sparkles, Trash2 } from 'lucide-react';
import { Memory, SearchResult } from '../types';

interface MemoryCardProps {
  item: Memory | SearchResult;
  onOpen: (item: Memory | SearchResult) => void;
  onDelete?: (id: string, e: React.MouseEvent) => void;
  isSearchMatch?: boolean;
}

export const MemoryCard: React.FC<MemoryCardProps> = ({
  item,
  onOpen,
  onDelete,
  isSearchMatch = false,
}) => {
  const searchResult = item as SearchResult;
  const matchPct = isSearchMatch ? Math.round(searchResult.score * 100) : null;
  const semanticPct = isSearchMatch ? Math.round(searchResult.semantic_score * 100) : null;
  const keywordPct = isSearchMatch ? Math.round(searchResult.keyword_score * 100) : null;

  // Format timestamp
  const dateObj = new Date(item.timestamp * 1000);
  const formattedDate = dateObj.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
  const formattedTime = dateObj.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div
      onClick={() => onOpen(item)}
      className="group relative cursor-pointer overflow-hidden rounded-2xl border border-[#282c3f] bg-[#12141c] hover:border-blue-500/50 hover:bg-[#161924] transition-all duration-200 shadow-sm hover:shadow-xl hover:shadow-blue-900/10 flex flex-col"
    >
      {/* Top Screenshot Preview */}
      <div className="relative aspect-video w-full overflow-hidden bg-[#090a0f] border-b border-[#282c3f]">
        <img
          src={item.screenshot_path}
          alt={item.window_title}
          className="h-full w-full object-cover object-top transition-transform duration-300 group-hover:scale-105"
          onError={(e) => {
            // Fallback image if missing
            (e.target as HTMLImageElement).src =
              'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="225" viewBox="0 0 400 225"><rect width="400" height="225" fill="%23141722"/><text x="50%" y="50%" fill="%2364748b" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="14">Screenshot Not Loaded</text></svg>';
          }}
        />

        {/* DEMO DATA pill */}
        {item.is_demo && (
          <span className="absolute top-2.5 right-2.5 rounded-md bg-rose-600/90 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white shadow-sm backdrop-blur-sm">
            Demo Data
          </span>
        )}

        {/* Match score badge for search results */}
        {isSearchMatch && matchPct !== null && (
          <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5 rounded-lg bg-blue-600/90 px-2.5 py-1 text-xs font-bold text-white shadow-md backdrop-blur-md border border-blue-400/30">
            <Sparkles size={12} />
            <span>{matchPct}% Match</span>
          </div>
        )}

        {/* Quick action buttons */}
        <div className="absolute bottom-2 right-2 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
          {onDelete && (
            <button
              onClick={(e) => onDelete(item.id, e)}
              title="Delete memory"
              className="p-1.5 rounded-lg bg-red-600/80 hover:bg-red-600 text-white backdrop-blur-sm transition-all"
            >
              <Trash2 size={13} />
            </button>
          )}
          <div className="p-1.5 rounded-lg bg-blue-600/80 hover:bg-blue-600 text-white backdrop-blur-sm transition-all">
            <ExternalLink size={13} />
          </div>
        </div>
      </div>

      {/* Content Section */}
      <div className="flex flex-1 flex-col p-4">
        {/* App & Date Bar */}
        <div className="flex items-center justify-between gap-2 text-xs text-slate-400 mb-2">
          <div className="flex items-center gap-1.5 font-medium text-blue-400 truncate">
            <AppWindow size={14} className="shrink-0" />
            <span className="truncate">{item.application_name}</span>
          </div>
          <div className="flex items-center gap-1 shrink-0 text-slate-400 text-[11px]">
            <Calendar size={12} />
            <span>{formattedDate} • {formattedTime}</span>
          </div>
        </div>

        {/* Window Title */}
        <h3 className="text-sm font-semibold text-white line-clamp-1 group-hover:text-blue-300 transition-colors mb-2">
          {item.window_title}
        </h3>

        {/* Snippet */}
        <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed bg-[#0b0c12] p-2 rounded-lg border border-[#202434] mb-3">
          {isSearchMatch ? (searchResult.snippet || searchResult.extracted_text) : (item.extracted_text || 'No text extracted')}
        </p>

        {/* Match explanation footer if searching */}
        {isSearchMatch && searchResult.match_explanation && (
          <div className="mt-auto pt-2 border-t border-[#222638] text-[11px] text-slate-400 flex items-start gap-1.5">
            <span className="text-blue-400 font-semibold shrink-0">Why matched:</span>
            <span className="line-clamp-2">{searchResult.match_explanation}</span>
          </div>
        )}

        {/* Detailed score pills if search */}
        {isSearchMatch && semanticPct !== null && (
          <div className="mt-2 flex items-center gap-2 text-[10px] text-slate-400">
            <span className="rounded bg-[#1a1e2d] px-2 py-0.5 border border-[#2d3248]">
              Semantic: <strong className="text-blue-300">{semanticPct}%</strong>
            </span>
            <span className="rounded bg-[#1a1e2d] px-2 py-0.5 border border-[#2d3248]">
              Keyword: <strong className="text-emerald-300">{keywordPct}%</strong>
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
