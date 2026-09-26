"use client";

import React, { useState } from "react";
import { MessageSquare, MoreHorizontal, Edit2, Trash2 } from "lucide-react";
import { Conversation } from "@/types";

interface SessionItemProps {
  conversation: Conversation;
  isActive: boolean;
  onSelect: (id: string) => void;
  onRename: (conversation: Conversation) => void;
  onDelete: (id: string) => void;
}

export const SessionItem: React.FC<SessionItemProps> = ({
  conversation,
  isActive,
  onSelect,
  onRename,
  onDelete,
}) => {
  const [showOptions, setShowOptions] = useState(false);

  return (
    <div
      onClick={() => onSelect(conversation.id)}
      className={`group relative flex items-center justify-between gap-2 px-3 py-2 rounded-lg cursor-pointer text-xs transition-colors duration-150 ${
        isActive
          ? "bg-slate-200/70 text-slate-900 font-semibold"
          : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 font-normal"
      }`}
    >
      <div className="flex items-center gap-2 min-w-0 flex-1">
        <MessageSquare
          className={`h-3.5 w-3.5 shrink-0 ${
            isActive ? "text-slate-900" : "text-slate-400 group-hover:text-slate-600"
          }`}
        />
        <span className="truncate leading-tight">{conversation.title || "Untitled Chat"}</span>
      </div>

      <div className="relative shrink-0" onClick={(e) => e.stopPropagation()}>
        <button
          onClick={() => setShowOptions((prev) => !prev)}
          className={`p-1 rounded-md transition-opacity ${
            isActive
              ? "text-slate-600 hover:text-slate-900 hover:bg-slate-300/60"
              : "text-slate-400 hover:text-slate-700 opacity-0 group-hover:opacity-100 hover:bg-slate-200/70"
          }`}
          aria-label="Session options"
        >
          <MoreHorizontal className="h-3.5 w-3.5" />
        </button>

        {showOptions && (
          <>
            <div className="fixed inset-0 z-30" onClick={() => setShowOptions(false)} />
            <div className="absolute right-0 top-6 z-40 w-36 rounded-lg bg-white p-1 shadow-md border border-slate-200 text-xs font-medium text-slate-700">
              <button
                onClick={() => {
                  setShowOptions(false);
                  onRename(conversation);
                }}
                className="flex w-full items-center gap-2 px-2.5 py-1.5 rounded-md hover:bg-slate-50 text-slate-700 hover:text-slate-900 transition-colors"
              >
                <Edit2 className="h-3 w-3 text-slate-500" />
                Rename
              </button>
              <button
                onClick={() => {
                  setShowOptions(false);
                  onDelete(conversation.id);
                }}
                className="flex w-full items-center gap-2 px-2.5 py-1.5 rounded-md hover:bg-red-50 text-red-600 hover:text-red-700 transition-colors"
              >
                <Trash2 className="h-3 w-3 text-red-500" />
                Delete
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
