import React from "react";
import { AlertCircle, CheckCircle2, Loader2, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { ConnectionDiagnostic } from "./types";

interface ConnectionStatusPillProps {
  diagnostic: ConnectionDiagnostic;
}

export const ConnectionStatusPill: React.FC<ConnectionStatusPillProps> = ({ diagnostic }) => {
  const { status, latencyMs, errorMessage } = diagnostic;

  if (status === "idle") {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
        <Sparkles className="w-3.5 h-3.5 text-slate-400" />
        <span>Ready to test connection</span>
      </div>
    );
  }

  if (status === "testing") {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200 animate-pulse">
        <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-600" />
        <span>Pinging model endpoint...</span>
      </div>
    );
  }

  if (status === "healthy") {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
        <span>Connected & Verified</span>
        {latencyMs ? (
          <span className="font-mono text-[11px] bg-emerald-100 text-emerald-900 px-1 rounded">
            {latencyMs}ms
          </span>
        ) : null}
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-rose-50 text-rose-800 border border-rose-200 max-w-md truncate">
      <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
      <span className="truncate">{errorMessage || "Connection failed"}</span>
    </div>
  );
};
