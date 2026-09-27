import React, { useCallback, useEffect, useState } from "react";
import { Cloud, Eye, EyeOff, ShieldAlert } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { HybridLocalTier } from "./HybridLocalTier";
import { discoverModelsApi } from "./onboarding-api";
import { DiscoveredModelItem, OnboardingState } from "./types";

interface StepCredentialsHybridProps {
  state: OnboardingState;
  onChange: (patch: Partial<OnboardingState>) => void;
}

const HYBRID_CLOUD_PROVIDERS = [
  { id: "gemini", name: "Gemini" },
  { id: "openai", name: "OpenAI" },
  { id: "anthropic", name: "Anthropic" },
  { id: "groq", name: "Groq" },
];

export const StepCredentialsHybrid: React.FC<StepCredentialsHybridProps> = ({ state, onChange }) => {
  const [showKey, setShowKey] = useState(false);
  const [localEmbeddings, setLocalEmbeddings] = useState<DiscoveredModelItem[]>([]);
  const [cloudReasoning, setCloudReasoning] = useState<DiscoveredModelItem[]>([]);
  const [isScanningLocal, setIsScanningLocal] = useState(false);

  const activeCloud = state.providerName === "local" ? "gemini" : state.providerName;

  const scanLocalEmbeddings = useCallback(async (url: string) => {
    setIsScanningLocal(true);
    try {
      const res = await discoverModelsApi({ provider_mode: "local", base_url: url });
      setLocalEmbeddings(res.embedding_models);
      if (res.embedding_models.length > 0 && !res.embedding_models.some((m) => m.id === state.defaultEmbeddingModel)) {
        onChange({ defaultEmbeddingModel: res.embedding_models[0].id });
      }
    } catch {
      // Fallback
    } finally {
      setIsScanningLocal(false);
    }
  }, [onChange, state.defaultEmbeddingModel]);

  const scanCloudReasoning = useCallback(async (provider: string, key: string) => {
    if (!key || key.length < 8) return;
    try {
      const res = await discoverModelsApi({ provider_mode: "cloud", provider_name: provider, api_key: key });
      setCloudReasoning(res.reasoning_models);
      if (res.reasoning_models.length > 0 && !res.reasoning_models.some((m) => m.id === state.defaultLlmModel)) {
        onChange({ defaultLlmModel: res.reasoning_models[0].id });
      }
    } catch {
      // Fallback
    }
  }, [onChange, state.defaultLlmModel]);

  useEffect(() => {
    scanLocalEmbeddings(state.baseUrl || "http://localhost:11434");
    if (state.apiKey) scanCloudReasoning(activeCloud, state.apiKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCloudProviderSelect = (providerId: string) => {
    onChange({ providerName: providerId });
    setCloudReasoning([]);
    if (state.apiKey) scanCloudReasoning(providerId, state.apiKey);
  };

  return (
    <div className="space-y-4">
      {/* Tier 1: Local Embeddings Tier */}
      <HybridLocalTier
        state={state}
        onChange={onChange}
        localEmbeddings={localEmbeddings}
        isScanningLocal={isScanningLocal}
        onScanLocal={scanLocalEmbeddings}
      />

      {/* Tier 2: Cloud Frontier Reasoning Tier */}
      <div className="p-3.5 bg-white border border-slate-200 rounded-lg space-y-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-slate-100 text-slate-800 flex items-center justify-center border border-slate-200">
            <Cloud className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-slate-900">2. Cloud Frontier Reasoning (Synthesis Only)</h3>
            <p className="text-[11px] text-slate-500">Live API auto-discovered models for high-capacity synthesis</p>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-1.5">
          {HYBRID_CLOUD_PROVIDERS.map((provider) => {
            const isSelected = activeCloud === provider.id;
            return (
              <button
                key={provider.id}
                type="button"
                onClick={() => handleCloudProviderSelect(provider.id)}
                className={cn(
                  "py-1.5 px-2 rounded-md border text-center text-xs font-medium transition-colors select-none",
                  isSelected
                    ? "border-slate-900 bg-slate-900 text-white shadow-xs"
                    : "border-slate-200 bg-white hover:border-slate-300 text-slate-600 hover:bg-slate-50"
                )}
              >
                {provider.name}
              </button>
            );
          })}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-[11px] font-medium text-slate-700 mb-1">Cloud API Key (BYOK)</label>
            <div className="relative">
              <Input
                type={showKey ? "text" : "password"}
                value={state.apiKey}
                onChange={(e) => onChange({ apiKey: e.target.value })}
                onBlur={() => scanCloudReasoning(activeCloud, state.apiKey)}
                placeholder="Paste cloud API key..."
                className="font-mono text-xs pr-10"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600"
              >
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-slate-700 mb-1">
              Discovered Cloud Model ({cloudReasoning.length})
            </label>
            {cloudReasoning.length === 0 ? (
              <Input
                value={state.defaultLlmModel}
                onChange={(e) => onChange({ defaultLlmModel: e.target.value })}
                placeholder="e.g. gemini-2.0-flash"
                className="font-mono text-xs"
              />
            ) : (
              <select
                value={state.defaultLlmModel}
                onChange={(e) => onChange({ defaultLlmModel: e.target.value })}
                className="w-full text-xs rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900"
              >
                {cloudReasoning.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} {m.badge ? `(${m.badge})` : ""}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>
      </div>

      {/* Tier 3: Privacy Guardrail */}
      <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-md flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-slate-700 shrink-0" />
          <div>
            <div className="text-xs font-semibold text-slate-900">Pre-Flight Data Anonymization</div>
            <div className="text-[11px] text-slate-500">Automatically strip PII before passing context to cloud reasoning LLM</div>
          </div>
        </div>
        <input
          type="checkbox"
          checked={state.redactPii ?? true}
          onChange={(e) => onChange({ redactPii: e.target.checked })}
          className="rounded border-slate-300 text-slate-900 focus:ring-slate-900 w-4 h-4"
        />
      </div>
    </div>
  );
};
