"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Folder, MoreVertical, MessageSquare, FileText, Trash2, Edit3, Shield, ArrowUpRight } from "lucide-react";
import { Project } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface WorkspaceCardProps {
  project: Project;
  onEdit: (project: Project) => void;
  onDelete: (project: Project) => void;
}

export const WorkspaceCard: React.FC<WorkspaceCardProps> = ({ project, onEdit, onDelete }) => {
  const [menuOpen, setMenuOpen] = useState(false);

  const getRoleBadgeVariant = (role?: string): "default" | "success" | "warning" | "danger" | "neutral" => {
    if (role === "owner") return "default";
    if (role === "editor") return "warning";
    return "neutral";
  };

  return (
    <div className="relative group bg-white rounded-xl border border-slate-200/90 shadow-sm hover:shadow-md hover:border-slate-300 transition-all duration-200 flex flex-col justify-between p-5">
      <div>
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-900 text-white shadow-sm group-hover:bg-slate-800 transition-colors">
              <Folder className="h-5 w-5" />
            </div>
            <div>
              <Link
                href={`/projects/${project.id}`}
                className="font-semibold text-slate-900 hover:text-blue-600 transition-colors line-clamp-1 text-base flex items-center gap-1 group-hover:underline"
              >
                {project.name}
                <ArrowUpRight className="h-3.5 w-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
              </Link>
              <div className="flex items-center gap-2 mt-0.5">
                <Badge variant={getRoleBadgeVariant(project.role)} className="capitalize text-[10px] py-0 px-1.5">
                  <Shield className="h-2.5 w-2.5 mr-1 inline" />
                  {project.role || "viewer"}
                </Badge>
              </div>
            </div>
          </div>

          <div className="relative">
            <button
              onClick={() => setMenuOpen((prev) => !prev)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
              aria-label="Workspace options"
            >
              <MoreVertical className="h-4 w-4" />
            </button>

            {menuOpen && (
              <>
                <div className="fixed inset-0 z-20" onClick={() => setMenuOpen(false)} />
                <div className="absolute right-0 top-8 z-30 w-44 rounded-lg bg-white p-1 shadow-lg border border-slate-200 text-xs font-medium text-slate-700">
                  <button
                    onClick={() => {
                      setMenuOpen(false);
                      onEdit(project);
                    }}
                    className="flex w-full items-center gap-2 px-3 py-2 rounded-md hover:bg-slate-50 text-slate-700 hover:text-slate-900 transition-colors"
                  >
                    <Edit3 className="h-3.5 w-3.5" />
                    Edit Workspace
                  </button>
                  {project.role === "owner" && (
                    <button
                      onClick={() => {
                        setMenuOpen(false);
                        onDelete(project);
                      }}
                      className="flex w-full items-center gap-2 px-3 py-2 rounded-md hover:bg-red-50 text-red-600 hover:text-red-700 transition-colors"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Delete Workspace
                    </button>
                  )}
                </div>
              </>
            )}
          </div>
        </div>

        <p className="text-xs text-slate-500 line-clamp-2 min-h-[32px] mb-4">
          {project.description || "No description provided for this workspace."}
        </p>

        <div className="grid grid-cols-2 gap-2 py-2.5 px-3 bg-slate-50/80 rounded-lg border border-slate-100 text-xs mb-4">
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-medium">Documents</span>
            <span className="font-semibold text-slate-800">{project.document_count || 0}</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-medium">Chunks Indexed</span>
            <span className="font-semibold text-slate-800">{project.total_chunks || 0}</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
        <Link href={`/projects/${project.id}`} className="flex-1">
          <Button variant="outline" size="sm" className="w-full justify-center gap-1.5 text-xs text-slate-700 hover:bg-slate-50">
            <MessageSquare className="h-3.5 w-3.5" />
            Open Chat
          </Button>
        </Link>
        <Link href={`/projects/${project.id}/documents`} className="flex-1">
          <Button variant="ghost" size="sm" className="w-full justify-center gap-1.5 text-xs text-slate-600 hover:bg-slate-100">
            <FileText className="h-3.5 w-3.5" />
            Knowledge
          </Button>
        </Link>
      </div>
    </div>
  );
};
