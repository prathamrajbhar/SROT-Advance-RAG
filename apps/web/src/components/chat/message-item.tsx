"use client";

import React from "react";
import { Bot, User, Clock, DollarSign, Cpu } from "lucide-react";
import { ChatMessage, Citation } from "@/types";
import { CitationChip } from "./citation-chip";
import { ConfidenceDial } from "./confidence-dial";
import { VerdictPill } from "./verdict-pill";
import { MarkdownRenderer } from "./markdown-renderer";

export interface MessageItemProps {
  message: ChatMessage;
  onCitationClick?: (citation: Citation) => void;
}

export const MessageItem: React.FC<MessageItemProps> = ({
  message,
  onCitationClick,
}) => {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"} my-4 group`}>
      {!isUser && (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-900 text-white shadow-xs mt-0.5">
          <Bot className="h-4 w-4" />
        </div>
      )}

      <div className={`max-w-[85%] sm:max-w-[80%] ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`px-4 py-3 rounded-2xl ${
            isUser
              ? "bg-slate-900 text-white rounded-tr-xs shadow-xs"
              : "bg-white text-slate-900 rounded-tl-xs border border-slate-200/90 shadow-xs"
          }`}
        >
          <div className="text-sm break-words leading-relaxed">
            {isUser ? (
              <p className="whitespace-pre-wrap text-slate-100">{message.content_md}</p>
            ) : (
              <MarkdownRenderer content={message.content_md} />
            )}
          </div>

          {message.searched_documents && message.searched_documents.length > 0 && (
            <div className="mt-3 pt-2.5 border-t border-slate-100 text-xs text-slate-500">
              <span className="font-semibold text-slate-700">Searched Documents:</span>
              <ul className="list-disc list-inside mt-1 space-y-0.5">
                {message.searched_documents.map((d) => (
                  <li key={d.document_id} className="text-slate-600">{d.filename}</li>
                ))}
              </ul>
            </div>
          )}

          {!isUser && message.citations && message.citations.length > 0 && (
            <div className="mt-3 pt-2.5 border-t border-slate-100 flex flex-wrap items-center gap-1.5">
              <span className="text-xs font-semibold text-slate-600 mr-1">Sources:</span>
              {message.citations.map((c) => (
                <CitationChip
                  key={c.chunk_id}
                  citation={c}
                  onClick={(cit) => onCitationClick?.(cit)}
                />
              ))}
            </div>
          )}

          {!isUser && message.verdict && (
            <div className="mt-3 pt-2.5 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
              <div className="flex items-center gap-2">
                <VerdictPill verdict={message.verdict} />
                {message.confidence !== undefined && (
                  <ConfidenceDial score={message.confidence} />
                )}
              </div>

              <div className="flex items-center gap-3 text-[11px] text-slate-500">
                {message.latency_ms !== undefined && (
                  <span className="inline-flex items-center gap-1 text-slate-600">
                    <Clock className="h-3 w-3 text-slate-400" />
                    {message.latency_ms}ms
                  </span>
                )}
                {message.cost_usd !== undefined && message.cost_usd > 0 && (
                  <span className="inline-flex items-center gap-1 text-slate-600">
                    <DollarSign className="h-3 w-3 text-slate-400" />
                    ${message.cost_usd.toFixed(5)}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {isUser && (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-200 text-slate-700 mt-0.5 font-semibold text-xs">
          <User className="h-3.5 w-3.5" />
        </div>
      )}
    </div>
  );
};
