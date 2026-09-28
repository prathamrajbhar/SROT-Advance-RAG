"use client";

import React, { useRef, useState } from "react";
import { AlertCircle, CheckCircle2, FileUp, Loader2, UploadCloud, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { uploadFileDirectToS3 } from "@/lib/s3-multipart-uploader";
import { cn } from "@/lib/utils";
import { FileUploadTask } from "./types";

interface S3MultipartDropzoneProps {
  workspaceId: string;
  onUploadSuccess?: () => void;
  onClose?: () => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

export const S3MultipartDropzone: React.FC<S3MultipartDropzoneProps> = ({
  workspaceId,
  onUploadSuccess,
  onClose,
}) => {
  const [tasks, setTasks] = useState<FileUploadTask[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const startUpload = async (file: File) => {
    const taskId = `${file.name}-${Date.now()}`;
    const newTask: FileUploadTask = {
      id: taskId,
      file,
      status: "uploading",
      progressPercent: 0,
      uploadedBytes: 0,
      totalBytes: file.size,
    };
    setTasks((prev) => [newTask, ...prev]);

    try {
      await uploadFileDirectToS3(workspaceId, file, (percent, uploaded, total) => {
        setTasks((prev) =>
          prev.map((t) =>
            t.id === taskId
              ? { ...t, progressPercent: percent, uploadedBytes: uploaded, totalBytes: total, status: percent === 100 ? "completed" : "uploading" }
              : t,
          ),
        );
      });
      if (onUploadSuccess) onUploadSuccess();
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Upload failed";
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? { ...t, status: "error", error: errorMsg } : t)),
      );
    }
  };

  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    Array.from(files).forEach((file) => startUpload(file));
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">Direct-to-S3 Multipart Ingestion</h3>
          <p className="text-xs text-slate-500">Multi-gigabyte parallel 10MB chunk uploads without server proxying</p>
        </div>
        {onClose && (
          <Button variant="ghost" size="sm" onClick={onClose} className="h-7 w-7 p-0">
            <X className="w-4 h-4 text-slate-400" />
          </Button>
        )}
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setIsDragOver(false); handleFiles(e.dataTransfer.files); }}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          "border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors flex flex-col items-center justify-center gap-2",
          isDragOver ? "border-slate-900 bg-slate-50" : "border-slate-300 hover:border-slate-400 bg-slate-50/50",
        )}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center">
          <UploadCloud className="w-5 h-5" />
        </div>
        <div>
          <span className="text-xs font-semibold text-slate-800">Click to upload</span>
          <span className="text-xs text-slate-500"> or drag and drop files here</span>
        </div>
        <p className="text-[11px] text-slate-400 font-mono">
          PDF, DOCX, XLSX, CSV, MP4, MP3 up to 5GB per file
        </p>
      </div>

      {tasks.length > 0 && (
        <div className="space-y-2 pt-2 max-h-56 overflow-y-auto">
          {tasks.map((task) => (
            <div key={task.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 truncate pr-2">
                  <FileUp className="w-4 h-4 text-slate-500 shrink-0" />
                  <span className="font-medium text-slate-800 truncate">{task.file.name}</span>
                  <span className="text-[10px] text-slate-400 font-mono">({formatBytes(task.totalBytes)})</span>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  {task.status === "uploading" && <Loader2 className="w-3.5 h-3.5 animate-spin text-slate-700" />}
                  {task.status === "completed" && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />}
                  {task.status === "error" && <AlertCircle className="w-3.5 h-3.5 text-rose-600" />}
                  <span className="font-mono text-[11px] font-semibold text-slate-700">{task.progressPercent}%</span>
                </div>
              </div>

              <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                <div
                  className={cn(
                    "h-full transition-all duration-200 rounded-full",
                    task.status === "completed" ? "bg-emerald-600" : task.status === "error" ? "bg-rose-600" : "bg-slate-900",
                  )}
                  style={{ width: `${task.progressPercent}%` }}
                />
              </div>

              {task.error && <p className="text-[11px] text-rose-600">{task.error}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
