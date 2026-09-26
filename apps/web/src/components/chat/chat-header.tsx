"use client";

import React from "react";
import { MessageSquare, Database, FileText } from "lucide-react";
import { Conversation, Project } from "@/types";

interface ChatHeaderProps {
  activeConversation: Conversation | null;
  project: Project;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({ activeConversation, project }) => {
  return (
    <div className="flex h-12 items-center justify-between border-b border-slate-200/80 bg-white px-5 shrink-0">
      <div className="flex items-center gap-2.5 min-w-0">
        <MessageSquare className="h-4 w-4 text-slate-400 shrink-0" />
        <h2 className="text-xs font-semibold text-slate-800 truncate">
          {activeConversation?.title || "New Chat Session"}
        </h2>
      </div>

      <div className="flex items-center gap-2 text-[11px] text-slate-500 font-medium">
        <span className="flex items-center gap-1 bg-slate-50 border border-slate-200/80 px-2 py-0.5 rounded-md">
          <FileText className="h-3 w-3 text-slate-400" />
          {project.document_count || 0} Knowledge Docs
        </span>
      </div>
    </div>
  );
};
