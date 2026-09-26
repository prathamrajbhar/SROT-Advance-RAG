"use client";

import React, { useState, useMemo } from "react";
import { Plus, Search, MessageSquareDashed } from "lucide-react";
import { Conversation } from "@/types";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { SessionItem } from "./session-item";

interface SessionSidebarProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  isLoading: boolean;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onRename: (conversation: Conversation) => void;
  onDelete: (id: string) => void;
}

export const SessionSidebar: React.FC<SessionSidebarProps> = ({
  conversations,
  activeConversationId,
  isLoading,
  onSelect,
  onCreate,
  onRename,
  onDelete,
}) => {
  const [search, setSearch] = useState("");

  const filteredConversations = useMemo(() => {
    if (!search.trim()) return conversations;
    return conversations.filter((c) =>
      (c.title || "Untitled Chat").toLowerCase().includes(search.toLowerCase())
    );
  }, [conversations, search]);

  return (
    <aside className="w-60 border-r border-slate-200/90 bg-slate-50/70 flex flex-col shrink-0 h-full">
      <div className="p-3 border-b border-slate-200/70 space-y-2">
        <button
          onClick={onCreate}
          className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg bg-white border border-slate-200 text-slate-800 text-xs font-semibold shadow-xs hover:bg-slate-100 hover:border-slate-300 transition-colors"
        >
          <Plus className="h-3.5 w-3.5 text-slate-600" />
          <span>New Chat</span>
        </button>

        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search conversations..."
            className="pl-8 h-8 text-xs bg-white border-slate-200 focus:bg-white"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {isLoading ? (
          <div className="space-y-1.5 p-1">
            <Skeleton className="h-8 w-full rounded-lg" />
            <Skeleton className="h-8 w-full rounded-lg" />
            <Skeleton className="h-8 w-full rounded-lg" />
          </div>
        ) : filteredConversations.length === 0 ? (
          <div className="p-6 text-center text-slate-400">
            <MessageSquareDashed className="h-6 w-6 mx-auto mb-1.5 opacity-40 text-slate-500" />
            <p className="text-xs font-medium text-slate-600">
              {search ? "No chats found" : "No chats yet"}
            </p>
            <p className="text-[10px] text-slate-400 mt-0.5">
              {search ? "Try another search" : "Start a new conversation"}
            </p>
          </div>
        ) : (
          filteredConversations.map((conv) => (
            <SessionItem
              key={conv.id}
              conversation={conv}
              isActive={conv.id === activeConversationId}
              onSelect={onSelect}
              onRename={onRename}
              onDelete={onDelete}
            />
          ))
        )}
      </div>
    </aside>
  );
};
