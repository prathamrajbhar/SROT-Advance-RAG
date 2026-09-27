"use client";

import { useEffect, useState, useCallback } from "react";
import { getAccessToken, apiFetch } from "@/lib/api-client";
import { API_CONFIG } from "@/config/api";
import { ChatMessage, Citation } from "@/types";

export function useChatStream(conversationId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState<boolean>(false);
  const [currentStage, setCurrentStage] = useState<string | null>(null);

  const fetchHistory = useCallback(async () => {
    if (!conversationId) {
      setMessages([]);
      return;
    }
    setIsLoadingHistory(true);
    try {
      const data = await apiFetch<{ items: ChatMessage[] }>(
        `/conversations/${conversationId}/messages`
      );
      setMessages((prev) => {
        if (!data.items || data.items.length === 0) {
          return prev;
        }
        const seenIds = new Set<string>();
        const merged: ChatMessage[] = [];
        for (const msg of data.items) {
          if (!seenIds.has(msg.id)) {
            seenIds.add(msg.id);
            merged.push(msg);
          }
        }
        for (const msg of prev) {
          const alreadyPresent = merged.some(
            (m) => m.id === msg.id || (m.role === msg.role && m.content_md === msg.content_md)
          );
          if (!alreadyPresent) {
            seenIds.add(msg.id);
            merged.push(msg);
          }
        }
        return merged;
      });
    } catch {
      // Handle gracefully
    } finally {
      setIsLoadingHistory(false);
    }
  }, [conversationId]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const sendMessage = async (
    content: string,
    debug: boolean = false,
    overrideConvId?: string
  ) => {
    const targetConvId = overrideConvId || conversationId;
    if (!targetConvId || !content.trim() || isStreaming) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content_md: content,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => {
      const isRecentDuplicate = prev.some(
        (m) =>
          m.role === "user" &&
          m.content_md === content &&
          Math.abs(Date.now() - new Date(m.created_at).getTime()) < 3000
      );
      if (isRecentDuplicate) return prev;
      return [...prev, userMessage];
    });
    setIsStreaming(true);
    setCurrentStage("retrieving");

    const assistantMsgId = crypto.randomUUID();
    let accumulatedContent = "";
    const citations: Citation[] = [];

    try {
      const token = getAccessToken();
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(
        `${API_CONFIG.baseUrl}/conversations/${targetConvId}/messages`,
        {
          method: "POST",
          headers,
          body: JSON.stringify({ content, debug }),
        }
      );

      if (!res.ok || !res.body) {
        throw new Error("Failed to connect to chat stream");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const block of lines) {
          const eventMatch = block.match(/event:\s*([^\n]+)/);
          const dataMatch = block.match(/data:\s*([^\n]+)/);

          if (!eventMatch || !dataMatch) continue;

          const event = eventMatch[1].trim();
          const data = JSON.parse(dataMatch[1].trim());

          if (event === "status") {
            setCurrentStage(data.stage);
          } else if (event === "token") {
            accumulatedContent += data.t;
            setMessages((prev) => {
              const others = prev.filter((m) => m.id !== assistantMsgId);
              return [
                ...others,
                {
                  id: assistantMsgId,
                  role: "assistant",
                  content_md: accumulatedContent,
                  created_at: new Date().toISOString(),
                  citations: [...citations],
                },
              ];
            });
          } else if (event === "citation") {
            citations.push(data);
          } else if (event === "final") {
            setCurrentStage(null);
            setMessages((prev) => {
              const others = prev.filter((m) => m.id !== assistantMsgId);
              return [
                ...others,
                {
                  id: assistantMsgId,
                  role: "assistant",
                  content_md: data.content_md || accumulatedContent,
                  created_at: new Date().toISOString(),
                  verdict: data.verdict,
                  confidence: data.confidence,
                  faithfulness: data.faithfulness,
                  latency_ms: data.latency_ms,
                  cost_usd: data.cost_usd,
                  model_provider: data.model_provider,
                  model_name: data.model_name,
                  citations: [...citations],
                  searched_documents: data.searched_documents,
                  error_detail: data.error_detail,
                },
              ];
            });
          }
        }
      }
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Failed to connect to chat stream";
      setMessages((prev) => {
        const others = prev.filter((m) => m.id !== assistantMsgId);
        return [
          ...others,
          {
            id: assistantMsgId,
            role: "assistant",
            content_md: "Failed to communicate with the retrieval service. Please check your connection and try again.",
            created_at: new Date().toISOString(),
            verdict: "error",
            confidence: 0,
            error_detail: errorMsg,
          },
        ];
      });
    } finally {
      setIsStreaming(false);
      setCurrentStage(null);
    }
  };

  return {
    messages,
    setMessages,
    isStreaming,
    isLoadingHistory,
    currentStage,
    sendMessage,
    refreshHistory: fetchHistory,
  };
}
