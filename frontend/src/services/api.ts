import {
  BenchmarkMetrics,
  CaptureStatus,
  HardwareInfo,
  Memory,
  RuntimeStatus,
  SearchResponse,
  SettingsModel,
} from '../types';

const API_BASE = '/api';

export async function fetchHealth(): Promise<{ status: string; app: string; cloud_requests: number }> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function fetchStatus(): Promise<CaptureStatus> {
  const res = await fetch(`${API_BASE}/status`);
  return res.json();
}

export async function fetchHardware(): Promise<HardwareInfo> {
  const res = await fetch(`${API_BASE}/hardware`);
  return res.json();
}

export async function fetchRuntime(): Promise<RuntimeStatus> {
  const res = await fetch(`${API_BASE}/runtime`);
  return res.json();
}

export async function fetchMemories(
  limit = 50,
  offset = 0,
  app?: string,
  dateFrom?: string,
  dateTo?: string
): Promise<{ total: number; memories: Memory[]; unique_apps: string[] }> {
  const params = new URLSearchParams();
  params.set('limit', String(limit));
  params.set('offset', String(offset));
  if (app) params.set('app', app);
  if (dateFrom) params.set('date_from', dateFrom);
  if (dateTo) params.set('date_to', dateTo);

  const res = await fetch(`${API_BASE}/memories?${params.toString()}`);
  return res.json();
}

export async function fetchMemoryById(id: string): Promise<Memory> {
  const res = await fetch(`${API_BASE}/memories/${id}`);
  if (!res.ok) throw new Error('Memory not found');
  return res.json();
}

export async function triggerManualCapture(): Promise<{ status: string; message: string; memory: Memory | null }> {
  const res = await fetch(`${API_BASE}/capture`, { method: 'POST' });
  return res.json();
}

export async function startCapture(): Promise<CaptureStatus> {
  const res = await fetch(`${API_BASE}/capture/start`, { method: 'POST' });
  return res.json();
}

export async function stopCapture(): Promise<CaptureStatus> {
  const res = await fetch(`${API_BASE}/capture/stop`, { method: 'POST' });
  return res.json();
}

export async function executeSearch(
  query: string,
  application?: string,
  dateFrom?: string,
  dateTo?: string,
  limit = 20
): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      application: application || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      limit,
    }),
  });
  return res.json();
}

export async function fetchSettings(): Promise<SettingsModel> {
  const res = await fetch(`${API_BASE}/settings`);
  return res.json();
}

export async function updateSettings(settings: SettingsModel): Promise<SettingsModel> {
  const res = await fetch(`${API_BASE}/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  return res.json();
}

export async function deleteMemory(id: string): Promise<{ status: string; id: string }> {
  const res = await fetch(`${API_BASE}/memories/${id}`, { method: 'DELETE' });
  return res.json();
}

export async function deleteAllMemories(): Promise<{ status: string; deleted_count: number }> {
  const res = await fetch(`${API_BASE}/memories`, { method: 'DELETE' });
  return res.json();
}

export async function fetchBenchmark(): Promise<BenchmarkMetrics | null> {
  const res = await fetch(`${API_BASE}/benchmark`);
  return res.json();
}

export async function runBenchmark(): Promise<BenchmarkMetrics> {
  const res = await fetch(`${API_BASE}/benchmark/run`, { method: 'POST' });
  return res.json();
}

export async function seedDemoData(): Promise<{ status: string; count: number }> {
  const res = await fetch(`${API_BASE}/demo/seed`, { method: 'POST' });
  return res.json();
}
