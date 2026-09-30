export interface Memory {
  id: string;
  timestamp: number;
  iso_timestamp: string;
  screenshot_path: string;
  extracted_text: string;
  application_name: string;
  window_title: string;
  ocr_latency_ms: number;
  embedding_latency_ms: number;
  ocr_status?: string;
  is_demo: boolean;
  created_at: string;
}

export interface SearchResult {
  id: string;
  screenshot_path: string;
  timestamp: number;
  iso_timestamp: string;
  extracted_text: string;
  snippet: string;
  application_name: string;
  window_title: string;
  score: number;
  semantic_score: number;
  keyword_score: number;
  recency_score: number;
  match_explanation: string;
  is_demo: boolean;
}

export interface SearchResponse {
  query: string;
  total: number;
  elapsed_ms: number;
  results: SearchResult[];
}

export interface HardwareInfo {
  os: string;
  os_version: string;
  processor: string;
  machine: string;
  total_ram_gb: number;
  available_ram_gb: number;
  is_snapdragon: boolean;
  execution_providers: string[];
  qnn_available: boolean;
  cuda_available: boolean;
  active_runtime: string;
  acceleration_status: string;
  runtime_state?: string;
  cloud_requests: number;
}

export interface RuntimeStatus {
  active_model: string;
  active_runtime: string;
  active_device: string;
  active_provider_name: string;
  dimension: number;
  is_npu_active: boolean;
  fallback_in_use: boolean;
  runtime_state?: string;
  status_banner: string;
  providers: {
    qualcomm: {
      name: string;
      model: string;
      runtime: string;
      device: string;
      dimension: number;
      is_available: boolean;
      qnn_provider_present: boolean;
      snapdragon_detected: boolean;
      model_path: string;
      model_exists: boolean;
      reason: string;
    };
    cpu: {
      name: string;
      model: string;
      runtime: string;
      device: string;
      dimension: number;
      is_active: boolean;
      cached_items: number;
    };
  };
}

export interface CaptureStatus {
  is_capturing: boolean;
  interval_seconds: number;
  last_captured_at: string | null;
  total_memories: number;
  last_error: string | null;
  cloud_requests: number;
}

export interface SettingsModel {
  capture_interval_seconds: number;
  capture_enabled: boolean;
  excluded_applications: string[];
  semantic_weight: number;
  keyword_weight: number;
  recency_weight: number;
  preferred_provider: string;
  preferred_ocr: string;
}

export interface BenchmarkMetrics {
  timestamp: string;
  processor: string;
  os: string;
  model: string;
  execution_provider: string;
  cold_start_load_ms?: number;
  warm_embedding_avg_ms?: number;
  warm_embedding_p95_ms?: number;
  batch_embedding_avg_ms_per_item?: number;
  vector_search_latency_avg_ms?: number;
  full_search_latency_avg_ms?: number;
  ocr_latency_avg_ms: number;
  embedding_latency_avg_ms: number;
  embedding_latency_p95_ms: number;
  search_latency_avg_ms: number;
  end_to_end_avg_ms: number;
  samples_count: number;
  status: string;
  runtime_state?: string;
}

export type PageId = 'home' | 'search' | 'memories' | 'runtime' | 'benchmarks' | 'privacy';
