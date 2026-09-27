"use client";

import React, { useEffect, useState, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Search,
  Layers,
  Copy,
  Check,
  Download,
  ShieldAlert,
  ShieldCheck,
  FileText,
  Clock,
  Hash,
  Database,
  ExternalLink,
} from "lucide-react";
import { apiFetch, ApiError } from "@/lib/api-client";
import { DocumentChunksResponse, ChunkItem } from "@/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/components/ui/toast";
import { formatBytes } from "@/lib/utils";

export default function DocumentChunksPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params?.id as string;
  const docId = params?.docId as string;

  const [data, setData] = useState<DocumentChunksResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedKind, setSelectedKind] = useState<string>("all");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    async function loadChunks() {
      if (!projectId || !docId) return;
      setIsLoading(true);
      setError(null);
      try {
        const res = await apiFetch<DocumentChunksResponse>(
          `/projects/${projectId}/documents/${docId}/chunks`
        );
        setData(res);
      } catch (err: unknown) {
        const msg = err instanceof ApiError ? err.detail : "Failed to load document chunks";
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    }
    loadChunks();
  }, [projectId, docId]);

  const kinds = useMemo(() => {
    if (!data?.chunks) return [];
    const set = new Set(data.chunks.map((c) => c.kind));
    return Array.from(set);
  }, [data]);

  const filteredChunks = useMemo(() => {
    if (!data?.chunks) return [];
    return data.chunks.filter((chunk) => {
      const matchesSearch =
        searchQuery === "" ||
        chunk.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
        String(chunk.chunk_index).includes(searchQuery);
      const matchesKind = selectedKind === "all" || chunk.kind === selectedKind;
      return matchesSearch && matchesKind;
    });
  }, [data, searchQuery, selectedKind]);

  const copyContent = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    toast.success("Chunk content copied to clipboard");
    setTimeout(() => setCopiedId(null), 2000);
  };

  const exportJson = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${data.document.filename}-chunks.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Exported chunks to JSON");
  };

  if (isLoading) {
    return (
      <div className="flex-1 overflow-y-auto bg-slate-50 p-6 space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-32 w-full rounded-2xl" />
        <div className="space-y-4">
          <Skeleton className="h-28 w-full rounded-xl" />
          <Skeleton className="h-28 w-full rounded-xl" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 bg-slate-50 text-center">
        <div className="h-12 w-12 rounded-2xl bg-rose-100 text-rose-600 flex items-center justify-center mb-4">
          <Layers className="h-6 w-6" />
        </div>
        <h2 className="text-lg font-bold text-slate-900 mb-1">Failed to load chunks</h2>
        <p className="text-xs text-slate-500 mb-6 max-w-sm">{error || "Document not found"}</p>
        <Button onClick={() => router.push(`/projects/${projectId}/documents`)} size="sm">
          <ArrowLeft className="h-3.5 w-3.5 mr-1.5" /> Back to Documents
        </Button>
      </div>
    );
  }

  const { document: doc } = data;

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-slate-50 overflow-hidden">
      {/* Header Bar */}
      <header className="border-b border-slate-200/80 bg-white px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            href={`/projects/${projectId}/documents`}
            className="p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            title="Back to Documents"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-slate-900 truncate max-w-md">
                {doc.filename}
              </h1>
              <Badge variant="secondary" className="text-[10px] uppercase font-mono">
                {data.total_chunks} Chunks
              </Badge>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Chunk breakdown &amp; vector embedding inspector
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={exportJson}
            className="text-xs gap-1.5 border-slate-200"
          >
            <Download className="h-3.5 w-3.5" /> Export JSON
          </Button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto p-6 max-w-6xl w-full mx-auto space-y-6">
        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-3 rounded-xl border border-slate-200/80 shadow-sm">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search in chunk text..."
              className="w-full pl-9 pr-4 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-slate-900 bg-slate-50/50"
            />
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto text-xs">
            <button
              onClick={() => setSelectedKind("all")}
              className={`px-3 py-1 rounded-md capitalize font-medium transition-colors ${
                selectedKind === "all" ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              All ({data.chunks.length})
            </button>
            {kinds.map((k) => (
              <button
                key={k}
                onClick={() => setSelectedKind(k)}
                className={`px-3 py-1 rounded-md font-medium capitalize transition-colors ${
                  selectedKind === k ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {k.replace("_", " ")}
              </button>
            ))}
          </div>
        </div>

        {/* Chunks List */}
        {filteredChunks.length === 0 ? (
          <div className="rounded-2xl border-2 border-dashed border-slate-200 bg-white p-12 text-center">
            <Layers className="h-8 w-8 text-slate-400 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-700">No chunks matched</p>
            <p className="text-xs text-slate-400 mt-1">Try clearing filters or search terms</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredChunks.map((chunk) => {
              const isCopied = copiedId === chunk.id;
              return (
                <div
                  key={chunk.id}
                  className="rounded-xl border border-slate-200/90 bg-white p-4 shadow-sm hover:border-slate-300 transition-all space-y-3"
                >
                  <div className="flex items-center justify-between flex-wrap gap-2 text-xs">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded font-mono text-[11px]">
                        #{chunk.chunk_index + 1}
                      </span>
                      <Badge variant="secondary" className="capitalize text-[10px]">
                        {chunk.kind.replace("_", " ")}
                      </Badge>
                      <span className="text-slate-400 text-[11px] font-mono">
                        {chunk.token_count} tokens
                      </span>
                      {chunk.locator && Object.keys(chunk.locator).length > 0 && (
                        <span className="bg-slate-50 border border-slate-200 text-slate-600 px-2 py-0.5 rounded text-[10px] font-mono">
                          {Object.entries(chunk.locator)
                            .map(([k, v]) => `${k}: ${v}`)
                            .join(" | ")}
                        </span>
                      )}
                    </div>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyContent(chunk.content, chunk.id)}
                      className="h-7 text-xs gap-1 text-slate-500 hover:text-slate-900"
                    >
                      {isCopied ? (
                        <>
                          <Check className="h-3 w-3 text-emerald-600" /> Copied
                        </>
                      ) : (
                        <>
                          <Copy className="h-3 w-3" /> Copy
                        </>
                      )}
                    </Button>
                  </div>

                  <div className="rounded-lg bg-slate-900 p-3.5 text-slate-100 font-mono text-xs leading-relaxed overflow-x-auto whitespace-pre-wrap break-words">
                    {chunk.content}
                  </div>

                  {chunk.embedding_id && (
                    <div className="text-[10px] text-slate-400 font-mono flex items-center gap-2">
                      <span>Vector ID: {chunk.embedding_id}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
