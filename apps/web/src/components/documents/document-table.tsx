"use client";

import React from "react";
import Link from "next/link";
import {
  FileText,
  FileSpreadsheet,
  FileCode,
  FileAudio,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ExternalLink,
  Trash2,
  ShieldCheck,
  ShieldAlert,
  Layers,
} from "lucide-react";
import { DocumentItem } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatBytes } from "@/lib/utils";

interface DocumentTableProps {
  documents: DocumentItem[];
  projectId?: string;
  onView: (id: string) => void;
  onDelete: (doc: DocumentItem) => void;
}

export const DocumentTable: React.FC<DocumentTableProps> = ({
  documents,
  projectId,
  onView,
  onDelete,
}) => {
  const getFileIcon = (filename: string) => {
    const ext = filename.split(".").pop()?.toLowerCase();
    if (ext === "csv" || ext === "xlsx" || ext === "xls") {
      return <FileSpreadsheet className="h-4 w-4 text-emerald-600" />;
    }
    if (ext === "md" || ext === "txt" || ext === "json") {
      return <FileCode className="h-4 w-4 text-blue-600" />;
    }
    if (ext === "mp3" || ext === "wav" || ext === "m4a") {
      return <FileAudio className="h-4 w-4 text-purple-600" />;
    }
    return <FileText className="h-4 w-4 text-slate-700" />;
  };

  const getStatusBadge = (doc: DocumentItem) => {
    switch (doc.status) {
      case "indexed":
        return (
          <Badge variant="success" className="text-[11px] py-0.5 px-2">
            <CheckCircle2 className="h-3 w-3 mr-1 inline" /> Indexed
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="danger" className="text-[11px] py-0.5 px-2">
            <AlertTriangle className="h-3 w-3 mr-1 inline" /> Failed
          </Badge>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-0.5 text-[11px] font-medium text-amber-700 border border-amber-200">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse" />
            <span className="capitalize">{doc.status}</span>
          </span>
        );
    }
  };

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200/90 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-xs">
          <thead className="bg-slate-50 text-slate-700 font-semibold uppercase tracking-wider text-[10px]">
            <tr>
              <th className="py-3.5 pl-4 pr-3 text-left">Document</th>
              <th className="px-3 py-3.5 text-left">Status</th>
              <th className="px-3 py-3.5 text-left">Size</th>
              <th className="px-3 py-3.5 text-left">Chunks</th>
              <th className="px-3 py-3.5 text-left">PII Scan</th>
              <th className="py-3.5 pl-3 pr-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white text-slate-700">
            {documents.map((doc) => (
              <tr key={doc.id} className="hover:bg-slate-50/80 transition-colors">
                <td className="py-3 pl-4 pr-3">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-100">
                      {getFileIcon(doc.filename)}
                    </div>
                    <div className="min-w-0 max-w-xs">
                      <p className="font-semibold text-slate-900 truncate">{doc.filename}</p>
                      <p className="text-[10px] text-slate-400 truncate">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </td>
                <td className="px-3 py-3 whitespace-nowrap">
                  {getStatusBadge(doc)}
                  {doc.error_human && (
                    <p className="text-[10px] text-red-600 truncate max-w-[180px] mt-0.5">
                      {doc.error_human}
                    </p>
                  )}
                </td>
                <td className="px-3 py-3 whitespace-nowrap text-slate-600 font-medium">
                  {formatBytes(doc.size_bytes)}
                </td>
                <td className="px-3 py-3 whitespace-nowrap text-slate-600">
                  {doc.stats?.chunk_count !== undefined ? (
                    <span className="font-semibold text-slate-800">
                      {doc.stats.chunk_count} <span className="text-slate-400 font-normal">chunks</span>
                    </span>
                  ) : (
                    <span className="text-slate-400">-</span>
                  )}
                </td>
                <td className="px-3 py-3 whitespace-nowrap">
                  {doc.pii_flags?.density && doc.pii_flags.density !== "none" ? (
                    <Badge variant="warning" className="text-[10px]">
                      <ShieldAlert className="h-3 w-3 mr-1 inline text-amber-600" />
                      {doc.pii_flags.density} risk
                    </Badge>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[11px] text-emerald-600 font-medium">
                      <ShieldCheck className="h-3 w-3" /> Clear
                    </span>
                  )}
                </td>
                <td className="py-3 pl-3 pr-4 text-right whitespace-nowrap">
                  <div className="flex items-center justify-end gap-1.5">
                    {doc.status === "indexed" && projectId && (
                      <Link
                        href={`/projects/${projectId}/documents/${doc.id}/chunks`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center justify-center h-8 w-8 rounded-lg text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                        title="Inspect All Chunks (New Page)"
                      >
                        <Layers className="h-3.5 w-3.5" />
                      </Link>
                    )}
                    {doc.status === "indexed" && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onView(doc.id)}
                        className="h-8 w-8 p-0 text-slate-500 hover:text-slate-900 hover:bg-slate-100"
                        title="Preview Document"
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onDelete(doc)}
                      className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                      title="Delete Document"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
