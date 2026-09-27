import React from "react";
import { Cpu } from "lucide-react";
import { cn } from "@/lib/utils";
import { LocalEngine } from "./types";

export const LOCAL_ENGINES: Array<{ id: LocalEngine; name: string; defaultUrl: string; hint: string }> = [
  { id: "ollama", name: "Ollama", defaultUrl: "http://localhost:11434", hint: "Port 11434" },
  { id: "vllm", name: "vLLM", defaultUrl: "http://localhost:8000/v1", hint: "OpenAI-compatible" },
  { id: "localai", name: "LocalAI", defaultUrl: "http://localhost:8080/v1", hint: "Gateway proxy" },
];

interface LocalEngineSelectorProps {
  activeEngine: LocalEngine;
  onSelect: (engineId: LocalEngine) => void;
}

export const LocalEngineSelector: React.FC<LocalEngineSelectorProps> = ({ activeEngine, onSelect }) => {
  return (
    <div>
      <label className="block text-xs font-medium text-slate-700 mb-1.5">Select Local Inference Engine</label>
      <div className="grid grid-cols-3 gap-2">
        {LOCAL_ENGINES.map((engine) => {
          const isSelected = activeEngine === engine.id;
          return (
            <button
              key={engine.id}
              type="button"
              onClick={() => onSelect(engine.id)}
              className={cn(
                "p-2.5 rounded-lg border text-left text-xs font-medium transition-all duration-150 select-none",
                isSelected
                  ? "border-slate-900 bg-white ring-1 ring-slate-900 shadow-xs text-slate-900"
                  : "border-slate-200 bg-white hover:border-slate-300 text-slate-600 hover:bg-slate-50/50"
              )}
            >
              <div className="flex items-center gap-1.5 mb-0.5">
                <Cpu className="w-3.5 h-3.5" />
                <span className="font-semibold">{engine.name}</span>
              </div>
              <div className="text-[10px] text-slate-400 truncate">{engine.hint}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
