"use client";

import React, { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { CodeBlock } from "./code-block";

export interface MarkdownRendererProps {
  content: string;
  className?: string;
}

function unpackRawMarkdownContent(raw: string): string {
  if (!raw) return "";
  let text = raw.trim();

  // Strip JSON code blocks
  if (text.startsWith("```json") || text.startsWith("```")) {
    text = text.replace(/^```(?:json)?\s*\n?/i, "").replace(/\n?```\s*$/i, "").trim();
  }

  // Parse JSON if starts with {"answer_md"
  if (text.startsWith("{") && (text.includes('"answer_md"') || text.includes('"claims"'))) {
    try {
      const parsed = JSON.parse(text);
      if (parsed && typeof parsed.answer_md === "string") {
        text = parsed.answer_md;
      }
    } catch {
      const match = text.match(/"answer_md"\s*:\s*"([\s\S]*?)(?="\s*,\s*"claims"|"\s*\}\s*$|\Z)/);
      if (match) {
        text = match[1];
      }
    }
  }

  // If text contains claims residue, strip it
  if (text.includes('"claims"')) {
    text = text.replace(/,\s*"claims"\s*:\s*\[[\s\S]*?\]\s*\}?/g, "");
    text = text.replace(/\{\s*"answer_md"\s*:\s*"?/g, "");
    text = text.replace(/"\s*\}\s*$/g, "");
  }

  // Unescape literal \n, \r, \t, and escaped quotes
  text = text.replace(/\\r\\n/g, "\n").replace(/\\n/g, "\n").replace(/\\t/g, "\t").replace(/\\"/g, '"');

  return text.trim();
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  className = "",
}) => {
  const sanitizedContent = useMemo(
    () => unpackRawMarkdownContent(content),
    [content]
  );

  return (
    <div className={`prose-sm max-w-none text-slate-900 font-normal leading-relaxed ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="text-base font-bold text-slate-900 mt-4 mb-2 pb-1 border-b border-slate-200">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-sm font-bold text-slate-900 mt-3 mb-1.5">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 mt-2.5 mb-1">
              {children}
            </h3>
          ),
          p: ({ children }) => (
            <p className="mb-2.5 last:mb-0 leading-relaxed text-slate-900">
              {children}
            </p>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-slate-950">
              {children}
            </strong>
          ),
          em: ({ children }) => (
            <em className="italic text-slate-900">{children}</em>
          ),
          ul: ({ children }) => (
            <ul className="list-disc pl-5 mb-2.5 space-y-1 text-slate-900">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal pl-5 mb-2.5 space-y-1 text-slate-900">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="leading-relaxed pl-0.5">{children}</li>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-slate-400 bg-slate-50 rounded-r-md px-3.5 py-2 my-2.5 text-slate-800 italic">
              {children}
            </blockquote>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-3.5 rounded-lg border border-slate-200 shadow-sm">
              <table className="min-w-full divide-y divide-slate-200 text-xs">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-slate-50 font-semibold text-slate-800">
              {children}
            </thead>
          ),
          th: ({ children }) => (
            <th className="px-3.5 py-2.5 text-left font-semibold text-slate-900">
              {children}
            </th>
          ),
          tr: ({ children }) => (
            <tr className="hover:bg-slate-50/50 transition-colors">
              {children}
            </tr>
          ),
          td: ({ children }) => (
            <td className="px-3.5 py-2 border-t border-slate-100 text-slate-800">
              {children}
            </td>
          ),
          code: ({ className: codeClassName, children }) => {
            const match = /language-(\w+)/.exec(codeClassName || "");
            const isMultiLine = String(children).includes("\n");

            if (!match && !isMultiLine) {
              return (
                <code className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-900 text-xs font-mono font-medium border border-slate-200">
                  {children}
                </code>
              );
            }

            const language = match ? match[1] : "text";
            const codeString = String(children).replace(/\n$/, "");

            return <CodeBlock language={language} codeString={codeString} />;
          },
        }}
      >
        {sanitizedContent}
      </ReactMarkdown>
    </div>
  );
};
