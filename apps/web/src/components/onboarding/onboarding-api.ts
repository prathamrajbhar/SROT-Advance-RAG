import { apiFetch } from "@/lib/api-client";
import {
  DiscoverModelsResponse,
  ModelPullProgressResponse,
  OnboardingState,
  OnboardingStatusResponse,
  PipelineDiagnosticResponse,
} from "./types";

export interface WorkspaceCreationResult {
  tenant_id: string;
  workspace_id: string;
}

export interface ProviderPingResponse {
  healthy: boolean;
  latency_ms: number;
  resolved_model: string;
  error_message?: string;
}

export async function createWorkspaceApi(state: OnboardingState): Promise<WorkspaceCreationResult> {
  return apiFetch<WorkspaceCreationResult>("/onboarding/workspace", {
    method: "POST",
    body: JSON.stringify({
      tenant_name: state.tenantName,
      tenant_slug: state.tenantSlug,
      workspace_name: state.workspaceName,
      admin_email: state.adminEmail,
    }),
  });
}

export async function pingProviderApi(state: OnboardingState): Promise<ProviderPingResponse> {
  const isCloud = state.providerMode === "cloud";
  const effectiveBaseUrl = isCloud ? undefined : (state.baseUrl || undefined);
  return apiFetch<ProviderPingResponse>("/onboarding/test-provider", {
    method: "POST",
    body: JSON.stringify({
      provider_mode: state.providerMode,
      provider_name: state.providerName,
      model: state.defaultLlmModel,
      api_key: state.apiKey || undefined,
      base_url: effectiveBaseUrl,
    }),
  });
}

export async function saveProviderSettingsApi(state: OnboardingState): Promise<void> {
  if (!state.workspaceId) return;
  const isCloud = state.providerMode === "cloud";
  const effectiveBaseUrl = isCloud ? undefined : (state.baseUrl || undefined);
  await apiFetch("/onboarding/provider-settings", {
    method: "POST",
    body: JSON.stringify({
      workspace_id: state.workspaceId,
      provider_mode: state.providerMode,
      provider_name: state.providerName,
      api_key: state.apiKey || undefined,
      base_url: effectiveBaseUrl,
      default_llm_model: state.defaultLlmModel,
      default_embedding_model: state.defaultEmbeddingModel,
      default_reranker_model: state.defaultRerankerModel || "ms-marco-MiniLM-L-12-v2",
      reranker_api_key: state.rerankerApiKey || undefined,
    }),
  });
}

export async function seedSampleDataApi(workspaceId: string): Promise<void> {
  await apiFetch("/onboarding/seed-sample-data", {
    method: "POST",
    body: JSON.stringify({ workspace_id: workspaceId }),
  });
}

export async function discoverModelsApi(params: {
  provider_mode: string;
  provider_name?: string;
  api_key?: string;
  base_url?: string;
}): Promise<DiscoverModelsResponse> {
  return apiFetch<DiscoverModelsResponse>("/onboarding/discover-models", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function testPipelineApi(state: OnboardingState): Promise<PipelineDiagnosticResponse> {
  const isCloud = state.providerMode === "cloud";
  const effectiveBaseUrl = isCloud ? undefined : (state.baseUrl || undefined);
  return apiFetch<PipelineDiagnosticResponse>("/onboarding/test-pipeline", {
    method: "POST",
    body: JSON.stringify({
      provider_mode: state.providerMode,
      provider_name: state.providerName,
      llm_model: state.defaultLlmModel,
      embedding_model: state.defaultEmbeddingModel,
      reranker_model: state.defaultRerankerModel || "ms-marco-MiniLM-L-12-v2",
      api_key: state.apiKey || undefined,
      reranker_api_key: state.rerankerApiKey || undefined,
      base_url: effectiveBaseUrl,
    }),
  });
}

export async function startModelPullApi(modelName: string, engine = "ollama", baseUrl?: string): Promise<ModelPullProgressResponse> {
  return apiFetch<ModelPullProgressResponse>("/onboarding/models/pull", {
    method: "POST",
    body: JSON.stringify({
      engine,
      model_name: modelName,
      base_url: baseUrl || undefined,
    }),
  });
}

export async function getModelPullStatusApi(jobId: string): Promise<ModelPullProgressResponse> {
  return apiFetch<ModelPullProgressResponse>(`/onboarding/models/pull-status/${jobId}`, {
    method: "GET",
  });
}

export async function getOnboardingStatusApi(): Promise<OnboardingStatusResponse> {
  return apiFetch<OnboardingStatusResponse>("/onboarding/status", {
    method: "GET",
  });
}


