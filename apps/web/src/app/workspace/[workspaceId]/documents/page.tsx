"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Database, Plus, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/toast";
import { DocumentCatalogTable } from "@/components/documents/DocumentCatalogTable";
import { S3MultipartDropzone } from "@/components/documents/S3MultipartDropzone";
import { deleteDocumentApi, listDocumentsApi } from "@/components/documents/documents-api";
import { DocumentItem } from "@/components/documents/types";

export default function WorkspaceDocumentsPage() {
  const params = useParams();
  const workspaceId = params?.workspaceId as string;
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showDropzone, setShowDropzone] = useState(false);

  const fetchDocuments = useCallback(async () => {
    if (!workspaceId) return;
    try {
      const res = await listDocumentsApi(workspaceId);
      setDocuments(res.documents);
    } catch {
      toast.error("Failed to load document catalog", "Network Error");
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleDelete = async (docId: string) => {
    try {
      await deleteDocumentApi(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      toast.success("Document removed from catalog", "Deleted");
    } catch {
      toast.error("Failed to delete document", "Action Failed");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col justify-between">
      <div>
        <header className="border-b border-slate-200 px-6 py-3.5 flex items-center justify-between bg-white shadow-xs">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded bg-slate-900 text-white flex items-center justify-center font-bold text-xs">
              S
            </div>
            <span className="font-bold text-sm tracking-tight text-slate-900">SROT Enterprise</span>
            <span className="text-[10px] font-mono uppercase bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded border border-slate-200 font-medium">
              Document Ingestion
            </span>
          </div>

          <div className="flex items-center gap-3">
            <Link href="/onboarding">
              <Button variant="ghost" size="sm" className="gap-1.5 text-xs text-slate-500">
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Setup Wizard</span>
              </Button>
            </Link>
          </div>
        </header>

        <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-slate-900">Document Catalog</h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Direct-to-S3 multi-modal ingestion pipeline for text, tabular, audio, and video documents.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={fetchDocuments}
                className="gap-1.5 text-xs bg-white"
              >
                <RefreshCw className={isLoading ? "w-3.5 h-3.5 animate-spin" : "w-3.5 h-3.5"} />
                <span>Refresh</span>
              </Button>

              <Button
                size="sm"
                onClick={() => setShowDropzone((prev) => !prev)}
                className="gap-1.5 text-xs bg-slate-900 text-white hover:bg-slate-800"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>{showDropzone ? "Hide Uploader" : "Upload Documents"}</span>
              </Button>
            </div>
          </div>

          {showDropzone && (
            <S3MultipartDropzone
              workspaceId={workspaceId}
              onUploadSuccess={fetchDocuments}
              onClose={() => setShowDropzone(false)}
            />
          )}

          <DocumentCatalogTable
            documents={documents}
            onDelete={handleDelete}
            isLoading={isLoading}
          />
        </main>
      </div>

      <footer className="border-t border-slate-200 px-6 py-4 text-center text-xs text-slate-400">
        SROT Enterprise Multimodal RAG Platform • AES-256-GCM Vault • Tri-Layer Tenant Isolation
      </footer>
    </div>
  );
}
