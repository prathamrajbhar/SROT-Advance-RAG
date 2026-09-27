import React from "react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface StepIndicatorProps {
  currentStep: number;
}

const STEPS = [
  { step: 1, label: "Workspace" },
  { step: 2, label: "Architecture" },
  { step: 3, label: "Credentials" },
  { step: 4, label: "Launch" },
];

export const StepIndicator: React.FC<StepIndicatorProps> = ({ currentStep }) => {
  return (
    <div className="w-full py-4 border-b border-slate-200 bg-slate-50/50">
      <div className="max-w-4xl mx-auto px-4 flex items-center justify-between">
        {STEPS.map((item, index) => {
          const isCompleted = currentStep > item.step;
          const isCurrent = currentStep === item.step;

          return (
            <React.Fragment key={item.step}>
              <div className="flex items-center gap-2.5">
                <div
                  className={cn(
                    "w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium transition-all duration-200",
                    isCompleted && "bg-slate-900 text-white",
                    isCurrent && "border-2 border-slate-900 text-slate-900 bg-white font-semibold shadow-xs",
                    !isCompleted && !isCurrent && "border border-slate-300 text-slate-400 bg-white"
                  )}
                >
                  {isCompleted ? <Check className="w-3.5 h-3.5 stroke-[2.5]" /> : item.step}
                </div>
                <span
                  className={cn(
                    "text-xs tracking-tight transition-colors hidden sm:inline-block",
                    isCurrent && "font-semibold text-slate-900",
                    isCompleted && "font-medium text-slate-700",
                    !isCompleted && !isCurrent && "text-slate-400"
                  )}
                >
                  {item.label}
                </span>
              </div>
              {index < STEPS.length - 1 && (
                <div
                  className={cn(
                    "flex-1 h-[1px] mx-3 transition-colors",
                    currentStep > item.step ? "bg-slate-900" : "bg-slate-200"
                  )}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
