import React, { useState } from 'react';
import {
  Clock,
  FolderOpen,
  HardDrive,
  Lock,
  Plus,
  Save,
  ShieldCheck,
  Sliders,
  Trash2,
  X,
} from 'lucide-react';
import { SettingsModel } from '../types';

interface PrivacySettingsPageProps {
  settings: SettingsModel | null;
  onSaveSettings: (settings: SettingsModel) => Promise<void>;
  onDeleteAllMemories: () => Promise<void>;
  totalMemories: number;
}

export const PrivacySettingsPage: React.FC<PrivacySettingsPageProps> = ({
  settings,
  onSaveSettings,
  onDeleteAllMemories,
  totalMemories,
}) => {
  const [formData, setFormData] = useState<SettingsModel | null>(settings);
  const [newExclusion, setNewExclusion] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  React.useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  if (!formData) return null;

  const handleAddExclusion = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newExclusion.trim()) return;
    const clean = newExclusion.trim();
    if (!formData.excluded_applications.includes(clean)) {
      setFormData({
        ...formData,
        excluded_applications: [...formData.excluded_applications, clean],
      });
    }
    setNewExclusion('');
  };

  const handleRemoveExclusion = (app: string) => {
    setFormData({
      ...formData,
      excluded_applications: formData.excluded_applications.filter((a) => a !== app),
    });
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSaveSettings(formData);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-8 pb-16 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Lock className="text-emerald-400" size={24} />
          <span>Privacy & Capture Controls</span>
        </h1>
        <p className="text-xs text-slate-400">
          RecallX is strictly local-first. Configure security barriers, application exclusions, and interval rules.
        </p>
      </div>

      {/* Privacy Architecture Status Banner */}
      <div className="rounded-2xl border border-emerald-500/20 bg-emerald-950/10 p-5 space-y-3">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <ShieldCheck className="text-emerald-400" size={18} />
          Zero-Cloud Local Guarantees
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-2.5 rounded-xl bg-[#0e1017] border border-[#202434]">
            <span className="text-slate-400 block text-[10px]">OCR PROCESSING</span>
            <strong className="text-emerald-400 block mt-0.5">100% Local (WinRT)</strong>
          </div>
          <div className="p-2.5 rounded-xl bg-[#0e1017] border border-[#202434]">
            <span className="text-slate-400 block text-[10px]">EMBEDDINGS</span>
            <strong className="text-emerald-400 block mt-0.5">Local (NPU / CPU)</strong>
          </div>
          <div className="p-2.5 rounded-xl bg-[#0e1017] border border-[#202434]">
            <span className="text-slate-400 block text-[10px]">CLOUD UPLOAD</span>
            <strong className="text-slate-300 block mt-0.5">Disabled (0 Packets)</strong>
          </div>
          <div className="p-2.5 rounded-xl bg-[#0e1017] border border-[#202434]">
            <span className="text-slate-400 block text-[10px]">VECTOR DATABASE</span>
            <strong className="text-emerald-400 block mt-0.5">Local SQLite + NPZ</strong>
          </div>
        </div>
      </div>

      {/* Capture Configuration Form */}
      <div className="rounded-2xl border border-[#282c3f] bg-[#12141c] p-6 space-y-6">
        <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-[#282c3f] pb-3">
          <Sliders className="text-blue-400" size={16} />
          Capture & Timing Settings
        </h3>

        {/* Capture Interval */}
        <div className="space-y-2">
          <div className="flex justify-between items-center text-xs">
            <label className="text-slate-200 font-medium">Automatic Capture Interval</label>
            <span className="text-blue-400 font-mono font-bold">
              {formData.capture_interval_seconds} seconds
            </span>
          </div>
          <input
            type="range"
            min={5}
            max={120}
            step={5}
            value={formData.capture_interval_seconds}
            onChange={(e) =>
              setFormData({
                ...formData,
                capture_interval_seconds: parseInt(e.target.value, 10),
              })
            }
            className="w-full accent-blue-500 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-slate-500">
            <span>5s (High frequency)</span>
            <span>30s (Default)</span>
            <span>120s (Low battery use)</span>
          </div>
        </div>

        {/* Excluded Applications Manager */}
        <div className="space-y-3 pt-2">
          <div>
            <label className="text-xs font-medium text-slate-200 block">
              Excluded Applications (Privacy Shield)
            </label>
            <p className="text-[11px] text-slate-400">
              Screens from these apps will be rejected automatically before storage or embedding.
            </p>
          </div>

          {/* Chips */}
          <div className="flex flex-wrap gap-2">
            {formData.excluded_applications.map((app) => (
              <span
                key={app}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs bg-[#1a1e2d] text-slate-200 border border-[#2e3348]"
              >
                <span>{app}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveExclusion(app)}
                  className="text-slate-400 hover:text-rose-400"
                >
                  <X size={12} />
                </button>
              </span>
            ))}
          </div>

          {/* Add Input */}
          <form onSubmit={handleAddExclusion} className="flex gap-2 max-w-sm">
            <input
              type="text"
              value={newExclusion}
              onChange={(e) => setNewExclusion(e.target.value)}
              placeholder="e.g. Chrome Incognito, Telegram"
              className="flex-1 px-3 py-1.5 rounded-lg border border-[#2d3248] bg-[#0c0e15] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
            <button
              type="submit"
              className="px-3 py-1.5 rounded-lg bg-[#202434] hover:bg-[#282d40] text-xs font-medium text-white flex items-center gap-1 transition-all"
            >
              <Plus size={13} />
              Add
            </button>
          </form>
        </div>

        {/* Save Button */}
        <div className="flex items-center justify-between pt-4 border-t border-[#222638]">
          <span className="text-xs text-emerald-400 font-medium">
            {saveSuccess && '✓ Settings saved successfully'}
          </span>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-500/20 transition-all"
          >
            <Save size={14} />
            <span>{isSaving ? 'Saving...' : 'Save Preferences'}</span>
          </button>
        </div>
      </div>

      {/* Data Storage & Wipe Card */}
      <div className="rounded-2xl border border-[#282c3f] bg-[#12141c] p-6 space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <HardDrive className="text-slate-400" size={16} />
          Local Storage Vault Management
        </h3>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-[#0c0e15] border border-[#222638] text-xs">
          <div>
            <p className="font-semibold text-white">Local Screenshot Directory</p>
            <code className="text-slate-400 text-[11px]">RecallX/data/screenshots/</code>
          </div>
          <span className="text-slate-400">
            {totalMemories} screenshots currently saved
          </span>
        </div>

        <div className="flex items-center justify-between pt-2">
          <div>
            <h4 className="text-xs font-semibold text-rose-400">Erase Memory Timeline</h4>
            <p className="text-[11px] text-slate-400">
              Permanently purges all captured screenshots, SQLite database records, and vector embeddings.
            </p>
          </div>
          <button
            onClick={() => setShowClearConfirm(true)}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-rose-600/10 hover:bg-rose-600/20 text-rose-300 border border-rose-500/30 transition-all"
          >
            Delete All Memories
          </button>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showClearConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-rose-500/30 bg-[#12141c] p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Trash2 className="text-rose-400" size={18} />
              Confirm Permanent Erasure
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Are you sure? This immediately deletes all screenshots and index entries from your device storage.
            </p>
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setShowClearConfirm(false)}
                className="px-4 py-2 rounded-xl text-xs font-medium text-slate-300 hover:bg-[#202434]"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  setShowClearConfirm(false);
                  await onDeleteAllMemories();
                }}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/30"
              >
                Yes, Purge Data
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
