import React from "react";
import { Cpu, RefreshCw } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { DiscoveredModelItem, OnboardingState } from "./types";

interface HybridLocalTierProps {
  state: OnboardingState;
  onChange: (patch: Partial<OnboardingState>) => void;
  localEmbeddings: DiscoveredModelItem[];
  isScanningLocal: boolean;
  onScanLocal: (url: string) => void;
}

export const HybridLocalTier: React.FC<HybridLocalTierProps> = ({
  state,
  onChange,
  localEmbeddings,
  isScanningLocal,
  onScanLocal,
}) => {
  return (
    <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-slate-900 text-white flex items-center justify-center">
            <Cpu className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-slate-900">1. On-Premise Vector Engine (Zero Egress)</h3>
            <p className="text-[11px] text-slate-500">Auto-detected downloaded embeddings on your local daemon</p>
          </div>
        </div>
        <button
          type="button"
          disabled={isScanningLocal}
          onClick={() => onScanLocal(state.baseUrl)}
          className="inline-flex items-center gap-1 text-[10px] font-mono text-slate-600 hover:text-slate-900 disabled:opacity-50"
        >
          <RefreshCw className={cn("w-3 h-3", isScanningLocal && "animate-spin")} />
          <span>{isScanningLocal ? "Scanning..." : "Rescan"}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="block text-[11px] font-medium text-slate-700 mb-1">Local Daemon URL</label>
          <Input
            value={state.baseUrl}
            onChange={(e) => onChange({ baseUrl: e.target.value })}
            onBlur={() => onScanLocal(state.baseUrl)}
            placeholder="http://localhost:11434"
            className="font-mono text-xs bg-white"
          />
        </div>
        <div>
          <label className="block text-[11px] font-medium text-slate-700 mb-1">
            Downloaded Local Embedding ({localEmbeddings.length})
          </label>
          {localEmbeddings.length === 0 ? (
            <Input
              value={state.defaultEmbeddingModel}
              onChange={(e) => onChange({ defaultEmbeddingModel: e.target.value })}
              placeholder="e.g. nomic-embed-text"
              className="font-mono text-xs bg-white"
            />
          ) : (
            <select
              value={state.defaultEmbeddingModel}
              onChange={(e) => onChange({ defaultEmbeddingModel: e.target.value })}
              className="w-full text-xs rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900"
            >
              {localEmbeddings.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} {m.badge ? `(${m.badge})` : ""}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>
    </div>
  );
};
