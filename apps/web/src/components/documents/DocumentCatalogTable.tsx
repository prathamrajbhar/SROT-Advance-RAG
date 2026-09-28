"use client";

import React, { useState } from "react";
import {
  FileSpreadsheet,
  FileText,
  Music,
  Trash2,
  Video,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { DocumentItem } from "./types";

interface DocumentCatalogTableProps {
  documents: DocumentItem[];
  onDelete: (id: string) => Promise<void>;
  isLoading?: boolean;
}

function getModalityIcon(fileType: string) {
  switch (fileType.toLowerCase()) {
    case "tabular": return FileSpreadsheet;
    case "video": return Video;
    case "audio": return Music;
    default: return FileText;
  }
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export const DocumentCatalogTable: React.FC<DocumentCatalogTableProps> = ({
  documents,
  onDelete,
  isLoading,
}) => {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    try {
      await onDelete(id);
    } finally {
      setDeletingId(null);
    }
  };

  if (isLoading && documents.length === 0) {
    return (
      <div className="p-12 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
        <Loader2 className="w-4 h-4 animate-spin text-slate-700" />
        <span>Loading catalog...</span>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="p-12 text-center text-xs text-slate-400 border border-slate-200 rounded-xl bg-white">
        No documents uploaded yet. Drag and drop files above to begin ingestion.
      </div>
    );
  }

  return (
    <div className="border border-slate-200 rounded-xl bg-white shadow-xs overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-medium">
            <tr>
              <th className="px-4 py-3 font-semibold">Document</th>
              <th className="px-4 py-3 font-semibold">Modality</th>
              <th className="px-4 py-3 font-semibold">Size</th>
              <th className="px-4 py-3 font-semibold">Status</th>
              <th className="px-4 py-3 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {documents.map((doc) => {
              const Icon = getModalityIcon(doc.file_type);
              const isDeleting = deletingId === doc.id;
              const isProcessing = ["QUEUED", "EXTRACTING", "CHUNKING", "INDEXING"].includes(doc.job_stage || "");

              return (
                <tr key={doc.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2.5 truncate max-w-xs sm:max-w-md">
                      <div className="w-7 h-7 rounded bg-slate-100 text-slate-700 flex items-center justify-center shrink-0">
                        <Icon className="w-3.5 h-3.5" />
                      </div>
                      <div className="truncate">
                        <div className="font-medium text-slate-900 truncate">{doc.filename}</div>
                        <div className="text-[10px] text-slate-400 font-mono">
                          {new Date(doc.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  </td>

                  <td className="px-4 py-3 font-mono capitalize text-[11px] text-slate-600">
                    {doc.file_type}
                  </td>

                  <td className="px-4 py-3 font-mono text-[11px] text-slate-600">
                    {formatBytes(doc.file_size_bytes)}
                  </td>

                  <td className="px-4 py-3">
                    {doc.status === "READY" && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full">
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        Ready ({doc.chunk_count} chunks)
                      </span>
                    )}
                    {isProcessing && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-full animate-pulse">
                        <Loader2 className="w-3 h-3 animate-spin text-blue-600" />
                        {doc.job_stage} ({doc.job_progress || 0}%)
                      </span>
                    )}
                    {doc.status === "UPLOADED" && !isProcessing && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full">
                        <Clock className="w-3 h-3 text-amber-600" />
                        Uploaded (Pending)
                      </span>
                    )}
                    {doc.status === "FAILED" && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-medium bg-rose-50 text-rose-700 border border-rose-200 px-2 py-0.5 rounded-full">
                        <AlertTriangle className="w-3 h-3 text-rose-600" />
                        Failed
                      </span>
                    )}
                  </td>

                  <td className="px-4 py-3 text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(doc.id)}
                      disabled={isDeleting}
                      className="h-7 w-7 p-0 text-slate-400 hover:text-rose-600"
                    >
                      {isDeleting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                    </Button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
