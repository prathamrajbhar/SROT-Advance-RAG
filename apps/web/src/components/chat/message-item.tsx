"use client";

import React, { useState } from "react";
import { Bot, User, Clock, DollarSign, Copy, Check, Pencil, RotateCw, AlertTriangle, ChevronDown, ChevronUp } from "lucide-react";
import { ChatMessage, Citation } from "@/types";
import { CitationChip } from "./citation-chip";
import { ConfidenceDial } from "./confidence-dial";
import { VerdictPill } from "./verdict-pill";
import { MarkdownRenderer } from "./markdown-renderer";

export interface MessageItemProps {
  message: ChatMessage;
  onCitationClick?: (citation: Citation) => void;
  onRetry?: (queryText: string) => void;
  onEdit?: (messageId: string, newContent: string) => void;
  associatedUserQuery?: string;
}

export const MessageItem: React.FC<MessageItemProps> = ({
  message,
  onCitationClick,
  onRetry,
  onEdit,
  associatedUserQuery,
}) => {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content_md);
  const [showErrorDetail, setShowErrorDetail] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content_md);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSaveEdit = () => {
    if (!editContent.trim() || editContent === message.content_md) {
      setIsEditing(false);
      return;
    }
    onEdit?.(message.id, editContent.trim());
    setIsEditing(false);
  };

  const isError = message.verdict === "error";
  const retryTargetQuery = isUser ? message.content_md : associatedUserQuery || message.content_md;

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"} my-4 group relative`}>
      {!isUser && (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-900 text-white shadow-xs mt-0.5">
          <Bot className="h-4 w-4" />
        </div>
      )}

      <div className={`max-w-[85%] sm:max-w-[80%] flex flex-col ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`px-4 py-3 rounded-2xl transition-all ${
            isUser
              ? "bg-slate-900 text-white rounded-tr-xs shadow-xs"
              : isError
              ? "bg-rose-50/70 border border-rose-200 text-slate-900 rounded-tl-xs shadow-xs"
              : "bg-white text-slate-900 rounded-tl-xs border border-slate-200/90 shadow-xs"
          }`}
        >
          {isUser && isEditing ? (
            <div className="w-full min-w-[280px] sm:min-w-[420px] space-y-2">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full bg-slate-800 text-white rounded-lg p-2 text-sm border border-slate-700 focus:outline-hidden focus:ring-1 focus:ring-slate-400 resize-y min-h-[70px]"
                autoFocus
              />
              <div className="flex justify-end gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => { setIsEditing(false); setEditContent(message.content_md); }}
                  className="px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveEdit}
                  className="px-3 py-1 rounded-md bg-white text-slate-900 font-medium hover:bg-slate-100"
                >
                  Save & Resend
                </button>
              </div>
            </div>
          ) : (
            <div className="text-sm break-words leading-relaxed">
              {isUser ? (
                <p className="whitespace-pre-wrap text-slate-100">{message.content_md}</p>
              ) : isError ? (
                <div className="space-y-3">
                  <div className="flex items-start gap-2 text-rose-800 font-medium">
                    <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-rose-600" />
                    <span>{message.content_md}</span>
                  </div>
                  {message.error_detail && (
                    <div className="text-xs bg-white/80 rounded-md border border-rose-200 p-2 text-slate-700">
                      <button
                        type="button"
                        onClick={() => setShowErrorDetail(!showErrorDetail)}
                        className="flex items-center justify-between w-full font-medium text-rose-700 hover:underline"
                      >
                        <span>Diagnostic Details</span>
                        {showErrorDetail ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                      </button>
                      {showErrorDetail && <p className="mt-1.5 font-mono text-[11px] text-slate-600 break-all">{message.error_detail}</p>}
                    </div>
                  )}
                  {onRetry && (
                    <button
                      type="button"
                      onClick={() => onRetry(retryTargetQuery)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-600 text-white hover:bg-rose-700 text-xs font-medium shadow-xs transition-colors"
                    >
                      <RotateCw className="h-3.5 w-3.5" />
                      <span>Retry Question</span>
                    </button>
                  )}
                </div>
              ) : (
                <MarkdownRenderer content={message.content_md} />
              )}
            </div>
          )}

          {!isUser && !isError && message.citations && message.citations.length > 0 && (
            <div className="mt-3 pt-2.5 border-t border-slate-100 flex flex-wrap items-center gap-1.5">
              <span className="text-xs font-semibold text-slate-600 mr-1">Sources:</span>
              {message.citations.map((c) => (
                <CitationChip key={c.chunk_id} citation={c} onClick={(cit) => onCitationClick?.(cit)} />
              ))}
            </div>
          )}

          {!isUser && message.verdict && (
            <div className="mt-3 pt-2.5 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
              <div className="flex items-center gap-2">
                <VerdictPill verdict={message.verdict} />
                {message.confidence !== undefined && <ConfidenceDial score={message.confidence} />}
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

        {/* Hover Action Bar */}
        {!isEditing && (
          <div className="flex items-center gap-1 mt-1 opacity-0 group-hover:opacity-100 transition-opacity text-slate-400">
            <button
              type="button"
              onClick={handleCopy}
              title="Copy text"
              className="p-1 rounded-md hover:bg-slate-100 hover:text-slate-700 transition-colors"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
            </button>
            {isUser && onEdit && (
              <button
                type="button"
                onClick={() => setIsEditing(true)}
                title="Edit question"
                className="p-1 rounded-md hover:bg-slate-100 hover:text-slate-700 transition-colors"
              >
                <Pencil className="h-3.5 w-3.5" />
              </button>
            )}
            {!isUser && onRetry && (
              <button
                type="button"
                onClick={() => onRetry(retryTargetQuery)}
                title="Retry response"
                className="p-1 rounded-md hover:bg-slate-100 hover:text-slate-700 transition-colors"
              >
                <RotateCw className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-200 text-slate-700 mt-0.5 font-semibold text-xs">
          <User className="h-3.5 w-3.5" />
        </div>
      )}
    </div>
  );
};

