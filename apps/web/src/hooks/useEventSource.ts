"use client";

import { useEffect, useRef } from "react";

export interface SSEEventData {
  document_id: string;
  stage: string;
  progress_percent: number;
  message?: string;
  metadata?: Record<string, unknown>;
  timestamp?: number;
}

export function useEventSource(
  url: string | null,
  onMessage: (data: SSEEventData) => void,
  onError?: (err: Event) => void,
) {
  const onMessageRef = useRef(onMessage);
  const onErrorRef = useRef(onError);
  onMessageRef.current = onMessage;
  onErrorRef.current = onError;

  useEffect(() => {
    if (!url) return;

    const eventSource = new EventSource(url);

    eventSource.addEventListener("progress", (event: MessageEvent) => {
      try {
        const parsed: SSEEventData = JSON.parse(event.data);
        onMessageRef.current(parsed);
      } catch {
        // Silently skip malformed event data
      }
    });

    eventSource.onerror = (event) => {
      if (onErrorRef.current) {
        onErrorRef.current(event);
      }
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [url]);
}
