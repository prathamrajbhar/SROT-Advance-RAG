"use client";

import React, { useEffect, useState, use, useCallback } from "react";
import { apiFetch } from "@/lib/api-client";
import { Project, ProjectMetrics } from "@/types";
import { ProjectHeader } from "@/components/project/project-header";
import { EvalDashboard } from "@/components/eval/eval-dashboard";

export default function ProjectEvalPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;

  const [project, setProject] = useState<Project | null>(null);
  const [metrics, setMetrics] = useState<ProjectMetrics | null>(null);
  const [evalRuns, setEvalRuns] = useState<any[]>([]);

  const loadData = useCallback(async () => {
    if (!projectId) return;
    try {
      const projData = await apiFetch<Project>(`/projects/${projectId}`);
      setProject(projData);

      const metricsData = await apiFetch<ProjectMetrics>(`/projects/${projectId}/metrics`);
      setMetrics(metricsData);

      const runsData = await apiFetch<{ items: any[] }>(`/projects/${projectId}/eval/runs`);
      setEvalRuns(runsData.items);
    } catch {
      // Handle error
    }
  }, [projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleTriggerEval = async () => {
    await apiFetch(`/projects/${projectId}/eval/run`, {
      method: "POST",
      body: JSON.stringify({ notes: "Manual benchmark triggered via dashboard" }),
    });
    await loadData();
  };

  if (!project) {
    return <div className="p-8 text-sm text-slate-500">Loading project...</div>;
  }

  return (
    <div className="flex flex-col h-full bg-slate-50 overflow-y-auto">
      <ProjectHeader project={project} />

      <div className="p-6 max-w-5xl">
        <EvalDashboard
          metrics={metrics}
          evalRuns={evalRuns}
          onTriggerEval={handleTriggerEval}
        />
      </div>
    </div>
  );
}
