import React from 'react';
import { Clock, Database, Globe, Power, ShieldCheck } from 'lucide-react';
import { CaptureStatus } from '../types';

interface CaptureControlProps {
  status: CaptureStatus | null;
  onToggleCapture: () => void;
  isLoading: boolean;
}

export const CaptureControl: React.FC<CaptureControlProps> = ({
  status,
  onToggleCapture,
  isLoading,
}) => {
  const isCapturing = status?.is_capturing ?? false;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-3 w-full">
      {/* Capture Switch Card */}
      <div className="rounded-2xl border border-[#282c3f] bg-[#12141c] p-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div
            className={`flex h-11 w-11 items-center justify-center rounded-xl transition-all ${
              isCapturing
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-md shadow-emerald-500/20'
                : 'bg-slate-800 text-slate-400 border border-slate-700'
            }`}
          >
            <Power size={20} className={isCapturing ? 'animate-pulse' : ''} />
          </div>
          <div>
            <p className="text-xs text-slate-400">Automatic Capture</p>
            <p className="text-sm font-bold text-white flex items-center gap-2">
              {isCapturing ? (
                <>
                  <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
                  <span className="text-emerald-400">ACTIVE ({status?.interval_seconds}s)</span>
                </>
              ) : (
                <span className="text-slate-400">OFF (Paused)</span>
              )}
            </p>
          </div>
        </div>

        <button
          onClick={onToggleCapture}
          disabled={isLoading}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            isCapturing
              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30 hover:bg-rose-500/30'
              : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30'
          }`}
        >
          {isCapturing ? 'Turn OFF' : 'Turn ON'}
        </button>
      </div>

      {/* Last Captured Card */}
      <div className="rounded-2xl border border-[#282c3f] bg-[#12141c] p-4 flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
          <Clock size={20} />
        </div>
        <div>
          <p className="text-xs text-slate-400">Last Captured</p>
          <p className="text-sm font-semibold text-white">
            {status?.last_captured_at || 'Awaiting trigger'}
          </p>
        </div>
      </div>

      {/* Memories Stored Card */}
      <div className="rounded-2xl border border-[#282c3f] bg-[#12141c] p-4 flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
          <Database size={20} />
        </div>
        <div>
          <p className="text-xs text-slate-400">Memories Stored</p>
          <p className="text-sm font-semibold text-white">
            {status?.total_memories.toLocaleString() ?? '0'} records
          </p>
        </div>
      </div>

      {/* Cloud Requests: 0 Card */}
      <div className="rounded-2xl border border-emerald-500/20 bg-emerald-950/10 p-4 flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
          <ShieldCheck size={20} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <p className="text-xs text-emerald-400 font-semibold">Zero-Cloud Guarantee</p>
          </div>
          <p className="text-sm font-bold text-white flex items-center gap-1.5">
            Cloud Requests: <span className="text-emerald-400">0</span>
          </p>
        </div>
      </div>
    </div>
  );
};
