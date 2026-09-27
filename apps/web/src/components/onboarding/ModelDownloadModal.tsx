import React, { useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, Download, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getModelPullStatusApi, startModelPullApi } from "./onboarding-api";
import { ModelPullProgressResponse } from "./types";

interface ModelDownloadModalProps {
  modelName: string;
  engine?: string;
  baseUrl?: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const ModelDownloadModal: React.FC<ModelDownloadModalProps> = ({
  modelName,
  engine = "ollama",
  baseUrl,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [progress, setProgress] = useState<ModelPullProgressResponse | null>(null);

  useEffect(() => {
    if (!isOpen || !modelName) return;

    let timer: NodeJS.Timeout;
    let isCancelled = false;

    const runDownload = async () => {
      try {
        const startRes = await startModelPullApi(modelName, engine, baseUrl);
        if (isCancelled) return;
        setProgress(startRes);

        const pollStatus = async () => {
          try {
            const statusRes = await getModelPullStatusApi(startRes.job_id);
            if (isCancelled) return;
            setProgress(statusRes);

            if (statusRes.status === "ready") {
              onSuccess();
            } else if (statusRes.status !== "failed") {
              timer = setTimeout(pollStatus, 800);
            }
          } catch {
            if (!isCancelled) {
              setProgress((prev) => prev ? { ...prev, status: "failed", error: "Connection lost to download worker" } : null);
            }
          }
        };
        timer = setTimeout(pollStatus, 800);
      } catch (err: unknown) {
        if (!isCancelled) {
          setProgress({
            job_id: "error",
            model_name: modelName,
            engine,
            status: "failed",
            completed_bytes: 0,
            total_bytes: 0,
            percentage: 0,
            error: err instanceof Error ? err.message : "Failed to initiate model pull",
          });
        }
      }
    };

    runDownload();

    return () => {
      isCancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [isOpen, modelName, engine, baseUrl, onSuccess]);

  if (!isOpen) return null;

  const isReady = progress?.status === "ready";
  const isFailed = progress?.status === "failed";
  const completedMb = progress ? Math.round(progress.completed_bytes / (1024 * 1024)) : 0;
  const totalMb = progress ? Math.round(progress.total_bytes / (1024 * 1024)) : 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
      <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-md w-full p-5 space-y-4 animate-in fade-in zoom-in-95">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded bg-slate-900 text-white flex items-center justify-center">
              <Download className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900">In-Platform Model Downloader</h3>
              <p className="text-[11px] text-slate-500 font-mono truncate">{modelName}</p>
            </div>
          </div>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-mono text-slate-600">
            <span>{progress?.status_text || "Pulling manifest..."}</span>
            <span>{progress ? `${progress.percentage}%` : "0%"}</span>
          </div>
          <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
            <div
              className="h-full bg-slate-900 transition-all duration-300 rounded-full"
              style={{ width: `${progress ? progress.percentage : 0}%` }}
            />
          </div>
          {totalMb > 0 && (
            <div className="text-[10px] text-slate-400 font-mono text-right">
              {completedMb}MB / {totalMb}MB
            </div>
          )}
        </div>

        {/* Status Callout */}
        {isReady && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-2 text-xs text-emerald-900">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>Model downloaded and verified on local daemon!</span>
          </div>
        )}
        {isFailed && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-2 text-xs text-rose-900">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold">Download Failed</div>
              <div className="text-[11px] text-rose-700">{progress?.error || "Could not complete pull."}</div>
            </div>
          </div>
        )}

        {/* Action */}
        <div className="flex justify-end pt-2">
          {isReady ? (
            <Button onClick={onClose} size="sm" className="bg-emerald-800 hover:bg-emerald-900 text-white">
              <span>Select Model</span>
            </Button>
          ) : isFailed ? (
            <Button onClick={onClose} variant="outline" size="sm">
              <span>Close</span>
            </Button>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-slate-500 font-mono">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Streaming bytes...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
