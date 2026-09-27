import React from "react";
import { ArrowLeft, ArrowRight, Check, CheckCircle2, Cpu, FileSpreadsheet, FileText, Layers, Music, Sparkles, Video } from "lucide-react";
import { Button } from "@/components/ui/button";
import { OnboardingState } from "./types";

interface StepLaunchProps {
  state: OnboardingState;
  onSeedSampleData: () => Promise<void>;
  isSeeding: boolean;
  isSeeded: boolean;
  onFinish: () => void;
  onBack: () => void;
}

const SAMPLE_FILES = [
  { name: "sample_financials.xlsx", desc: "P&L tabs with DuckDB Text-to-SQL readiness", icon: FileSpreadsheet },
  { name: "sample_contract.pdf", desc: "Multi-column clauses with visual bounding boxes", icon: FileText },
  { name: "sample_tech_demo.mp4", desc: "30s video with word timestamps and keyframes", icon: Video },
  { name: "sample_audio_brief.mp3", desc: "Spoken executive brief with speaker markers", icon: Music },
];

export const StepLaunch: React.FC<StepLaunchProps> = ({
  state,
  onSeedSampleData,
  isSeeding,
  isSeeded,
  onFinish,
  onBack,
}) => {
  return (
    <div className="space-y-5">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          <h2 className="text-lg font-semibold text-slate-900 tracking-tight">Review Architecture & Launch</h2>
        </div>
        <p className="text-xs text-slate-500">
          Your AI pipeline is configured and ready to initialize for <span className="font-medium text-slate-800">{state.workspaceName}</span>.
        </p>
      </div>

      {/* Architecture & Pipeline Summary */}
      <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-2.5">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-900">
          <span className="flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-slate-700" />
            <span>Configured RAG Architecture</span>
          </span>
          <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-200 text-slate-800">
            {state.providerMode} mode
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
          <div className="p-2.5 bg-white rounded border border-slate-200">
            <div className="text-[10px] text-slate-400 uppercase font-medium">Reasoning LLM</div>
            <div className="font-mono text-xs font-semibold text-slate-900 truncate mt-0.5">{state.defaultLlmModel}</div>
            <div className="text-[10px] text-slate-500 capitalize">{state.providerName} Provider</div>
          </div>

          <div className="p-2.5 bg-white rounded border border-slate-200">
            <div className="text-[10px] text-slate-400 uppercase font-medium">Vector Embedding</div>
            <div className="font-mono text-xs font-semibold text-slate-900 truncate mt-0.5">{state.defaultEmbeddingModel}</div>
            <div className="text-[10px] text-slate-500">Stage 1: Dense Retrieval</div>
          </div>

          <div className="p-2.5 bg-white rounded border border-slate-200">
            <div className="text-[10px] text-slate-400 uppercase font-medium flex items-center gap-1">
              <Cpu className="w-3 h-3 text-slate-500" />
              <span>Cross-Encoder Reranker</span>
            </div>
            <div className="font-mono text-xs font-semibold text-slate-900 truncate mt-0.5">
              {state.defaultRerankerModel || "ms-marco-MiniLM-L-12-v2"}
            </div>
            <div className="text-[10px] text-emerald-700 font-medium">Stage 2: Re-Scoring Engine</div>
          </div>
        </div>
      </div>

      {/* Enterprise Sample Pack */}
      <div className="p-4 rounded-lg border border-slate-900 bg-white ring-1 ring-slate-900/10 space-y-3.5">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-900 mb-0.5">
              <Sparkles className="w-4 h-4 text-amber-500 fill-amber-500" />
              <span>Preload Verified Multimodal Dataset (Recommended)</span>
            </div>
            <p className="text-[11px] text-slate-600">
              Instantly provisions 4 sample files to test multimodal queries and text-to-SQL:
            </p>
          </div>
          <span className="text-[10px] font-medium bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded-full">
            Ready
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
          {SAMPLE_FILES.map((file) => {
            const Icon = file.icon;
            return (
              <div key={file.name} className="flex items-start gap-2 p-2 bg-slate-50 rounded border border-slate-200">
                <Icon className="w-4 h-4 text-slate-700 shrink-0 mt-0.5" />
                <div>
                  <div className="font-mono text-[11px] font-medium text-slate-800">{file.name}</div>
                  <div className="text-[10px] text-slate-500 leading-tight">{file.desc}</div>
                </div>
              </div>
            );
          })}
        </div>

        {isSeeded ? (
          <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-md flex items-center justify-between text-xs text-emerald-900">
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-600 stroke-[3]" />
              <span className="font-medium">4 files seeded and queued for indexing!</span>
            </div>
            <Button size="sm" onClick={onFinish} className="gap-1.5 bg-emerald-800 hover:bg-emerald-900 text-white">
              <span>Go to Workspace</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          </div>
        ) : (
          <Button type="button" onClick={onSeedSampleData} isLoading={isSeeding} className="w-full gap-2 bg-slate-900 hover:bg-slate-800 text-white shadow-xs">
            <Sparkles className="w-4 h-4" />
            <span>Load Enterprise Sample Pack (10s)</span>
          </Button>
        )}
      </div>

      <div className="pt-3 border-t border-slate-200 flex justify-between items-center">
        <Button variant="outline" onClick={onBack} className="gap-2">
          <ArrowLeft className="w-4 h-4" />
          <span>Back</span>
        </Button>
        <Button variant="ghost" onClick={onFinish} className="gap-2 text-slate-600 hover:text-slate-900">
          <span>Skip to Empty Workspace</span>
          <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};
