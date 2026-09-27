export type ProviderMode = "cloud" | "local" | "hybrid";
export type LocalEngine = "ollama" | "vllm" | "localai";

export interface OnboardingState {
  tenantName: string;
  tenantSlug: string;
  workspaceName: string;
  adminEmail: string;
  tenantId?: string;
  workspaceId?: string;
  providerMode: ProviderMode;
  providerName: string;
  localEngine?: LocalEngine;
  apiKey: string;
  baseUrl: string;
  bearerToken?: string;
  defaultLlmModel: string;
  defaultEmbeddingModel: string;
  defaultRerankerModel: string;
  rerankerApiKey?: string;
  redactPii?: boolean;
}

export type ConnectionStatus = "idle" | "testing" | "healthy" | "error";

export interface ProbeResult {
  healthy: boolean;
  latency_ms: number;
  model: string;
  message?: string;
  metadata?: { dimensions?: number; [key: string]: unknown };
}

export interface PipelineDiagnosticResponse {
  healthy: boolean;
  overall_latency_ms: number;
  llm_probe: ProbeResult;
  embedding_probe: ProbeResult;
  reranker_probe: ProbeResult;
}

export interface ConnectionDiagnostic {
  status: ConnectionStatus;
  latencyMs?: number;
  resolvedModel?: string;
  errorMessage?: string;
  pipeline?: PipelineDiagnosticResponse;
}

export interface ModelPullProgressResponse {
  job_id: string;
  model_name: string;
  engine: string;
  status: "starting" | "downloading" | "verifying" | "ready" | "failed";
  completed_bytes: number;
  total_bytes: number;
  percentage: number;
  status_text?: string;
  error?: string;
}

export interface DiscoveredModelItem {
  id: string;
  name: string;
  category: "reasoning" | "embedding";
  badge?: string;
  context_length?: number;
  description?: string;
}

export interface DiscoverModelsResponse {
  provider: string;
  reasoning_models: DiscoveredModelItem[];
  embedding_models: DiscoveredModelItem[];
  is_live: boolean;
  total_count: number;
  message?: string;
}

export interface OnboardingStatusResponse {
  is_onboarded: boolean;
  tenant_id?: string;
  tenant_name?: string;
  workspace_id?: string;
  workspace_name?: string;
  provider_mode?: string;
  default_llm_model?: string;
  default_embedding_model?: string;
  default_reranker_model?: string;
}


