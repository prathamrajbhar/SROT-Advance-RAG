import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatBytes(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
}

export function formatConfidenceLabel(score: number): {
  label: string;
  color: "success" | "warning" | "danger";
} {
  if (score >= 0.75) {
    return { label: "High confidence", color: "success" };
  }
  if (score >= 0.5) {
    return { label: "Moderate — verify citations", color: "warning" };
  }
  return { label: "Low — likely insufficient evidence", color: "danger" };
}
