"use client";

import React, { useEffect, useState, use } from "react";
import { apiFetch } from "@/lib/api-client";
import { Citation, Project, Conversation } from "@/types";
import { useConversations } from "@/hooks/use-conversations";
import { useChatStream } from "@/hooks/use-chat-stream";
import { ProjectHeader } from "@/components/project/project-header";
import { SessionSidebar } from "@/components/chat/session-sidebar";
import { ChatHeader } from "@/components/chat/chat-header";
import { MessageList } from "@/components/chat/message-list";
import { ChatInput } from "@/components/chat/chat-input";
import { EmptyChatState } from "@/components/chat/empty-chat-state";
import { SessionRenameModal } from "@/components/chat/session-rename-modal";
import { DocumentViewerModal } from "@/components/viewer/document-viewer-modal";
import { Skeleton } from "@/components/ui/skeleton";

export default function ProjectChatPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;

  const [project, setProject] = useState<Project | null>(null);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [renamingConv, setRenamingConv] = useState<Conversation | null>(null);

  const {
    conversations,
    activeConversationId,
    setActiveConversationId,
    isLoading: isConvLoading,
    createConversation,
    updateConversationTitle,
    deleteConversation,
  } = useConversations(projectId);

  const {
    messages,
    isStreaming,
    isLoadingHistory,
    currentStage,
    sendMessage,
  } = useChatStream(activeConversationId);

  useEffect(() => {
    async function loadProject() {
      if (!projectId) return;
      try {
        const projData = await apiFetch<Project>(`/projects/${projectId}`);
        setProject(projData);
      } catch {
        // Handle error gracefully
      }
    }
    loadProject();
  }, [projectId]);

  const handleCreateNewSession = async () => {
    await createConversation("New Chat");
  };

  const handleSelectPrompt = (promptText: string) => {
    sendMessage(promptText, false);
  };

  const activeConv = conversations.find((c) => c.id === activeConversationId) || null;

  if (!project) {
    return (
      <div className="flex h-full flex-col bg-slate-50">
        <div className="h-16 border-b border-slate-200 bg-white p-4">
          <Skeleton className="h-6 w-48" />
        </div>
        <div className="flex-1 p-6">
          <Skeleton className="h-full w-full rounded-2xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-slate-50 overflow-hidden">
      <ProjectHeader project={project} />

      <div className="flex flex-1 min-h-0 overflow-hidden">
        <SessionSidebar
          conversations={conversations}
          activeConversationId={activeConversationId}
          isLoading={isConvLoading}
          onSelect={(id) => setActiveConversationId(id)}
          onCreate={handleCreateNewSession}
          onRename={(conv) => setRenamingConv(conv)}
          onDelete={(id) => deleteConversation(id)}
        />

        <div className="flex-1 flex flex-col min-w-0 bg-white overflow-hidden">
          <ChatHeader
            activeConversation={activeConv}
            project={project}
          />

          <div className="flex-1 overflow-y-auto p-4 sm:p-6 bg-slate-50/50">
            {isLoadingHistory ? (
              <div className="space-y-4 max-w-3xl mx-auto p-4">
                <Skeleton className="h-20 w-3/4 rounded-xl" />
                <Skeleton className="h-24 w-1/2 ml-auto rounded-xl" />
                <Skeleton className="h-28 w-4/5 rounded-xl" />
              </div>
            ) : messages.length === 0 ? (
              <EmptyChatState
                project={project}
                onSelectPrompt={handleSelectPrompt}
              />
            ) : (
              <div className="max-w-4xl mx-auto">
                <MessageList
                  messages={messages}
                  currentStage={currentStage}
                  onCitationClick={(cit) => setSelectedCitation(cit)}
                />
              </div>
            )}
          </div>

          <div className="p-4 bg-white border-t border-slate-200 shrink-0">
            <div className="max-w-4xl mx-auto">
              <ChatInput
                onSendMessage={sendMessage}
                isStreaming={isStreaming}
                currentStage={currentStage}
              />
            </div>
          </div>
        </div>
      </div>

      <SessionRenameModal
        isOpen={!!renamingConv}
        initialTitle={renamingConv?.title || ""}
        onClose={() => setRenamingConv(null)}
        onRename={async (title) => {
          if (renamingConv) {
            await updateConversationTitle(renamingConv.id, title);
          }
        }}
      />

      <DocumentViewerModal
        isOpen={!!selectedCitation}
        onClose={() => setSelectedCitation(null)}
        citation={selectedCitation}
      />
    </div>
  );
}
