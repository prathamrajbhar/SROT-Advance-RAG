import React from "react";
import { cn } from "@/lib/utils";

export interface CloudProviderItem {
  id: string;
  name: string;
  docsUrl: string;
}

export const CLOUD_PROVIDERS: CloudProviderItem[] = [
  { id: "gemini", name: "Google Gemini", docsUrl: "https://aistudio.google.com/app/apikey" },
  { id: "openai", name: "OpenAI", docsUrl: "https://platform.openai.com/api-keys" },
  { id: "anthropic", name: "Anthropic", docsUrl: "https://console.anthropic.com/settings/keys" },
  { id: "groq", name: "Groq LPU", docsUrl: "https://console.groq.com/keys" },
];

interface CloudProviderSelectorProps {
  selectedId: string;
  onSelect: (id: string) => void;
}

export const CloudProviderSelector: React.FC<CloudProviderSelectorProps> = ({ selectedId, onSelect }) => {
  return (
    <div>
      <label className="block text-xs font-medium text-slate-700 mb-1.5">Select Cloud Provider</label>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {CLOUD_PROVIDERS.map((provider) => {
          const isSelected = selectedId === provider.id;
          return (
            <button
              key={provider.id}
              type="button"
              onClick={() => onSelect(provider.id)}
              className={cn(
                "p-2.5 rounded-lg border text-left text-xs font-medium transition-all duration-150 select-none",
                isSelected
                  ? "border-slate-900 bg-white ring-1 ring-slate-900 shadow-xs text-slate-900"
                  : "border-slate-200 bg-white hover:border-slate-300 text-slate-600 hover:bg-slate-50/50"
              )}
            >
              <div className="font-semibold">{provider.name}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
