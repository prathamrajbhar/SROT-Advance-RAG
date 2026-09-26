"use client";

import React, { useState } from "react";
import { AlertTriangle, Trash2, X } from "lucide-react";
import { Project } from "@/types";
import { Button } from "@/components/ui/button";

interface WorkspaceDeleteDialogProps {
  isOpen: boolean;
  project: Project | null;
  onClose: () => void;
  onConfirm: (projectId: string) => Promise<void>;
}

export const WorkspaceDeleteDialog: React.FC<WorkspaceDeleteDialogProps> = ({
  isOpen,
  project,
  onClose,
  onConfirm,
}) => {
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !project) return null;

  const handleDelete = async () => {
    setIsDeleting(true);
    setError(null);
    try {
      await onConfirm(project.id);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete workspace");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 animate-in fade-in">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-slate-100">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-100 text-red-600">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-900">Delete Workspace</h3>
              <p className="text-xs text-slate-500">This action is permanent and cannot be undone</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-4 rounded-lg bg-red-50 p-3.5 text-xs text-red-700 border border-red-200/80 leading-relaxed">
          Are you sure you want to delete <span className="font-semibold">{project.name}</span>? All indexed vector embeddings in Qdrant, uploaded source documents in S3, and chat histories will be deleted immediately.
        </div>

        {error && (
          <div className="mt-3 rounded-lg bg-red-100 p-2.5 text-xs text-red-800">
            {error}
          </div>
        )}

        <div className="mt-6 flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onClose}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            type="button"
            size="sm"
            onClick={handleDelete}
            disabled={isDeleting}
            className="bg-red-600 hover:bg-red-700 text-white min-w-[120px]"
          >
            <Trash2 className="h-3.5 w-3.5 mr-1.5" />
            {isDeleting ? "Deleting..." : "Delete Forever"}
          </Button>
        </div>
      </div>
    </div>
  );
};
