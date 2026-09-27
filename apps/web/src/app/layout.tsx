import type { Metadata } from "next";
import "./globals.css";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { ToastProvider } from "@/components/ui/toast";
import { AuthProvider } from "@/hooks/use-auth";

export const metadata: Metadata = {
  title: "SROT — Enterprise Multi-Project Multimodal RAG",
  description: "Enterprise Multi-Project Multimodal RAG Platform with confidence scoring and evidence citations.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 min-h-screen antialiased">
        <ErrorBoundary>
          <ToastProvider>
            <AuthProvider>
              {children}
            </AuthProvider>
          </ToastProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
