"use client";

import React from "react";
import { Sparkles, FileSearch, HelpCircle, ShieldCheck, ArrowRight } from "lucide-react";
import { Project } from "@/types";

interface EmptyChatStateProps {
  project: Project;
  onSelectPrompt: (prompt: string) => void;
}

export const EmptyChatState: React.FC<EmptyChatStateProps> = ({ project, onSelectPrompt }) => {
  const samplePrompts = [
    {
      icon: FileSearch,
      title: "Summarize Knowledge Base",
      prompt: "Give me an executive summary of all uploaded documents in this workspace.",
    },
    {
      icon: HelpCircle,
      title: "Key Terms & Requirements",
      prompt: "What are the core obligations, important dates, and requirements outlined in the documents?",
    },
    {
      icon: ShieldCheck,
      title: "Compliance & Fact Verification",
      prompt: "Verify any compliance policies, candidate details, or financial stats with exact citations.",
    },
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full max-w-xl mx-auto text-center px-4 py-12">
      <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-white shadow-sm mb-4">
        <Sparkles className="h-5 w-5 text-slate-100" />
      </div>

      <h3 className="text-lg font-bold text-slate-900 mb-1.5 tracking-tight">
        How can I help with {project.name}?
      </h3>
      <p className="text-xs text-slate-500 max-w-md mb-8 leading-relaxed">
        Ask any question. Answers are extracted strictly from your indexed documents with verified citations and confidence scores.
      </p>

      <div className="w-full space-y-2.5 text-left">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block px-1">
          Suggested queries
        </span>
        <div className="grid grid-cols-1 gap-2">
          {samplePrompts.map((item, idx) => {
            const Icon = item.icon;
            return (
              <button
                key={idx}
                onClick={() => onSelectPrompt(item.prompt)}
                className="group flex items-center justify-between p-3 rounded-xl border border-slate-200/90 bg-white hover:border-slate-300 hover:shadow-xs transition-all text-left"
              >
                <div className="flex items-center gap-3 min-w-0 pr-2">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600 group-hover:bg-slate-900 group-hover:text-white transition-colors">
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-slate-900 group-hover:text-blue-600 transition-colors truncate">
                      {item.title}
                    </p>
                    <p className="text-[11px] text-slate-400 truncate mt-0.5">
                      {item.prompt}
                    </p>
                  </div>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-slate-300 group-hover:text-slate-700 transition-colors shrink-0" />
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
