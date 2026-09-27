import React from "react";
import { AlertCircle, Bot, CheckCircle2, Cpu, Layers, Play, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ConnectionDiagnostic, ProbeResult } from "./types";

interface TriEngineDiagnosticsProps {
  diagnostic: ConnectionDiagnostic;
  onTestPipeline: () => Promise<void>;
  isLoading?: boolean;
}

const ProbeCard: React.FC<{
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  probe?: ProbeResult;
  fallbackModel?: string;
}> = ({ title, icon: Icon, probe, fallbackModel }) => {
  const isHealthy = probe?.healthy;
  const hasResult = probe !== undefined;

  return (
    <div
      className={cn(
        "p-2.5 rounded-lg border text-xs transition-all",
        !hasResult && "bg-white border-slate-200 text-slate-600",
        hasResult && isHealthy && "bg-emerald-50/40 border-emerald-200 text-emerald-950",
        hasResult && !isHealthy && "bg-rose-50/40 border-rose-200 text-rose-950"
      )}
    >
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-1.5 font-semibold text-slate-800">
          <Icon className="w-3.5 h-3.5 text-slate-500" />
          <span>{title}</span>
        </div>
        {hasResult && (
          <span className={cn("text-[10px] font-mono px-1.5 py-0.5 rounded", isHealthy ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800")}>
            {probe.latency_ms}ms
          </span>
        )}
      </div>
      <div className="font-mono text-[11px] truncate text-slate-700">
        {probe?.model || fallbackModel || "Pending verification..."}
      </div>
      <div className="text-[10px] text-slate-500 mt-0.5 flex items-center gap-1">
        {hasResult && isHealthy && <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" />}
        {hasResult && !isHealthy && <AlertCircle className="w-3 h-3 text-rose-600 shrink-0" />}
        <span className="truncate">{probe?.message || "Not tested yet"}</span>
      </div>
    </div>
  );
};

export const TriEngineDiagnostics: React.FC<TriEngineDiagnosticsProps> = ({
  diagnostic,
  onTestPipeline,
  isLoading,
}) => {
  const pipeline = diagnostic.pipeline;
  const isTesting = diagnostic.status === "testing" || isLoading;

  return (
    <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-900">Tri-Engine Pipeline Verification</span>
            {pipeline && (
              <span
                className={cn(
                  "text-[10px] uppercase font-mono px-2 py-0.5 rounded-full font-medium border",
                  pipeline.healthy
                    ? "bg-emerald-100 text-emerald-800 border-emerald-200"
                    : "bg-rose-100 text-rose-800 border-rose-200"
                )}
              >
                {pipeline.healthy ? `All 3 Engines Verified (${pipeline.overall_latency_ms}ms)` : "Verification Failed"}
              </span>
            )}
          </div>
          <p className="text-[11px] text-slate-500">Live dry run validating LLM generation, vector dimensions, and reranker scoring</p>
        </div>

        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={onTestPipeline}
          disabled={isTesting}
          className="gap-1.5 shrink-0 bg-white"
        >
          {isTesting ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3 fill-current" />}
          <span>{isTesting ? "Probing Pipeline..." : "Test Pipeline"}</span>
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        <ProbeCard title="1. Reasoning LLM" icon={Bot} probe={pipeline?.llm_probe} />
        <ProbeCard title="2. Vector Embeddings" icon={Layers} probe={pipeline?.embedding_probe} />
        <ProbeCard title="3. Cross-Encoder" icon={Cpu} probe={pipeline?.reranker_probe} />
      </div>

      {diagnostic.status === "error" && diagnostic.errorMessage && (
        <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-md text-[11px] text-rose-800 flex items-start gap-2">
          <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0 mt-0.5" />
          <span>{diagnostic.errorMessage}</span>
        </div>
      )}
    </div>
  );
};
