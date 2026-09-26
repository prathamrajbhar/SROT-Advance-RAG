"use client";

import React from "react";
import { FolderKanban, FileCheck, Database, CheckCircle2 } from "lucide-react";
import { Project } from "@/types";

interface WorkspacesStatsBarProps {
  projects: Project[];
}

export const WorkspacesStatsBar: React.FC<WorkspacesStatsBarProps> = ({ projects }) => {
  const totalDocs = projects.reduce((acc, p) => acc + (p.document_count || 0), 0);
  const totalChunks = projects.reduce((acc, p) => acc + (p.total_chunks || 0), 0);

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div className="rounded-xl bg-white border border-slate-200/90 p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
            <FolderKanban className="h-4 w-4" />
          </div>
          <div>
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">
              Workspaces
            </span>
            <span className="text-xl font-bold text-slate-900">{projects.length}</span>
          </div>
        </div>
      </div>

      <div className="rounded-xl bg-white border border-slate-200/90 p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
            <FileCheck className="h-4 w-4" />
          </div>
          <div>
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">
              Knowledge Docs
            </span>
            <span className="text-xl font-bold text-slate-900">{totalDocs}</span>
          </div>
        </div>
      </div>

      <div className="rounded-xl bg-white border border-slate-200/90 p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
            <Database className="h-4 w-4" />
          </div>
          <div>
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">
              Vector Chunks
            </span>
            <span className="text-xl font-bold text-slate-900">{totalChunks}</span>
          </div>
        </div>
      </div>

      <div className="rounded-xl bg-white border border-slate-200/90 p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
            <CheckCircle2 className="h-4 w-4" />
          </div>
          <div>
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">
              System Health
            </span>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-bold text-slate-900">All Nodes Online</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
