"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X, Copy, Check } from "lucide-react";

export type ToastType = "success" | "error" | "warning" | "info";

export interface ToastItem {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  traceId?: string;
  durationMs?: number;
}

interface ToastContextType {
  toasts: ToastItem[];
  addToast: (toast: Omit<ToastItem, "id">) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

type ToastListener = (toast: Omit<ToastItem, "id">) => void;
const listeners: Set<ToastListener> = new Set();

export const toast = {
  success: (message: string, title?: string, traceId?: string) => {
    listeners.forEach((fn) => fn({ type: "success", message, title, traceId }));
  },
  error: (message: string, title?: string, traceId?: string) => {
    listeners.forEach((fn) => fn({ type: "error", message, title, traceId }));
  },
  warning: (message: string, title?: string, traceId?: string) => {
    listeners.forEach((fn) => fn({ type: "warning", message, title, traceId }));
  },
  info: (message: string, title?: string, traceId?: string) => {
    listeners.forEach((fn) => fn({ type: "info", message, title, traceId }));
  },
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback((newToast: Omit<ToastItem, "id">) => {
    const id = Math.random().toString(36).substring(2, 9);
    const item: ToastItem = { ...newToast, id };
    setToasts((prev) => [...prev.slice(-4), item]);

    const duration = newToast.durationMs ?? (newToast.type === "error" ? 6000 : 4000);
    setTimeout(() => {
      removeToast(id);
    }, duration);
  }, [removeToast]);

  useEffect(() => {
    const handler: ToastListener = (t) => addToast(t);
    listeners.add(handler);
    return () => {
      listeners.delete(handler);
    };
  }, [addToast]);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-md w-full pointer-events-none px-4 sm:px-0">
        {toasts.map((t) => (
          <ToastCard key={t.id} toast={t} onClose={() => removeToast(t.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
};

const ToastCard: React.FC<{ toast: ToastItem; onClose: () => void }> = ({ toast: item, onClose }) => {
  const [copied, setCopied] = useState(false);

  const copyTrace = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!item.traceId) return;
    navigator.clipboard.writeText(item.traceId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const icons: Record<ToastType, React.ReactNode> = {
    success: <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />,
    error: <AlertCircle className="h-4 w-4 text-rose-500 shrink-0" />,
    warning: <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />,
    info: <Info className="h-4 w-4 text-blue-500 shrink-0" />,
  };

  const borderColors: Record<ToastType, string> = {
    success: "border-emerald-500/20 bg-slate-900/95 text-slate-100",
    error: "border-rose-500/30 bg-slate-900/95 text-slate-100",
    warning: "border-amber-500/20 bg-slate-900/95 text-slate-100",
    info: "border-blue-500/20 bg-slate-900/95 text-slate-100",
  };

  return (
    <div
      role="alert"
      className={`pointer-events-auto flex items-start gap-3 rounded-xl border p-3.5 shadow-2xl backdrop-blur-md transition-all animate-in fade-in slide-in-from-bottom-2 ${borderColors[item.type]}`}
    >
      <div className="mt-0.5">{icons[item.type]}</div>
      <div className="flex-1 min-w-0">
        {item.title && <div className="text-xs font-semibold text-white mb-0.5">{item.title}</div>}
        <div className="text-xs text-slate-300 break-words leading-relaxed">{item.message}</div>
        {item.traceId && (
          <div className="mt-2 flex items-center gap-1.5 text-[11px] text-slate-400">
            <span>Trace:</span>
            <code className="bg-slate-800 px-1.5 py-0.5 rounded font-mono text-slate-300 text-[10px]">
              {item.traceId.substring(0, 8)}
            </code>
            <button
              onClick={copyTrace}
              className="p-1 hover:text-white transition-colors"
              title="Copy full trace ID"
            >
              {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
            </button>
          </div>
        )}
      </div>
      <button
        onClick={onClose}
        className="text-slate-400 hover:text-white transition-colors p-1 -mr-1 -mt-1 rounded-lg hover:bg-slate-800"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
};
