import React from 'react';
import {
  AppWindow,
  Calendar,
  Check,
  Clock,
  Copy,
  Cpu,
  FileText,
  Lock,
  Sparkles,
  Trash2,
  X,
} from 'lucide-react';
import { Memory, SearchResult } from '../types';

interface MemoryDetailModalProps {
  item: Memory | SearchResult | null;
  onClose: () => void;
  onDelete: (id: string) => void;
}

export const MemoryDetailModal: React.FC<MemoryDetailModalProps> = ({
  item,
  onClose,
  onDelete,
}) => {
  const [copied, setCopied] = React.useState(false);

  if (!item) return null;

  const searchResult = item as SearchResult;
  const isSearch = 'score' in item;

  const dateObj = new Date(item.timestamp * 1000);
  const formattedDate = dateObj.toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
  const formattedTime = dateObj.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  const handleCopyText = () => {
    navigator.clipboard.writeText(item.extracted_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative flex max-h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl border border-[#2d3248] bg-[#12141c] shadow-2xl">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-[#282c3f] px-6 py-4 bg-[#141722]">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <AppWindow size={20} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-blue-400">
                  {item.application_name}
                </span>
                {item.is_demo && (
                  <span className="rounded bg-rose-600 px-1.5 py-0.5 text-[10px] font-bold text-white">
                    DEMO
                  </span>
                )}
                <span className="rounded bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-400 border border-emerald-500/20">
                  Stored Locally
                </span>
              </div>
              <h2 className="text-base font-semibold text-white truncate max-w-xl">
                {item.window_title}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onDelete(item.id)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-rose-300 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 transition-all"
            >
              <Trash2 size={14} />
              Delete Memory
            </button>
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-[#202434] hover:text-white transition-all"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Match Explanation Banner if Search */}
          {isSearch && (
            <div className="rounded-xl border border-blue-500/30 bg-blue-950/20 p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 text-sm font-semibold text-blue-400">
                  <Sparkles size={16} />
                  <span>Semantic Match Analysis</span>
                </div>
                <div className="flex items-center gap-3 text-xs">
                  <span className="text-slate-300">
                    Relevance Score: <strong>{Math.round(searchResult.score * 100)}%</strong>
                  </span>
                  <span className="text-blue-300">
                    Semantic: {Math.round(searchResult.semantic_score * 100)}%
                  </span>
                  <span className="text-emerald-300">
                    Keyword: {Math.round(searchResult.keyword_score * 100)}%
                  </span>
                </div>
              </div>
              <p className="text-xs text-slate-300">{searchResult.match_explanation}</p>
            </div>
          )}

          {/* Screenshot Preview */}
          <div className="overflow-hidden rounded-xl border border-[#282c3f] bg-[#090a0f]">
            <img
              src={item.screenshot_path}
              alt={item.window_title}
              className="w-full object-contain max-h-[460px] mx-auto"
            />
          </div>

          {/* Metadata & OCR Panels */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Extracted Text (2 cols) */}
            <div className="md:col-span-2 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400">
                  <FileText size={14} />
                  Extracted Screen Content (OCR)
                </h4>
                <button
                  onClick={handleCopyText}
                  className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                >
                  {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                  <span>{copied ? 'Copied!' : 'Copy Text'}</span>
                </button>
              </div>
              <div className="rounded-xl border border-[#24283b] bg-[#0b0c12] p-4 text-xs font-mono text-slate-200 whitespace-pre-wrap leading-relaxed max-h-56 overflow-y-auto">
                {item.extracted_text || 'No text extracted from this screen.'}
              </div>
            </div>

            {/* Technical Metadata (1 col) */}
            <div className="space-y-4 rounded-xl border border-[#24283b] bg-[#141722] p-4 text-xs">
              <h4 className="font-semibold text-white uppercase tracking-wider text-[11px] border-b border-[#282c3f] pb-2">
                Memory Details
              </h4>

              <div className="space-y-3 text-slate-300">
                <div>
                  <span className="text-slate-500 block text-[10px]">TIMESTAMP</span>
                  <div className="flex items-center gap-1.5 text-white font-medium mt-0.5">
                    <Calendar size={13} className="text-slate-400" />
                    <span>{formattedDate}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-400 text-[11px] mt-0.5">
                    <Clock size={12} />
                    <span>{formattedTime}</span>
                  </div>
                </div>

                <div>
                  <span className="text-slate-500 block text-[10px]">MEMORY ID</span>
                  <code className="text-[11px] text-blue-300">{item.id}</code>
                </div>

                <div>
                  <span className="text-slate-500 block text-[10px]">PRIVACY STATUS</span>
                  <div className="flex items-center gap-1 text-emerald-400 mt-0.5 font-medium">
                    <Lock size={12} />
                    <span>100% Local Device Storage</span>
                  </div>
                </div>

                {'ocr_latency_ms' in item && (
                  <div>
                    <span className="text-slate-500 block text-[10px]">PIPELINE LATENCY</span>
                    <div className="grid grid-cols-2 gap-2 mt-1">
                      <div className="rounded bg-[#0e1017] p-2 border border-[#202434]">
                        <span className="text-[10px] text-slate-400 block">OCR Latency</span>
                        <strong className="text-white">{(item as Memory).ocr_latency_ms} ms</strong>
                      </div>
                      <div className="rounded bg-[#0e1017] p-2 border border-[#202434]">
                        <span className="text-[10px] text-slate-400 block">Embedding</span>
                        <strong className="text-white">{(item as Memory).embedding_latency_ms} ms</strong>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
