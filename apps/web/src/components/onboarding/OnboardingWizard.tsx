"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "@/components/ui/toast";
import { StepIndicator } from "./StepIndicator";
import { StepWorkspace } from "./StepWorkspace";
import { StepProviderMode } from "./StepProviderMode";
import { StepCredentials } from "./StepCredentials";
import { StepLaunch } from "./StepLaunch";
import {
  createWorkspaceApi,
  saveProviderSettingsApi,
  seedSampleDataApi,
  testPipelineApi,
} from "./onboarding-api";
import { ConnectionDiagnostic, OnboardingState } from "./types";

const INITIAL_STATE: OnboardingState = {
  tenantName: "",
  tenantSlug: "",
  workspaceName: "Default Workspace",
  adminEmail: "",
  providerMode: "cloud",
  providerName: "gemini",
  apiKey: "",
  baseUrl: "http://localhost:11434",
  defaultLlmModel: "gemini-2.0-flash",
  defaultEmbeddingModel: "text-embedding-004",
  defaultRerankerModel: "ms-marco-MiniLM-L-12-v2",
};

export const OnboardingWizard: React.FC = () => {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [state, setState] = useState<OnboardingState>(INITIAL_STATE);
  const [isLoading, setIsLoading] = useState(false);
  const [isSeeding, setIsSeeding] = useState(false);
  const [isSeeded, setIsSeeded] = useState(false);
  const [diagnostic, setDiagnostic] = useState<ConnectionDiagnostic>({ status: "idle" });

  const updateState = (patch: Partial<OnboardingState>) => setState((prev) => ({ ...prev, ...patch }));

  const handleWorkspaceSubmit = async () => {
    setIsLoading(true);
    try {
      const res = await createWorkspaceApi(state);
      updateState({ tenantId: res.tenant_id, workspaceId: res.workspace_id });
      setCurrentStep(2);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestConnection = async () => {
    setDiagnostic({ status: "testing" });
    try {
      const res = await testPipelineApi(state);
      if (res.healthy) {
        setDiagnostic({ status: "healthy", latencyMs: res.overall_latency_ms, resolvedModel: res.llm_probe.model, pipeline: res });
        toast.success("All 3 pipeline engines verified", "Tri-Engine Check Passed");
      } else {
        const failedMsgs = [
          !res.llm_probe.healthy && `LLM: ${res.llm_probe.message || "failed"}`,
          !res.embedding_probe.healthy && `Embedding: ${res.embedding_probe.message || "failed"}`,
          !res.reranker_probe.healthy && `Reranker: ${res.reranker_probe.message || "failed"}`,
        ].filter(Boolean).join(" • ");
        setDiagnostic({ status: "error", errorMessage: failedMsgs || "Pipeline verification failed", pipeline: res });
      }
    } catch (err: unknown) {
      setDiagnostic({ status: "error", errorMessage: err instanceof Error ? err.message : "Diagnostics failed" });
    }
  };

  const handleCredentialsSubmit = async () => {
    if (!state.workspaceId) { setCurrentStep(1); return; }
    setIsLoading(true);
    try {
      await saveProviderSettingsApi(state);
      setCurrentStep(4);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSeedSampleData = async () => {
    if (!state.workspaceId) return;
    setIsSeeding(true);
    try {
      await seedSampleDataApi(state.workspaceId);
      setIsSeeded(true);
      toast.success("4 multi-modal files queued for indexing", "Sample Data Seeded");
    } finally {
      setIsSeeding(false);
    }
  };

  const handleFinish = () => {
    toast.success("Workspace setup complete! AI engines ready.", "Launch Complete");
    if (state.workspaceId) {
      router.push(`/workspace/${state.workspaceId}/documents`);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col justify-between">
      <div>
        <header className="border-b border-slate-200 px-6 py-3.5 flex items-center justify-between bg-white shadow-xs">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded bg-slate-900 text-white flex items-center justify-center font-bold text-xs">S</div>
            <span className="font-bold text-sm tracking-tight text-slate-900">SROT Enterprise</span>
            <span className="text-[10px] font-mono uppercase bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded border border-slate-200 font-medium">Setup Wizard</span>
          </div>
          <div className="text-xs text-slate-500 font-mono">{state.adminEmail ? `Logged in: ${state.adminEmail}` : "v2.0 • Enterprise Multimodal RAG"}</div>
        </header>

        <StepIndicator currentStep={currentStep} />

        <main className="max-w-3xl mx-auto px-4 py-8">
          <div className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8 shadow-xs">
            {currentStep === 1 && <StepWorkspace state={state} onChange={updateState} onNext={handleWorkspaceSubmit} isLoading={isLoading} />}
            {currentStep === 2 && <StepProviderMode state={state} onChange={updateState} onNext={() => setCurrentStep(3)} onBack={() => setCurrentStep(1)} />}
            {currentStep === 3 && <StepCredentials state={state} onChange={updateState} diagnostic={diagnostic} onTestConnection={handleTestConnection} onNext={handleCredentialsSubmit} onBack={() => setCurrentStep(2)} />}
            {currentStep === 4 && <StepLaunch state={state} onSeedSampleData={handleSeedSampleData} isSeeding={isSeeding} isSeeded={isSeeded} onFinish={handleFinish} onBack={() => setCurrentStep(3)} />}
          </div>
        </main>
      </div>

      <footer className="border-t border-slate-200 px-6 py-4 text-center text-xs text-slate-400">
        SROT Enterprise Multimodal RAG Platform • AES-256-GCM Vault • Tri-Layer Tenant Isolation
      </footer>
    </div>
  );
};
