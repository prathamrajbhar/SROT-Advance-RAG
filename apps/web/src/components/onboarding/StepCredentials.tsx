import React from "react";
import { ArrowLeft, ArrowRight, KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StepCredentialsCloud } from "./StepCredentialsCloud";
import { StepCredentialsHybrid } from "./StepCredentialsHybrid";
import { StepCredentialsLocal } from "./StepCredentialsLocal";
import { RerankerSelector } from "./RerankerSelector";
import { TriEngineDiagnostics } from "./TriEngineDiagnostics";
import { ConnectionDiagnostic, OnboardingState } from "./types";

interface StepCredentialsProps {
  state: OnboardingState;
  onChange: (patch: Partial<OnboardingState>) => void;
  diagnostic: ConnectionDiagnostic;
  onTestConnection: () => Promise<void>;
  onNext: () => void;
  onBack: () => void;
}

export const StepCredentials: React.FC<StepCredentialsProps> = ({
  state,
  onChange,
  diagnostic,
  onTestConnection,
  onNext,
  onBack,
}) => {
  return (
    <div className="space-y-5">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <KeyRound className="w-5 h-5 text-slate-700" />
          <h2 className="text-lg font-semibold text-slate-900 tracking-tight">BYOK Credentials & Verification</h2>
        </div>
        <p className="text-xs text-slate-500">
          {state.providerMode === "cloud" && "Configure cloud model credentials, verified vector embeddings, and reranking."}
          {state.providerMode === "local" && "Target your self-hosted inference cluster with dedicated local embeddings."}
          {state.providerMode === "hybrid" && "Configure dual-layer topology: local vector storage with cloud reasoning."}
        </p>
      </div>

      {state.providerMode === "cloud" && (
        <StepCredentialsCloud state={state} onChange={onChange} />
      )}
      {state.providerMode === "local" && (
        <StepCredentialsLocal state={state} onChange={onChange} />
      )}
      {state.providerMode === "hybrid" && (
        <StepCredentialsHybrid state={state} onChange={onChange} />
      )}

      {/* Stage 2 Cross-Encoder Reranker Engine */}
      <RerankerSelector
        selectedModel={state.defaultRerankerModel}
        cohereApiKey={state.rerankerApiKey}
        onChange={onChange}
      />

      {/* Tri-Engine Pipeline Diagnostic Probe */}
      <TriEngineDiagnostics
        diagnostic={diagnostic}
        onTestPipeline={onTestConnection}
      />

      <div className="pt-3 border-t border-slate-200 flex justify-between items-center">
        <Button variant="outline" onClick={onBack} className="gap-2">
          <ArrowLeft className="w-4 h-4" />
          <span>Back</span>
        </Button>
        <Button onClick={onNext} className="gap-2">
          <span>Review & Launch</span>
          <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};
