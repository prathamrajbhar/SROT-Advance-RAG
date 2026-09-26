import React from "react";
import { Trash2, ExternalLink, AlertTriangle, CheckCircle, Clock } from "lucide-react";
import { DocumentItem } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatBytes } from "@/lib/utils";

export interface UploadProgressListProps {
  documents: DocumentItem[];
  onDelete: (id: string) => void;
  onView: (id: string) => void;
}

export const UploadProgressList: React.FC<UploadProgressListProps> = ({
  documents,
  onDelete,
  onView,
}) => {
  if (documents.length === 0) {
    return (
      <div className="text-center py-8 text-xs text-slate-500">
        No documents uploaded to this project yet.
      </div>
    );
  }

  const getStatusBadge = (doc: DocumentItem) => {
    switch (doc.status) {
      case "indexed":
        return <Badge variant="success"><CheckCircle className="h-3 w-3" /> Indexed</Badge>;
      case "failed":
        return <Badge variant="danger"><AlertTriangle className="h-3 w-3" /> Failed</Badge>;
      default:
        return <Badge variant="warning"><Clock className="h-3 w-3" /> {doc.status}</Badge>;
    }
  };

  return (
    <div className="divide-y divide-slate-200 border border-slate-200 rounded-xl bg-white overflow-hidden shadow-sm">
      {documents.map((doc) => (
        <div key={doc.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
          <div className="flex-1 min-w-0 pr-4">
            <div className="flex items-center gap-2">
              <span className="font-medium text-sm text-slate-900 truncate">
                {doc.filename}
              </span>
              {getStatusBadge(doc)}
              {doc.pii_flags && doc.pii_flags.density && doc.pii_flags.density !== "none" && (
                <Badge variant="warning">
                  PII: {doc.pii_flags.density}
                </Badge>
              )}
            </div>

            <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
              <span>{formatBytes(doc.size_bytes)}</span>
              {doc.stats?.chunk_count && (
                <span>· {doc.stats.chunk_count} chunks</span>
              )}
              {doc.error_human && (
                <span className="text-red-600 font-medium">· {doc.error_human}</span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {doc.status === "indexed" && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onView(doc.id)}
                title="View document"
              >
                <ExternalLink className="h-4 w-4" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDelete(doc.id)}
              className="text-red-600 hover:bg-red-50 hover:text-red-700"
              title="Delete document"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
};
