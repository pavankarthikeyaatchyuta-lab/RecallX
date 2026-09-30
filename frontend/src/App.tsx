import React, { useEffect, useRef, useState } from 'react';
import { Navbar } from './components/Navbar';
import { MemoryDetailModal } from './components/MemoryDetailModal';
import { HomePage } from './pages/HomePage';
import { SearchPage } from './pages/SearchPage';
import { MemoriesPage } from './pages/MemoriesPage';
import { RuntimePage } from './pages/RuntimePage';
import { BenchmarkPage } from './pages/BenchmarkPage';
import { PrivacySettingsPage } from './pages/PrivacySettingsPage';
import {
  BenchmarkMetrics,
  CaptureStatus,
  HardwareInfo,
  Memory,
  PageId,
  RuntimeStatus,
  SearchResult,
  SettingsModel,
} from './types';
import * as api from './services/api';

export function App() {
  const [activePage, setActivePage] = useState<PageId>('home');
  const [captureStatus, setCaptureStatus] = useState<CaptureStatus | null>(null);
  const [hardwareInfo, setHardwareInfo] = useState<HardwareInfo | null>(null);
  const [runtimeStatus, setRuntimeStatus] = useState<RuntimeStatus | null>(null);
  const [benchmarkMetrics, setBenchmarkMetrics] = useState<BenchmarkMetrics | null>(null);
  const [settings, setSettings] = useState<SettingsModel | null>(null);

  const [memories, setMemories] = useState<Memory[]>([]);
  const [totalMemories, setTotalMemories] = useState(0);
  const [uniqueApps, setUniqueApps] = useState<string[]>([]);
  const [selectedAppFilter, setSelectedAppFilter] = useState('');

  const [isCapturingManual, setIsCapturingManual] = useState(false);
  const [isTogglingCapture, setIsTogglingCapture] = useState(false);
  const [isRefreshingMemories, setIsRefreshingMemories] = useState(false);

  const [searchInitialQuery, setSearchInitialQuery] = useState('');
  const [selectedMemoryForModal, setSelectedMemoryForModal] = useState<Memory | SearchResult | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const searchInputRef = useRef<HTMLInputElement | null>(null);

  // Show Toast
  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Load initial data
  const loadData = async () => {
    try {
      const [statusRes, hwRes, rtRes, memRes, setRes, bmRes] = await Promise.allSettled([
        api.fetchStatus(),
        api.fetchHardware(),
        api.fetchRuntime(),
        api.fetchMemories(50, 0, selectedAppFilter || undefined),
        api.fetchSettings(),
        api.fetchBenchmark(),
      ]);

      if (statusRes.status === 'fulfilled') setCaptureStatus(statusRes.value);
      if (hwRes.status === 'fulfilled') setHardwareInfo(hwRes.value);
      if (rtRes.status === 'fulfilled') setRuntimeStatus(rtRes.value);
      if (memRes.status === 'fulfilled') {
        setMemories(memRes.value.memories);
        setTotalMemories(memRes.value.total);
        setUniqueApps(memRes.value.unique_apps);
      }
      if (setRes.status === 'fulfilled') setSettings(setRes.value);
      if (bmRes.status === 'fulfilled') setBenchmarkMetrics(bmRes.value);
    } catch (e) {
      console.error('Failed to load initial data:', e);
    }
  };

  useEffect(() => {
    loadData();
    // Poll status every 6 seconds
    const interval = setInterval(async () => {
      try {
        const s = await api.fetchStatus();
        setCaptureStatus(s);
      } catch {}
    }, 6000);
    return () => clearInterval(interval);
  }, [selectedAppFilter]);

  // Global Keyboard Shortcut: Ctrl + Shift + Space
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.code === 'Space') {
        e.preventDefault();
        setActivePage('home');
        setTimeout(() => {
          searchInputRef.current?.focus();
        }, 100);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Quick manual capture
  const handleQuickCapture = async () => {
    setIsCapturingManual(true);
    try {
      const res = await api.triggerManualCapture();
      if (res.status === 'success' && res.memory) {
        showToast(`Memory captured: ${res.memory.application_name}`);
        await loadData();
      } else {
        showToast(res.message);
      }
    } catch (err) {
      showToast('Capture failed');
    } finally {
      setIsCapturingManual(false);
    }
  };

  // Toggle periodic capture
  const handleToggleCapture = async () => {
    if (!captureStatus) return;
    setIsTogglingCapture(true);
    try {
      let updated: CaptureStatus;
      if (captureStatus.is_capturing) {
        updated = await api.stopCapture();
        showToast('Periodic capture paused');
      } else {
        updated = await api.startCapture();
        showToast(`Periodic capture started (${updated.interval_seconds}s)`);
      }
      setCaptureStatus(updated);
    } catch (err) {
      showToast('Failed to toggle capture');
    } finally {
      setIsTogglingCapture(false);
    }
  };

  // Seed demo data
  const handleSeedDemo = async () => {
    try {
      const res = await api.seedDemoData();
      showToast(`Seeded ${res.count} realistic demo memories`);
      await loadData();
    } catch (err) {
      showToast('Failed to seed demo data');
    }
  };

  // Search submission from home page
  const handleHomeSearch = (query: string) => {
    setSearchInitialQuery(query);
    setActivePage('search');
  };

  // Delete single memory
  const handleDeleteMemory = async (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    try {
      await api.deleteMemory(id);
      showToast('Memory deleted');
      if (selectedMemoryForModal?.id === id) {
        setSelectedMemoryForModal(null);
      }
      await loadData();
    } catch (err) {
      showToast('Failed to delete memory');
    }
  };

  // Delete all memories
  const handleDeleteAllMemories = async () => {
    try {
      const res = await api.deleteAllMemories();
      showToast(`Purged ${res.deleted_count} memories`);
      setSelectedMemoryForModal(null);
      await loadData();
    } catch (err) {
      showToast('Failed to clear memories');
    }
  };

  // Save Settings
  const handleSaveSettings = async (newSettings: SettingsModel) => {
    const updated = await api.updateSettings(newSettings);
    setSettings(updated);
    showToast('Settings saved successfully');
  };

  // Run benchmark
  const handleRunBenchmark = async () => {
    const res = await api.runBenchmark();
    setBenchmarkMetrics(res);
    showToast('Benchmark run completed');
    return res;
  };

  return (
    <div className="min-h-screen bg-[#090a0f] text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* Navigation */}
      <Navbar
        activePage={activePage}
        onNavigate={setActivePage}
        onQuickCapture={handleQuickCapture}
        onSeedDemo={handleSeedDemo}
        isCapturingManual={isCapturingManual}
        totalMemories={totalMemories}
      />

      {/* Main Content Area */}
      <main className="flex-1 px-4 sm:px-6 lg:px-8 pt-6">
        {activePage === 'home' && (
          <HomePage
            onSearchSubmit={handleHomeSearch}
            onNavigate={setActivePage}
            onOpenMemory={setSelectedMemoryForModal}
            onDeleteMemory={handleDeleteMemory}
            captureStatus={captureStatus}
            onToggleCapture={handleToggleCapture}
            isTogglingCapture={isTogglingCapture}
            recentMemories={memories}
            searchRef={searchInputRef}
          />
        )}

        {activePage === 'search' && (
          <SearchPage
            initialQuery={searchInitialQuery}
            onExecuteSearch={api.executeSearch}
            uniqueApps={uniqueApps}
            onOpenMemory={setSelectedMemoryForModal}
            onDeleteMemory={handleDeleteMemory}
            searchRef={searchInputRef}
          />
        )}

        {activePage === 'memories' && (
          <MemoriesPage
            memories={memories}
            totalCount={totalMemories}
            uniqueApps={uniqueApps}
            selectedApp={selectedAppFilter}
            onSelectApp={setSelectedAppFilter}
            onRefresh={async () => {
              setIsRefreshingMemories(true);
              await loadData();
              setIsRefreshingMemories(false);
            }}
            onOpenMemory={setSelectedMemoryForModal}
            onDeleteMemory={handleDeleteMemory}
            onDeleteAll={handleDeleteAllMemories}
            isRefreshing={isRefreshingMemories}
          />
        )}

        {activePage === 'runtime' && (
          <RuntimePage
            hardware={hardwareInfo}
            runtime={runtimeStatus}
            onRefresh={loadData}
          />
        )}

        {activePage === 'benchmarks' && (
          <BenchmarkPage
            metrics={benchmarkMetrics}
            onRunBenchmark={handleRunBenchmark}
          />
        )}

        {activePage === 'privacy' && (
          <PrivacySettingsPage
            settings={settings}
            onSaveSettings={handleSaveSettings}
            onDeleteAllMemories={handleDeleteAllMemories}
            totalMemories={totalMemories}
          />
        )}
      </main>

      {/* Memory Detail Modal */}
      <MemoryDetailModal
        item={selectedMemoryForModal}
        onClose={() => setSelectedMemoryForModal(null)}
        onDelete={handleDeleteMemory}
      />

      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 rounded-xl border border-blue-500/30 bg-[#12141c]/95 px-4 py-2.5 text-xs font-medium text-white shadow-2xl backdrop-blur-md animate-in slide-in-from-bottom-3 duration-200">
          {toastMessage}
        </div>
      )}
    </div>
  );
}

export default App;
