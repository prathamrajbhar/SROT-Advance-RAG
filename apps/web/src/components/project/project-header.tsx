"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  MessageSquare,
  Files,
  Users,
  BarChart3,
  ShieldCheck,
  ChevronRight,
  LayoutGrid,
  LogOut,
  Layers,
} from "lucide-react";
import { Project } from "@/types";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/use-auth";

export interface ProjectHeaderProps {
  project: Project;
}

export const ProjectHeader: React.FC<ProjectHeaderProps> = ({ project }) => {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [profileOpen, setProfileOpen] = useState(false);

  const tabs = [
    { name: "Chat", href: `/projects/${project.id}`, icon: MessageSquare },
    { name: "Documents", href: `/projects/${project.id}/documents`, icon: Files, badge: project.document_count },
    { name: "Evaluation", href: `/projects/${project.id}/eval`, icon: BarChart3 },
    { name: "Members", href: `/projects/${project.id}/members`, icon: Users },
  ];

  return (
    <header className="sticky top-0 z-30 flex h-14 w-full items-center justify-between border-b border-slate-200/90 bg-white/95 backdrop-blur-sm px-5 shadow-xs shrink-0">
      {/* Left: Breadcrumbs & Workspace Context */}
      <div className="flex items-center gap-3 min-w-0">
        <Link
          href="/"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-900 text-white shadow-xs hover:bg-slate-800 transition-colors"
          title="Return to Workspaces Hub"
        >
          <Layers className="h-4 w-4" />
        </Link>

        <div className="flex items-center gap-1.5 text-xs text-slate-500 min-w-0">
          <Link
            href="/"
            className="hover:text-slate-900 transition-colors font-medium text-slate-500 hover:underline hidden sm:inline"
          >
            Workspaces
          </Link>
          <ChevronRight className="h-3 w-3 text-slate-300 hidden sm:inline" />
          <span className="font-semibold text-slate-900 truncate max-w-[180px] sm:max-w-xs text-sm">
            {project.name}
          </span>
          <Badge
            variant={project.role === "owner" ? "default" : "secondary"}
            className="capitalize text-[10px] py-0 px-1.5 font-medium ml-1"
          >
            {project.role || "viewer"}
          </Badge>
        </div>
      </div>

      {/* Center: Clean Segmented Navigation Tabs */}
      <nav className="flex items-center gap-1 bg-slate-100/90 p-1 rounded-xl border border-slate-200/60">
        {tabs.map((tab) => {
          const isActive = pathname === tab.href;
          const Icon = tab.icon;
          return (
            <Link
              key={tab.name}
              href={tab.href}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? "bg-white text-slate-900 shadow-xs font-semibold"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/50"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{tab.name}</span>
              {tab.badge !== undefined && tab.badge > 0 && (
                <span
                  className={`ml-0.5 rounded-full px-1.5 py-0.1 text-[10px] font-bold ${
                    isActive ? "bg-slate-900 text-white" : "bg-slate-200 text-slate-700"
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Right: User Profile & Quick Actions */}
      <div className="flex items-center gap-2.5">
        <div className="relative">
          <button
            onClick={() => setProfileOpen((prev) => !prev)}
            className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50/80 p-1 pr-2.5 hover:bg-slate-100 transition-colors"
          >
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-900 text-white text-[11px] font-bold">
              {user?.email ? user.email.charAt(0).toUpperCase() : "U"}
            </div>
            <span className="text-xs font-medium text-slate-700 max-w-[100px] truncate hidden md:inline">
              {user?.email?.split("@")[0] || "Account"}
            </span>
          </button>

          {profileOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setProfileOpen(false)} />
              <div className="absolute right-0 top-9 z-50 w-52 rounded-xl bg-white p-1.5 shadow-xl border border-slate-200 text-xs text-slate-700 animate-in fade-in">
                <div className="px-3 py-2 border-b border-slate-100">
                  <p className="font-semibold text-slate-900 truncate">{user?.email}</p>
                  <p className="text-[10px] text-slate-400 capitalize mt-0.5">{project.role || "Member"}</p>
                </div>
                <Link
                  href="/"
                  onClick={() => setProfileOpen(false)}
                  className="flex w-full items-center gap-2 px-3 py-2 mt-1 rounded-lg text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  <LayoutGrid className="h-3.5 w-3.5" />
                  All Workspaces
                </Link>
                <button
                  onClick={() => {
                    setProfileOpen(false);
                    logout();
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 rounded-lg text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  Sign Out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
};
