"use client";

import React, { useState } from "react";
import { Check, Copy } from "lucide-react";

export interface CodeBlockProps {
  language?: string;
  codeString: string;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  language = "text",
  codeString,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(codeString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback if clipboard API is restricted
    }
  };

  return (
    <div className="relative my-3 rounded-lg border border-slate-700/60 bg-slate-900 text-slate-100 shadow-sm overflow-hidden text-xs font-mono">
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-slate-800/90 border-b border-slate-700/60 select-none">
        <span className="font-semibold text-slate-300 uppercase tracking-wider text-[11px]">
          {language || "code"}
        </span>
        <button
          type="button"
          onClick={handleCopy}
          aria-label={copied ? "Copied to clipboard" : "Copy code"}
          className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-700/50 hover:bg-slate-700 active:bg-slate-600 text-slate-200 hover:text-white transition-colors focus:outline-none focus:ring-1 focus:ring-slate-400"
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5 text-emerald-400" />
              <span className="text-[11px] text-emerald-400 font-medium">Copied</span>
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5 text-slate-300" />
              <span className="text-[11px]">Copy</span>
            </>
          )}
        </button>
      </div>

      <div className="p-3.5 overflow-x-auto leading-relaxed">
        <pre className="font-mono text-slate-100 whitespace-pre">
          <code>{codeString}</code>
        </pre>
      </div>
    </div>
  );
};
