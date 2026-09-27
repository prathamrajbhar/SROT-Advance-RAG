import React, { useCallback, useEffect, useState } from "react";
import { ExternalLink, Eye, EyeOff, Info, RefreshCw, ShieldCheck } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { CloudProviderSelector, CLOUD_PROVIDERS } from "./CloudProviderSelector";
import { discoverModelsApi } from "./onboarding-api";
import { DiscoveredModelItem, OnboardingState } from "./types";

interface StepCredentialsCloudProps {
  state: OnboardingState;
  onChange: (patch: Partial<OnboardingState>) => void;
}

export const StepCredentialsCloud: React.FC<StepCredentialsCloudProps> = ({ state, onChange }) => {
  const [showKey, setShowKey] = useState(false);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [reasoningModels, setReasoningModels] = useState<DiscoveredModelItem[]>([]);
  const [embeddingModels, setEmbeddingModels] = useState<DiscoveredModelItem[]>([]);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [isCustomModel, setIsCustomModel] = useState(false);

  const activeProvider = CLOUD_PROVIDERS.find((p) => p.id === state.providerName) || CLOUD_PROVIDERS[0];
  const isReasoningOnly = state.providerName === "groq" || state.providerName === "anthropic";

  const fetchCloudModels = useCallback(async (provider: string, key: string) => {
    if (!key || key.length < 8) {
      setStatusMessage("Enter API key to auto-discover active models.");
      return;
    }
    setIsDiscovering(true);
    try {
      const res = await discoverModelsApi({ provider_mode: "cloud", provider_name: provider, api_key: key });
      setReasoningModels(res.reasoning_models);
      setEmbeddingModels(res.embedding_models);
      setStatusMessage(res.message || null);

      if (res.reasoning_models.length > 0 && !res.reasoning_models.some((m) => m.id === state.defaultLlmModel)) {
        onChange({ defaultLlmModel: res.reasoning_models[0].id });
      }
      if (res.embedding_models.length > 0 && !res.embedding_models.some((m) => m.id === state.defaultEmbeddingModel)) {
        onChange({ defaultEmbeddingModel: res.embedding_models[0].id });
      }
    } catch {
      setStatusMessage("Failed to fetch models from provider API.");
    } finally {
      setIsDiscovering(false);
    }
  }, [onChange, state.defaultEmbeddingModel, state.defaultLlmModel]);

  useEffect(() => {
    if (state.apiKey) fetchCloudModels(state.providerName, state.apiKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.providerName]);

  const handleProviderSelect = (providerId: string) => {
    const defaultEmbed = providerId === "gemini" ? "text-embedding-004" : providerId === "openai" ? "text-embedding-3-large" : "nomic-embed-text";
    onChange({ providerName: providerId, defaultEmbeddingModel: defaultEmbed });
    setReasoningModels([]);
    setEmbeddingModels([]);
    if (state.apiKey) fetchCloudModels(providerId, state.apiKey);
  };

  return (
    <div className="space-y-4">
      <CloudProviderSelector selectedId={state.providerName} onSelect={handleProviderSelect} />

      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="block text-xs font-medium text-slate-700">{activeProvider.name} API Key (BYOK)</label>
          <a href={activeProvider.docsUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[11px] text-slate-500 hover:text-slate-800">
            <span>Get API Key</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
        <div className="relative">
          <Input
            type={showKey ? "text" : "password"}
            value={state.apiKey}
            onChange={(e) => onChange({ apiKey: e.target.value })}
            onBlur={() => fetchCloudModels(state.providerName, state.apiKey)}
            placeholder="Paste your API key here..."
            className="font-mono text-xs pr-10"
            required
          />
          <button type="button" onClick={() => setShowKey(!showKey)} className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600">
            {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
        <div className="flex items-center justify-between mt-1 text-[11px]">
          <span className="flex items-center gap-1 text-emerald-700">
            <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
            <span>Encrypted with AES-256-GCM envelope encryption before persistence</span>
          </span>
          <button
            type="button"
            disabled={isDiscovering || !state.apiKey}
            onClick={() => fetchCloudModels(state.providerName, state.apiKey)}
            className="inline-flex items-center gap-1 text-slate-600 hover:text-slate-900 font-medium disabled:opacity-40"
          >
            <RefreshCw className={cn("w-3 h-3", isDiscovering && "animate-spin")} />
            <span>{isDiscovering ? "Discovering..." : "Discover Live Models"}</span>
          </button>
        </div>
      </div>

      {isReasoningOnly && (
        <div className="p-2.5 bg-blue-50 border border-blue-200 rounded-lg flex items-start gap-2 text-[11px] text-blue-900">
          <Info className="w-3.5 h-3.5 text-blue-600 shrink-0 mt-0.5" />
          <span><strong>{activeProvider.name}</strong> focuses exclusively on high-speed inference and provides no native embedding API. SROT pairs it with the vector embedding options below.</span>
        </div>
      )}

      {statusMessage && <div className="p-2 bg-slate-50 border border-slate-200 rounded text-[11px] text-slate-600 font-mono">{statusMessage}</div>}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs font-medium text-slate-700">Reasoning LLM ({reasoningModels.length})</label>
            <button type="button" onClick={() => setIsCustomModel(!isCustomModel)} className="text-[11px] text-slate-500 hover:text-slate-800 underline">
              {isCustomModel ? "Detected list" : "Custom model"}
            </button>
          </div>
          {isCustomModel || reasoningModels.length === 0 ? (
            <Input value={state.defaultLlmModel} onChange={(e) => onChange({ defaultLlmModel: e.target.value })} placeholder="e.g. llama-3.3-70b-versatile" className="font-mono text-xs" />
          ) : (
            <select value={state.defaultLlmModel} onChange={(e) => onChange({ defaultLlmModel: e.target.value })} className="w-full text-xs rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900">
              {reasoningModels.map((m) => (<option key={m.id} value={m.id}>{m.name} {m.badge ? `(${m.badge})` : ""}</option>))}
            </select>
          )}
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">Vector Embedding Engine ({embeddingModels.length})</label>
          <select value={state.defaultEmbeddingModel} onChange={(e) => onChange({ defaultEmbeddingModel: e.target.value })} className="w-full text-xs rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900">
            {embeddingModels.map((m) => (<option key={m.id} value={m.id}>{m.name} {m.badge ? `(${m.badge})` : ""}</option>))}
          </select>
        </div>
      </div>
    </div>
  );
};
