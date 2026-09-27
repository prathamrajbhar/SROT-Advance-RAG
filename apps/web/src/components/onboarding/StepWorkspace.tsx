import React, { useState } from "react";
import { ArrowRight, Building2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { OnboardingState } from "./types";

interface StepWorkspaceProps {
  state: OnboardingState;
  onChange: (patch: Partial<OnboardingState>) => void;
  onNext: () => void;
  isLoading: boolean;
}

export const StepWorkspace: React.FC<StepWorkspaceProps> = ({
  state,
  onChange,
  onNext,
  isLoading,
}) => {
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!state.tenantName.trim()) {
      setError("Organization name is required.");
      return;
    }
    if (!state.tenantSlug.trim()) {
      setError("Organization slug identifier is required.");
      return;
    }
    if (!state.workspaceName.trim()) {
      setError("Workspace name is required.");
      return;
    }
    if (!state.adminEmail.trim() || !state.adminEmail.includes("@")) {
      setError("A valid admin work email is required.");
      return;
    }
    setError(null);
    onNext();
  };

  const handleNameChange = (name: string) => {
    const slug = name.toLowerCase().replace(/[^a-z0-9]/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");
    onChange({ tenantName: name, tenantSlug: slug });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Building2 className="w-5 h-5 text-slate-700" />
          <h2 className="text-lg font-semibold text-slate-900 tracking-tight">Organization & Workspace</h2>
        </div>
        <p className="text-xs text-slate-500">
          Create an isolated enterprise multi-tenant tenant environment and initial workspace.
        </p>
      </div>

      {error && (
        <div className="p-3 text-xs bg-rose-50 border border-rose-200 text-rose-800 rounded-md">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">Organization Name</label>
          <Input
            value={state.tenantName}
            onChange={(e) => handleNameChange(e.target.value)}
            placeholder="Acme Corporation"
            required
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">Tenant Slug (Identifier)</label>
          <Input
            value={state.tenantSlug}
            onChange={(e) => onChange({ tenantSlug: e.target.value })}
            placeholder="acme-corp"
            required
          />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">Initial Workspace Name</label>
          <Input
            value={state.workspaceName}
            onChange={(e) => onChange({ workspaceName: e.target.value })}
            placeholder="Legal & Financial Intelligence"
            required
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">Admin Work Email</label>
          <Input
            type="email"
            value={state.adminEmail}
            onChange={(e) => onChange({ adminEmail: e.target.value })}
            placeholder="admin@acme.com"
            required
          />
        </div>
      </div>

      <div className="pt-4 border-t border-slate-200 flex justify-end">
        <Button type="submit" isLoading={isLoading} className="gap-2">
          <span>Continue to Architecture</span>
          <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
    </form>
  );
};
