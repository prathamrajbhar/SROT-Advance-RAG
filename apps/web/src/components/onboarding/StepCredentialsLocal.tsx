import React, { useCallback, useEffect, useState } from "react";
import { AlertCircle, Download, Lock, RefreshCw } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { LocalEngineSelector, LOCAL_ENGINES } from "./LocalEngineSelector";
import { ModelDownloadModal } from "./ModelDownloadModal";
import { discoverModelsApi } from "./onboarding-api";
import { DiscoveredModelItem, LocalEngine, OnboardingState } from "./types";

interface StepCredentialsLocalProps {
  state: OnboardingState;
  onChange: (patch: Partial<OnboardingState>) => void;
}

export const StepCredentialsLocal: React.FC<StepCredentialsLocalProps> = ({ state, onChange }) => {
  const [isScanning, setIsScanning] = useState(false);
  const [reasoningModels, setReasoningModels] = useState<DiscoveredModelItem[]>([]);
  const [embeddingModels, setEmbeddingModels] = useState<DiscoveredModelItem[]>([]);
  const [scanMessage, setScanMessage] = useState<string | null>(null);
  const [isCustomMode, setIsCustomMode] = useState(false);
  const [downloadTarget, setDownloadTarget] = useState<string | null>(null);

  const activeEngine = state.localEngine || "ollama";

  const scanLocalModels = useCallback(async (url: string) => {
    setIsScanning(true);
    try {
      const res = await discoverModelsApi({ provider_mode: "local", base_url: url, api_key: state.apiKey || undefined });
      setReasoningModels(res.reasoning_models);
      setEmbeddingModels(res.embedding_models);
      setScanMessage(res.message || null);
      if (res.reasoning_models.length > 0 && !res.reasoning_models.some((m) => m.id === state.defaultLlmModel)) {
        onChange({ defaultLlmModel: res.reasoning_models[0].id });
      }
      if (res.embedding_models.length > 0 && !res.embedding_models.some((m) => m.id === state.defaultEmbeddingModel)) {
        onChange({ defaultEmbeddingModel: res.embedding_models[0].id });
      }
    } catch {
      setScanMessage("Host unreachable. Ensure Ollama/vLLM is running.");
    } finally {
      setIsScanning(false);
    }
  }, [onChange, state.apiKey, state.defaultEmbeddingModel, state.defaultLlmModel]);

  useEffect(() => {
    scanLocalModels(state.baseUrl || "http://localhost:11434");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleEngineSelect = (engineId: LocalEngine) => {
    const engineConfig = LOCAL_ENGINES.find((e) => e.id === engineId);
    const newUrl = engineConfig?.defaultUrl || state.baseUrl;
    onChange({ localEngine: engineId, baseUrl: newUrl });
    scanLocalModels(newUrl);
  };

  return (
    <div className="space-y-4">
      <LocalEngineSelector activeEngine={activeEngine} onSelect={handleEngineSelect} />

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs font-medium text-slate-700">Host Endpoint URL</label>
            <button
              type="button"
              disabled={isScanning}
              onClick={() => scanLocalModels(state.baseUrl)}
              className="inline-flex items-center gap-1 text-[11px] text-slate-600 hover:text-slate-900 disabled:opacity-50"
            >
              <RefreshCw className={cn("w-3 h-3", isScanning && "animate-spin")} />
              <span>{isScanning ? "Scanning..." : "Rescan Host"}</span>
            </button>
          </div>
          <Input
            value={state.baseUrl}
            onChange={(e) => onChange({ baseUrl: e.target.value })}
            onBlur={() => scanLocalModels(state.baseUrl)}
            placeholder="http://localhost:11434"
            className="font-mono text-xs"
            required
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">Bearer Token (Optional)</label>
          <Input
            type="password"
            value={state.apiKey}
            onChange={(e) => onChange({ apiKey: e.target.value })}
            placeholder="Optional authorization token..."
            className="font-mono text-xs"
          />
        </div>
      </div>

      {scanMessage && (
        <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-md flex items-center justify-between text-[11px]">
          <span className="text-slate-600 font-mono truncate">{scanMessage}</span>
          <button type="button" onClick={() => setIsCustomMode(!isCustomMode)} className="text-slate-800 underline font-medium shrink-0 ml-2">
            {isCustomMode ? "Use Detected List" : "Manual Tag"}
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs font-medium text-slate-700">Reasoning ({reasoningModels.length})</label>
            <button
              type="button"
              onClick={() => setDownloadTarget("llama3.2:3b")}
              className="inline-flex items-center gap-1 text-[10px] text-blue-700 hover:text-blue-900 font-medium"
            >
              <Download className="w-2.5 h-2.5" />
              <span>Pull Llama 3.2</span>
            </button>
          </div>
          {isCustomMode || reasoningModels.length === 0 ? (
            <Input value={state.defaultLlmModel} onChange={(e) => onChange({ defaultLlmModel: e.target.value })} placeholder="e.g. llama3.2:3b" className="font-mono text-xs" />
          ) : (
            <select value={state.defaultLlmModel} onChange={(e) => onChange({ defaultLlmModel: e.target.value })} className="w-full text-xs rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900">
              {reasoningModels.map((m) => (<option key={m.id} value={m.id}>{m.name} {m.badge ? `(${m.badge})` : ""}</option>))}
            </select>
          )}
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs font-medium text-slate-700">Embedding ({embeddingModels.length})</label>
            <button
              type="button"
              onClick={() => setDownloadTarget("nomic-embed-text:latest")}
              className="inline-flex items-center gap-1 text-[10px] text-blue-700 hover:text-blue-900 font-medium"
            >
              <Download className="w-2.5 h-2.5" />
              <span>Pull Nomic Embed</span>
            </button>
          </div>
          {isCustomMode || embeddingModels.length === 0 ? (
            <Input value={state.defaultEmbeddingModel} onChange={(e) => onChange({ defaultEmbeddingModel: e.target.value })} placeholder="e.g. nomic-embed-text" className="font-mono text-xs" />
          ) : (
            <select value={state.defaultEmbeddingModel} onChange={(e) => onChange({ defaultEmbeddingModel: e.target.value })} className="w-full text-xs rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900">
              {embeddingModels.map((m) => (<option key={m.id} value={m.id}>{m.name} {m.badge ? `(${m.badge})` : ""}</option>))}
            </select>
          )}
        </div>
      </div>

      {reasoningModels.length === 0 && !isScanning && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start justify-between gap-3 text-xs text-amber-900">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
            <div>
              <p className="font-semibold">No downloaded models detected</p>
              <p className="text-[11px] text-amber-700 mt-0.5">Click to pull directly into your local Ollama daemon:</p>
            </div>
          </div>
          <div className="flex gap-2 shrink-0">
            <button type="button" onClick={() => setDownloadTarget("nomic-embed-text:latest")} className="px-2 py-1 rounded bg-amber-100 hover:bg-amber-200 text-amber-900 font-mono text-[10px]">
              Pull Embed (274MB)
            </button>
            <button type="button" onClick={() => setDownloadTarget("llama3.2:3b")} className="px-2 py-1 rounded bg-amber-100 hover:bg-amber-200 text-amber-900 font-mono text-[10px]">
              Pull Llama 3.2 (2GB)
            </button>
          </div>
        </div>
      )}

      <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-md flex items-center gap-2 text-[11px] text-slate-600">
        <Lock className="w-3.5 h-3.5 text-slate-500 shrink-0" />
        <span>Zero Egress: Inference executes entirely on your hardware.</span>
      </div>

      <ModelDownloadModal
        isOpen={downloadTarget !== null}
        modelName={downloadTarget || ""}
        baseUrl={state.baseUrl}
        onClose={() => setDownloadTarget(null)}
        onSuccess={() => {
          scanLocalModels(state.baseUrl);
          setDownloadTarget(null);
        }}
      />
    </div>
  );
};
