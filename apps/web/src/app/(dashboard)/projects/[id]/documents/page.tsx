"use client";

import React, { useEffect, useState, useMemo, use } from "react";
import { Search, FolderOpen, RefreshCw } from "lucide-react";
import { apiFetch } from "@/lib/api-client";
import { Citation, Project, DocumentItem } from "@/types";
import { useDocuments } from "@/hooks/use-documents";
import { ProjectHeader } from "@/components/project/project-header";
import { FileDropzone } from "@/components/upload/file-dropzone";
import { DocumentTable } from "@/components/documents/document-table";
import { DocumentDeleteDialog } from "@/components/documents/document-delete-dialog";
import { DocumentViewerModal } from "@/components/viewer/document-viewer-modal";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export default function ProjectDocumentsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;

  const [project, setProject] = useState<Project | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [deletingDoc, setDeletingDoc] = useState<DocumentItem | null>(null);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [viewerUrl, setViewerUrl] = useState<string | null>(null);

  const {
    documents,
    isLoading: isDocsLoading,
    isUploading,
    uploadFiles,
    deleteDocument,
    getViewerUrl,
    refresh,
  } = useDocuments(projectId);

  useEffect(() => {
    async function loadProject() {
      if (!projectId) return;
      try {
        const projData = await apiFetch<Project>(`/projects/${projectId}`);
        setProject(projData);
      } catch {
        // Handle gracefully
      }
    }
    loadProject();
  }, [projectId]);

  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      const matchesSearch = doc.filename.toLowerCase().includes(search.toLowerCase());
      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "processing"
          ? ["queued", "parsing", "chunking", "embedding", "indexing"].includes(doc.status)
          : doc.status === statusFilter);
      return matchesSearch && matchesStatus;
    });
  }, [documents, search, statusFilter]);

  const handleView = async (docId: string) => {
    const doc = documents.find((d) => d.id === docId);
    if (!doc) return;
    try {
      const url = await getViewerUrl(docId);
      setViewerUrl(url);
      setSelectedCitation({
        index: 1,
        chunk_id: docId,
        document_id: docId,
        document_name: doc.filename,
        snippet: `Viewing document: ${doc.filename}`,
      });
    } catch {
      // Handle error gracefully
    }
  };

  if (!project) {
    return (
      <div className="flex h-full flex-col bg-slate-50">
        <div className="h-16 border-b border-slate-200 bg-white p-4">
          <Skeleton className="h-6 w-48" />
        </div>
        <div className="flex-1 p-6 space-y-4">
          <Skeleton className="h-32 w-full rounded-2xl" />
          <Skeleton className="h-64 w-full rounded-2xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-slate-50 overflow-y-auto">
      <ProjectHeader project={project} />

      <div className="p-6 md:p-8 space-y-6 max-w-6xl w-full mx-auto">
        <FileDropzone onFilesSelected={uploadFiles} isUploading={isUploading} />

        <div className="space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Knowledge Repository</h3>
              <p className="text-xs text-slate-500">
                {documents.length} source {documents.length === 1 ? "document" : "documents"} indexed in vector store
              </p>
            </div>

            <div className="flex items-center gap-2">
              <div className="relative w-48">
                <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
                <Input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Filter by name..."
                  className="pl-8 h-8 text-xs bg-white"
                />
              </div>

              <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs">
                {["all", "indexed", "processing", "failed"].map((f) => (
                  <button
                    key={f}
                    onClick={() => setStatusFilter(f)}
                    className={`px-2.5 py-1 rounded-md capitalize text-[11px] font-medium transition-colors ${
                      statusFilter === f
                        ? "bg-white text-slate-900 shadow-sm"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => refresh()}
                className="h-8 px-2 text-slate-600 hover:text-slate-900"
                title="Refresh Documents"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>

          {filteredDocuments.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
              <FolderOpen className="h-8 w-8 mx-auto text-slate-400 mb-2" />
              <p className="text-xs font-semibold text-slate-800">
                {search ? "No matching documents found" : "No documents in this workspace yet"}
              </p>
              <p className="text-[11px] text-slate-400 mt-1">
                {search ? "Try a different search query" : "Upload files above to begin semantic indexing"}
              </p>
            </div>
          ) : (
            <DocumentTable
              documents={filteredDocuments}
              projectId={projectId}
              onView={handleView}
              onDelete={(doc) => setDeletingDoc(doc)}
            />
          )}
        </div>
      </div>

      <DocumentDeleteDialog
        isOpen={!!deletingDoc}
        document={deletingDoc}
        onClose={() => setDeletingDoc(null)}
        onConfirm={async (docId) => {
          await deleteDocument(docId);
        }}
      />

      <DocumentViewerModal
        isOpen={!!selectedCitation}
        onClose={() => {
          setSelectedCitation(null);
          setViewerUrl(null);
        }}
        citation={selectedCitation}
        documentUrl={viewerUrl}
      />
    </div>
  );
}
