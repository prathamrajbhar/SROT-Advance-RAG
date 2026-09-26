"use client";

import { useEffect, useState, useCallback } from "react";
import { getAccessToken, apiFetch } from "@/lib/api-client";
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
      setMessages(data.items || []);
    } catch {
      // Handle gracefully
    } finally {
      setIsLoadingHistory(false);
    }
  }, [conversationId]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const sendMessage = async (content: string, debug: boolean = false) => {
    if (!conversationId || !content.trim() || isStreaming) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content_md: content,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
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
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/conversations/${conversationId}/messages`,
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
                },
              ];
            });
          }
        }
      }
    } catch (err) {
      setCurrentStage(null);
    } finally {
      setIsStreaming(false);
      setCurrentStage(null);
    }
  };

  return { messages, setMessages, isStreaming, isLoadingHistory, currentStage, sendMessage, refreshHistory: fetchHistory };
}
