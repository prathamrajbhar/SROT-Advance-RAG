"use client";

import React, { useState, useMemo, useEffect } from "react";
import { useRouter } from "next/navigation";
import { FolderPlus, Layers, Search, Filter, AlertTriangle, RefreshCw } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { useProjects } from "@/hooks/use-projects";
import { Project } from "@/types";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { WorkspacesHeader } from "@/components/workspaces/workspaces-header";
import { WorkspacesStatsBar } from "@/components/workspaces/workspaces-stats-bar";
import { WorkspaceCard } from "@/components/workspaces/workspace-card";
import { WorkspaceModal } from "@/components/workspaces/workspace-modal";
import { WorkspaceDeleteDialog } from "@/components/workspaces/workspace-delete-dialog";

export default function HomePage() {
  const { user, isLoading: isAuthLoading, logout } = useAuth();
  const {
    projects,
    isLoading: isProjectsLoading,
    error: projectsError,
    fetchProjects,
    createProject,
    updateProject,
    deleteProject,
  } = useProjects();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthLoading && !user) {
      router.push("/login");
    }
  }, [user, isAuthLoading, router]);

  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const [modalOpen, setModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [deletingProject, setDeletingProject] = useState<Project | null>(null);

  const filteredProjects = useMemo(() => {
    return projects.filter((p) => {
      const matchesSearch =
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesRole = roleFilter === "all" || p.role === roleFilter;
      return matchesSearch && matchesRole;
    });
  }, [projects, searchQuery, roleFilter]);

  const handleOpenCreate = () => {
    setEditingProject(null);
    setModalOpen(true);
  };

  const handleOpenEdit = (project: Project) => {
    setEditingProject(project);
    setModalOpen(true);
  };

  const handleModalSubmit = async (name: string, description?: string) => {
    if (editingProject) {
      await updateProject(editingProject.id, name, description);
    } else {
      const created = await createProject(name, description);
      router.push(`/projects/${created.id}`);
    }
  };

  if (isAuthLoading || (isProjectsLoading && projects.length === 0)) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <header className="h-16 border-b border-slate-200 bg-white px-6 flex items-center justify-between">
          <Skeleton className="h-8 w-36" />
          <Skeleton className="h-8 w-24" />
        </header>
        <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
          <Skeleton className="h-20 w-full rounded-xl" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Skeleton className="h-48 rounded-xl" />
            <Skeleton className="h-48 rounded-xl" />
            <Skeleton className="h-48 rounded-xl" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <WorkspacesHeader
        user={user}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onNewWorkspace={handleOpenCreate}
        onLogout={logout}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8">
        {projectsError && (
          <div className="mb-6 flex items-center justify-between gap-3 rounded-xl border border-rose-200 bg-rose-50/80 p-4 text-rose-900 shadow-sm">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-rose-600 shrink-0" />
              <div>
                <p className="text-xs font-semibold">Failed to load workspaces</p>
                <p className="text-xs text-rose-700">{projectsError}</p>
              </div>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={() => fetchProjects()}
              className="text-xs gap-1.5 border-rose-200 bg-white hover:bg-rose-50 text-rose-800"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Retry
            </Button>
          </div>
        )}

        <WorkspacesStatsBar projects={projects} />

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
          <div>
            <h1 className="text-xl font-bold text-slate-900">Knowledge Workspaces</h1>
            <p className="text-xs text-slate-500 mt-0.5">Select a workspace to enter chat sessions and query documents</p>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs">
            {["all", "owner", "editor", "viewer"].map((filter) => (
              <button
                key={filter}
                onClick={() => setRoleFilter(filter)}
                className={`px-3 py-1 rounded-md capitalize font-medium transition-colors ${
                  roleFilter === filter
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {filter}
              </button>
            ))}
          </div>
        </div>

        {filteredProjects.length === 0 ? (
          <div className="rounded-2xl border-2 border-dashed border-slate-200 bg-white p-12 text-center max-w-md mx-auto my-8">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 text-slate-600 mb-4">
              <FolderPlus className="h-6 w-6" />
            </div>
            <h3 className="text-base font-semibold text-slate-900">
              {searchQuery ? "No matching workspaces" : "No workspaces yet"}
            </h3>
            <p className="text-xs text-slate-500 mt-1 mb-6">
              {searchQuery
                ? "Try searching with different keywords or clear your filters."
                : "Create your first workspace to start uploading files and asking questions."}
            </p>
            <Button
              onClick={handleOpenCreate}
              className="bg-slate-900 hover:bg-slate-800 text-white text-xs gap-1.5"
            >
              <FolderPlus className="h-3.5 w-3.5" />
              Create Workspace
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProjects.map((project) => (
              <WorkspaceCard
                key={project.id}
                project={project}
                onEdit={handleOpenEdit}
                onDelete={(p) => setDeletingProject(p)}
              />
            ))}
          </div>
        )}
      </main>

      <WorkspaceModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmit={handleModalSubmit}
        initialData={editingProject}
      />

      <WorkspaceDeleteDialog
        isOpen={!!deletingProject}
        project={deletingProject}
        onClose={() => setDeletingProject(null)}
        onConfirm={async (id) => {
          await deleteProject(id);
        }}
      />
    </div>
  );
}
