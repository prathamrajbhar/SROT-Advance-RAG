import React, { useState } from "react";
import { ExternalLink, Eye, EyeOff, Layers, ShieldCheck } from "lucide-react";
import { Input } from "@/components/ui/input";

export interface RerankerOption {
  id: string;
  name: string;
  engine: "flashrank" | "cohere" | "bge" | "none";
  badge: string;
  latency: string;
  isDefault?: boolean;
}

export const RERANKER_OPTIONS: RerankerOption[] = [
  { id: "ms-marco-MiniLM-L-12-v2", name: "FlashRank MiniLM (L-12)", engine: "flashrank", badge: "Local ONNX • Zero Egress", latency: "~12ms", isDefault: true },
  { id: "ms-marco-TinyBERT-L-2-v2", name: "FlashRank TinyBERT", engine: "flashrank", badge: "Sub-5ms • Ultra Fast", latency: "~4ms" },
  { id: "rerank-v4-fast", name: "Cohere Rerank v4 Fast", engine: "cohere", badge: "Cloud BYOK • 32K Context", latency: "~60ms" },
  { id: "rerank-v4-pro", name: "Cohere Rerank v4 Pro", engine: "cohere", badge: "Cloud BYOK • Deep Precision", latency: "~110ms" },
  { id: "bge-reranker-v2-m3", name: "BAAI BGE-Reranker M3", engine: "bge", badge: "Self-Hosted / TEI", latency: "~30ms" },
  { id: "none", name: "Direct Vector Search Only", engine: "none", badge: "Single-Stage (No Rerank)", latency: "0ms" },
];

interface RerankerSelectorProps {
  selectedModel: string;
  cohereApiKey?: string;
  onChange: (patch: { defaultRerankerModel: string; rerankerApiKey?: string }) => void;
}

export const RerankerSelector: React.FC<RerankerSelectorProps> = ({ selectedModel, cohereApiKey, onChange }) => {
  const [showKey, setShowKey] = useState(false);
  const activeModel = selectedModel || "ms-marco-MiniLM-L-12-v2";
  const selectedConfig = RERANKER_OPTIONS.find((r) => r.id === activeModel) || RERANKER_OPTIONS[0];
  const isCohere = selectedConfig.engine === "cohere";

  return (
    <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-slate-900 text-white flex items-center justify-center">
            <Layers className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-slate-900">Stage 2: Cross-Encoder Reranker</h3>
            <p className="text-[11px] text-slate-500">Cross-attention re-scoring of candidate chunks to eliminate hallucinations</p>
          </div>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white text-slate-700 border border-slate-200">
          {selectedConfig.latency}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="block text-[11px] font-medium text-slate-700 mb-1">Reranking Model</label>
          <select
            value={activeModel}
            onChange={(e) => onChange({ defaultRerankerModel: e.target.value, rerankerApiKey: cohereApiKey })}
            className="w-full text-xs rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900"
          >
            {RERANKER_OPTIONS.map((opt) => (
              <option key={opt.id} value={opt.id}>
                {opt.name} ({opt.badge})
              </option>
            ))}
          </select>
        </div>

        <div>
          {isCohere ? (
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-[11px] font-medium text-slate-700">Cohere API Key (BYOK)</label>
                <a
                  href="https://dashboard.cohere.com/api-keys"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-[10px] text-slate-500 hover:text-slate-800"
                >
                  <span>Get Key</span>
                  <ExternalLink className="w-2.5 h-2.5" />
                </a>
              </div>
              <div className="relative">
                <Input
                  type={showKey ? "text" : "password"}
                  value={cohereApiKey || ""}
                  onChange={(e) => onChange({ defaultRerankerModel: activeModel, rerankerApiKey: e.target.value })}
                  placeholder="Paste Cohere API key..."
                  className="font-mono text-xs pr-9 bg-white"
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-2 top-2 text-slate-400 hover:text-slate-600"
                >
                  {showKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col justify-end">
              <div className="p-2 bg-white rounded border border-slate-200 flex items-center gap-2 text-[11px] text-slate-600">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                <span>
                  {selectedConfig.engine === "flashrank"
                    ? "In-Memory ONNX execution with zero API keys and zero network hops."
                    : selectedConfig.engine === "none"
                    ? "Reranking bypassed. Raw dense/sparse vector similarity used."
                    : "Self-hosted cross-encoder inference via local daemon."}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
