import React from "react";
import { ArrowLeft, ArrowRight, Check, Cloud, Cpu, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { OnboardingState, ProviderMode } from "./types";

interface StepProviderModeProps {
  state: OnboardingState;
  onChange: (patch: Partial<OnboardingState>) => void;
  onNext: () => void;
  onBack: () => void;
}

const MODES: Array<{
  id: ProviderMode;
  title: string;
  badge: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  dataflow: string;
  features: string[];
}> = [
  {
    id: "cloud",
    title: "Cloud Managed APIs",
    badge: "Direct BYOK",
    icon: Cloud,
    description: "Connect standard cloud APIs with AES-256 envelope encrypted client keys.",
    dataflow: "Cloud API ──> SROT Engine",
    features: ["Google Gemini (2.0 Flash / Pro)", "OpenAI (GPT-4o / o3-mini)", "Anthropic (Claude 3.7)", "Groq LPU Acceleration"],
  },
  {
    id: "local",
    title: "Self-Hosted / Private",
    badge: "Zero Data Egress",
    icon: Cpu,
    description: "Run strictly air-gapped on your private Kubernetes cluster or local workstation.",
    dataflow: "Private Host ──> Local Qdrant",
    features: ["Ollama native API (:11434)", "vLLM high-throughput engine", "Local embedding models (Nomic / Qwen3)"],
  },
  {
    id: "hybrid",
    title: "Hybrid Topology",
    badge: "Enterprise Recommended",
    icon: Layers,
    description: "Local on-premise embeddings paired with high-reasoning frontier cloud LLMs.",
    dataflow: "Local Vectors + Cloud Synthesis",
    features: ["Local embeddings on Qdrant", "Cloud synthesis reasoning", "Pre-flight PII & data masking"],
  },
];

export const StepProviderMode: React.FC<StepProviderModeProps> = ({
  state,
  onChange,
  onNext,
  onBack,
}) => {
  const handleSelect = (mode: ProviderMode) => {
    let defaultModel = state.defaultLlmModel;
    let defaultEmbedding = state.defaultEmbeddingModel;
    let defaultProvider = state.providerName;

    if (mode === "local") {
      defaultModel = "llama3.3:70b";
      defaultEmbedding = "nomic-embed-text";
      defaultProvider = "local";
    } else if (mode === "cloud") {
      defaultModel = "gemini-2.0-flash";
      defaultEmbedding = "text-embedding-004";
      defaultProvider = "gemini";
    } else if (mode === "hybrid") {
      defaultModel = "gemini-2.0-flash";
      defaultEmbedding = "nomic-embed-text";
      defaultProvider = "gemini";
    }

    onChange({
      providerMode: mode,
      providerName: defaultProvider,
      defaultLlmModel: defaultModel,
      defaultEmbeddingModel: defaultEmbedding,
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-900 tracking-tight">Select AI Model Architecture</h2>
        <p className="text-xs text-slate-500">
          Decide how multimodal embeddings and reasoning requests will route to AI backends.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {MODES.map((mode) => {
          const Icon = mode.icon;
          const isSelected = state.providerMode === mode.id;

          return (
            <div
              key={mode.id}
              onClick={() => handleSelect(mode.id)}
              className={cn(
                "relative p-4 rounded-xl border text-left cursor-pointer transition-all duration-150 flex flex-col justify-between select-none",
                isSelected
                  ? "border-slate-900 bg-white ring-2 ring-slate-900 shadow-sm"
                  : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50"
              )}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div
                    className={cn(
                      "w-8 h-8 rounded-lg flex items-center justify-center transition-colors",
                      isSelected ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"
                    )}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 font-medium">
                      {mode.badge}
                    </span>
                    {isSelected && (
                      <span className="w-4 h-4 rounded-full bg-slate-900 text-white flex items-center justify-center">
                        <Check className="w-2.5 h-2.5 stroke-[3]" />
                      </span>
                    )}
                  </div>
                </div>

                <h3 className="text-sm font-semibold text-slate-900 mb-1">{mode.title}</h3>
                <p className="text-xs text-slate-600 mb-2 leading-relaxed">{mode.description}</p>
                <div className="text-[11px] font-mono text-slate-500 bg-slate-50 px-2 py-1 rounded border border-slate-100 mb-3">
                  {mode.dataflow}
                </div>
              </div>

              <ul className="space-y-1.5 pt-3 border-t border-slate-100 text-[11px] text-slate-500">
                {mode.features.map((feature, i) => (
                  <li key={i} className="flex items-center gap-1.5">
                    <span className="w-1 h-1 rounded-full bg-slate-400 shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>

      <div className="pt-4 border-t border-slate-200 flex justify-between items-center">
        <Button variant="outline" onClick={onBack} className="gap-2">
          <ArrowLeft className="w-4 h-4" />
          <span>Back</span>
        </Button>
        <Button onClick={onNext} className="gap-2">
          <span>Configure Credentials</span>
          <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};
