"use client";

import React, { useState } from "react";
import { Layers, Plus, Search, LogOut, User, Sparkles } from "lucide-react";
import { User as UserType } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface WorkspacesHeaderProps {
  user: UserType | null;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onNewWorkspace: () => void;
  onLogout: () => void;
}

export const WorkspacesHeader: React.FC<WorkspacesHeaderProps> = ({
  user,
  searchQuery,
  onSearchChange,
  onNewWorkspace,
  onLogout,
}) => {
  const [profileOpen, setProfileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200 bg-white px-6 shadow-sm">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
            <Layers className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold tracking-tight text-slate-900 text-base">SROT</span>
              <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-600 border border-slate-200">
                Enterprise v2.0
              </span>
            </div>
            <span className="text-[11px] text-slate-400 block -mt-0.5">Unified Knowledge Hub</span>
          </div>
        </div>

        <div className="hidden md:flex relative items-center ml-8 w-72">
          <Search className="absolute left-3 h-3.5 w-3.5 text-slate-400" />
          <Input
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search workspaces..."
            className="pl-8 h-8 text-xs bg-slate-50/80 border-slate-200 focus:bg-white transition-colors"
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Button
          onClick={onNewWorkspace}
          size="sm"
          className="bg-slate-900 hover:bg-slate-800 text-white text-xs gap-1.5 shadow-sm"
        >
          <Plus className="h-3.5 w-3.5" />
          New Workspace
        </Button>

        <div className="relative">
          <button
            onClick={() => setProfileOpen((prev) => !prev)}
            className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 p-1 pr-3 hover:bg-slate-100 transition-colors"
          >
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-900 text-white text-xs font-semibold">
              {user?.email ? user.email.charAt(0).toUpperCase() : "U"}
            </div>
            <span className="text-xs font-medium text-slate-700 max-w-[120px] truncate hidden sm:inline">
              {user?.email || "User"}
            </span>
          </button>

          {profileOpen && (
            <>
              <div className="fixed inset-0 z-20" onClick={() => setProfileOpen(false)} />
              <div className="absolute right-0 top-10 z-30 w-52 rounded-xl bg-white p-2 shadow-xl border border-slate-200 text-xs text-slate-700 animate-in fade-in">
                <div className="px-3 py-2 border-b border-slate-100">
                  <p className="font-semibold text-slate-900 truncate">{user?.email}</p>
                  <p className="text-[10px] text-slate-400 mt-0.5">Active Session</p>
                </div>
                <button
                  onClick={() => {
                    setProfileOpen(false);
                    onLogout();
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 mt-1 rounded-lg text-red-600 hover:bg-red-50 transition-colors"
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
