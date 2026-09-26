import React from "react";
import { formatConfidenceLabel } from "@/lib/utils";

export interface ConfidenceDialProps {
  score: number;
}

export const ConfidenceDial: React.FC<ConfidenceDialProps> = ({ score }) => {
  const { label, color } = formatConfidenceLabel(score);
  const percentage = Math.round(score * 100);

  const colorStyles = {
    success: "bg-emerald-500 text-emerald-700 bg-emerald-50",
    warning: "bg-amber-500 text-amber-700 bg-amber-50",
    danger: "bg-rose-500 text-rose-700 bg-rose-50",
  };

  const barColors = {
    success: "bg-emerald-500",
    warning: "bg-amber-500",
    danger: "bg-rose-500",
  };

  return (
    <div className="flex items-center gap-2">
      <div className="w-16 bg-slate-200 h-2 rounded-full overflow-hidden">
        <div
          className={`h-full ${barColors[color]} transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-xs font-semibold text-slate-700">
        {percentage}%
      </span>
      <span className="text-xs text-slate-500">({label})</span>
    </div>
  );
};
