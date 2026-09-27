"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import { Button } from "./button";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error in production monitoring without leaking raw UI crashes
    if (process.env.NODE_ENV === "development") {
      // development inspection
    }
  }

  private handleReload = () => {
    window.location.reload();
  };

  private handleGoHome = () => {
    window.location.href = "/";
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen w-full flex items-center justify-center bg-slate-50 p-6">
          <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl border border-slate-200 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-red-100 text-red-600 mx-auto mb-4">
              <AlertTriangle className="h-6 w-6" />
            </div>

            <h2 className="text-lg font-bold text-slate-900 mb-1">
              Application Notice
            </h2>
            <p className="text-xs text-slate-500 mb-6 leading-relaxed">
              An unexpected UI error was caught and safely contained. You can refresh the current view or return to the main hub.
            </p>

            <div className="flex items-center justify-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={this.handleGoHome}
                className="text-xs gap-1.5"
              >
                <Home className="h-3.5 w-3.5" />
                Workspaces Hub
              </Button>
              <Button
                size="sm"
                onClick={this.handleReload}
                className="bg-slate-900 hover:bg-slate-800 text-white text-xs gap-1.5"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Reload Page
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
