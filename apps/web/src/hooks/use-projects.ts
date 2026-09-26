"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { Project } from "@/types";

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProjects = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiFetch<{ items: Project[]; total: number }>("/projects");
      setProjects(data.items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load projects");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const createProject = async (name: string, description?: string): Promise<Project> => {
    const created = await apiFetch<Project>("/projects", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    });
    await fetchProjects();
    return created;
  };

  const updateProject = async (id: string, name: string, description?: string): Promise<Project> => {
    const updated = await apiFetch<Project>(`/projects/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ name, description }),
    });
    await fetchProjects();
    return updated;
  };

  const deleteProject = async (id: string): Promise<void> => {
    await apiFetch(`/projects/${id}`, { method: "DELETE" });
    await fetchProjects();
  };

  return { projects, isLoading, error, fetchProjects, createProject, updateProject, deleteProject };
}
