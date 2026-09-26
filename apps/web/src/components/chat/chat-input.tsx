"use client";

import React, { useState, useRef, useEffect } from "react";
import { ArrowUp, Bug, Sparkles, Loader2 } from "lucide-react";

export interface ChatInputProps {
  onSend?: (message: string, debug: boolean) => void;
  onSendMessage?: (message: string, debug?: boolean) => void;
  disabled?: boolean;
  isStreaming?: boolean;
  currentStage?: string | null;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  onSendMessage,
  disabled = false,
  isStreaming = false,
  currentStage,
}) => {
  const [content, setContent] = useState("");
  const [debug, setDebug] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isDisabled = disabled || isStreaming;

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 140)}px`;
    }
  }, [content]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!content.trim() || isDisabled) return;
    const trimmed = content.trim();
    if (onSendMessage) {
      onSendMessage(trimmed, debug);
    } else if (onSend) {
      onSend(trimmed, debug);
    }
    setContent("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full">
      {isStreaming && currentStage && (
        <div className="flex items-center gap-2 mb-2 px-1 text-[11px] font-medium text-slate-500 animate-pulse">
          <Loader2 className="h-3 w-3 animate-spin text-slate-700" />
          <span className="capitalize">{currentStage}...</span>
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="relative rounded-2xl border border-slate-200/90 bg-white shadow-xs focus-within:border-slate-400 focus-within:ring-2 focus-within:ring-slate-900/5 transition-all p-3"
      >
        <textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your knowledge base..."
          rows={1}
          disabled={isDisabled}
          className="w-full resize-none bg-transparent text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none disabled:opacity-50 min-h-[24px] max-h-[140px] leading-relaxed"
        />

        <div className="flex items-center justify-between pt-2 border-t border-slate-100 mt-1">
          <button
            type="button"
            onClick={() => setDebug((prev) => !prev)}
            className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] font-medium transition-colors ${
              debug
                ? "bg-slate-900 text-white"
                : "text-slate-400 hover:text-slate-700 hover:bg-slate-100"
            }`}
            title="Toggle retrieval ranking inspection"
          >
            <Bug className="h-3 w-3" />
            <span>Debug Ranking</span>
          </button>

          <div className="flex items-center gap-2.5">
            <span className="text-[10px] text-slate-400 hidden sm:inline select-none">
              Enter to send, Shift+Enter for new line
            </span>
            <button
              type="submit"
              disabled={!content.trim() || isDisabled}
              className={`flex h-7 w-7 items-center justify-center rounded-lg transition-all ${
                content.trim() && !isDisabled
                  ? "bg-slate-900 text-white shadow-xs hover:bg-slate-800"
                  : "bg-slate-100 text-slate-300 cursor-not-allowed"
              }`}
              aria-label="Send message"
            >
              {isStreaming ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <ArrowUp className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
