"use client";

import { useEffect, useState, useCallback } from "react";
import { apiFetch } from "@/lib/api-client";
import { DocumentItem } from "@/types";

export function useDocuments(projectId: string) {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isUploading, setIsUploading] = useState<boolean>(false);

  const fetchDocuments = useCallback(async () => {
    if (!projectId) return;
    try {
      const data = await apiFetch<{ items: DocumentItem[]; total: number }>(
        `/projects/${projectId}/documents`
      );
      setDocuments(data.items);
    } catch {
      // Handle error gracefully
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchDocuments();
    const interval = setInterval(fetchDocuments, 4000);
    return () => clearInterval(interval);
  }, [fetchDocuments]);

  const uploadFiles = async (files: File[]) => {
    setIsUploading(true);
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    try {
      await apiFetch(`/projects/${projectId}/documents`, {
        method: "POST",
        body: formData,
      });
      await fetchDocuments();
    } finally {
      setIsUploading(false);
    }
  };

  const deleteDocument = async (docId: string) => {
    await apiFetch(`/projects/${projectId}/documents/${docId}`, {
      method: "DELETE",
    });
    await fetchDocuments();
  };

  const getViewerUrl = async (docId: string): Promise<string> => {
    const res = await apiFetch<{ url: string }>(
      `/projects/${projectId}/documents/${docId}/content`
    );
    return res.url;
  };

  return { documents, isLoading, isUploading, uploadFiles, deleteDocument, getViewerUrl, refresh: fetchDocuments };
}
