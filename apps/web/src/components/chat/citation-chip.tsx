import React from "react";
import { Citation } from "@/types";

export interface CitationChipProps {
  citation: Citation;
  onClick: (citation: Citation) => void;
}

export const CitationChip: React.FC<CitationChipProps> = ({ citation, onClick }) => {
  const getLocatorText = () => {
    if (!citation.locator) return "";
    if (citation.locator.page_number) return `p. ${citation.locator.page_number}`;
    if (citation.locator.start_s !== undefined) {
      const min = Math.floor(citation.locator.start_s / 60);
      const sec = Math.floor(citation.locator.start_s % 60);
      return `${min}:${sec < 10 ? "0" : ""}${sec}`;
    }
    if (citation.locator.row_range) {
      return `Rows ${citation.locator.row_range[0]}-${citation.locator.row_range[1]}`;
    }
    return "";
  };

  const locatorText = getLocatorText();

  return (
    <button
      onClick={() => onClick(citation)}
      className="inline-flex items-center gap-1 px-2 py-0.5 mx-0.5 text-xs font-medium rounded bg-slate-100 text-slate-800 border border-slate-300 hover:bg-slate-200 focus:outline-none focus:ring-1 focus:ring-slate-500 transition-colors"
      title={`${citation.document_name} ${locatorText ? `(${locatorText})` : ""}`}
    >
      <span>[{citation.index}]</span>
      <span className="truncate max-w-[120px]">{citation.document_name}</span>
      {locatorText && <span className="text-slate-500">· {locatorText}</span>}
    </button>
  );
};
