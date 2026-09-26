import React from "react";
import { Loader2, MessageSquare } from "lucide-react";
import { ChatMessage, Citation } from "@/types";
import { MessageItem } from "./message-item";

export interface MessageListProps {
  messages: ChatMessage[];
  currentStage?: string | null;
  onCitationClick?: (citation: Citation) => void;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  currentStage = null,
  onCitationClick,
}) => {
  const getStageLabel = (stage: string) => {
    switch (stage) {
      case "retrieving":
        return "Retrieving relevant document chunks (BM25 + Dense)...";
      case "reranking":
        return "Reranking candidates with cross-encoder...";
      case "generating":
        return "Generating grounded answer from context...";
      case "verifying":
        return "Verifying factual faithfulness and citations...";
      default:
        return "Processing request...";
    }
  };

  if (messages.length === 0 && !currentStage) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8 text-center text-slate-500">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 mb-3">
          <MessageSquare className="h-6 w-6 text-slate-400" />
        </div>
        <h3 className="text-sm font-semibold text-slate-700">No messages yet</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm">
          Ask any question regarding your indexed documents. Answers will include evidence-backed citations.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-2 space-y-2">
      {messages.map((msg) => (
        <MessageItem
          key={msg.id}
          message={msg}
          onCitationClick={onCitationClick}
        />
      ))}

      {currentStage && (
        <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded-lg p-3 my-2 animate-pulse">
          <Loader2 className="h-3.5 w-3.5 animate-spin text-slate-700" />
          <span>{getStageLabel(currentStage)}</span>
        </div>
      )}
    </div>
  );
};
