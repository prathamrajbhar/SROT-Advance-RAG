"use client";

import React, { useEffect, useState, use, useCallback } from "react";
import { apiFetch } from "@/lib/api-client";
import { Project, ProjectMember, Role } from "@/types";
import { ProjectHeader } from "@/components/project/project-header";
import { MembersTable } from "@/components/project/members-table";

export default function ProjectMembersPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;

  const [project, setProject] = useState<Project | null>(null);
  const [members, setMembers] = useState<ProjectMember[]>([]);

  const loadData = useCallback(async () => {
    if (!projectId) return;
    try {
      const projData = await apiFetch<Project>(`/projects/${projectId}`);
      setProject(projData);

      const membersData = await apiFetch<ProjectMember[]>(`/projects/${projectId}/members`);
      setMembers(membersData);
    } catch {
      // Handle error
    }
  }, [projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleAddMember = async (email: string, role: Role) => {
    await apiFetch(`/projects/${projectId}/members`, {
      method: "POST",
      body: JSON.stringify({ email, role }),
    });
    await loadData();
  };

  const handleRemoveMember = async (userId: string) => {
    await apiFetch(`/projects/${projectId}/members/${userId}`, {
      method: "DELETE",
    });
    await loadData();
  };

  if (!project) {
    return <div className="p-8 text-sm text-slate-500">Loading project...</div>;
  }

  return (
    <div className="flex flex-col h-full bg-slate-50 overflow-y-auto">
      <ProjectHeader project={project} />

      <div className="p-6 max-w-4xl">
        <MembersTable
          members={members}
          onAddMember={handleAddMember}
          onRemoveMember={handleRemoveMember}
        />
      </div>
    </div>
  );
}
