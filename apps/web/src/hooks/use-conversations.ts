"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { Conversation } from "@/types";

export function useConversations(projectId: string) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchConversations = useCallback(async () => {
    if (!projectId) return;
    try {
      const data = await apiFetch<Conversation[]>(`/projects/${projectId}/conversations`);
      setConversations(data);
      if (data.length > 0) {
        setActiveConversationId((prev) => {
          if (prev && data.some((c) => c.id === prev)) return prev;
          return data[0].id;
        });
      } else {
        setActiveConversationId(null);
      }
    } catch {
      // Graceful error handling
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const createConversation = async (title?: string): Promise<string> => {
    const res = await apiFetch<{ id: string }>(`/projects/${projectId}/conversations`, {
      method: "POST",
      body: JSON.stringify({ title: title || "New Chat" }),
    });
    await fetchConversations();
    setActiveConversationId(res.id);
    return res.id;
  };

  const updateConversationTitle = async (convId: string, title: string): Promise<void> => {
    await apiFetch(`/conversations/${convId}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    });
    await fetchConversations();
  };

  const deleteConversation = async (convId: string): Promise<void> => {
    await apiFetch(`/conversations/${convId}`, { method: "DELETE" });
    const remaining = conversations.filter((c) => c.id !== convId);
    setConversations(remaining);
    if (activeConversationId === convId) {
      setActiveConversationId(remaining.length > 0 ? remaining[0].id : null);
    }
  };

  return {
    conversations,
    activeConversationId,
    setActiveConversationId,
    isLoading,
    createConversation,
    updateConversationTitle,
    deleteConversation,
    refresh: fetchConversations,
  };
}
