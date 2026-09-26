import React from "react";
import { Citation } from "@/types";
import { Modal } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import { ExternalLink } from "lucide-react";

export interface DocumentViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  citation: Citation | null;
  documentUrl?: string | null;
}

export const DocumentViewerModal: React.FC<DocumentViewerModalProps> = ({
  isOpen,
  onClose,
  citation,
  documentUrl,
}) => {
  if (!citation) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Citation Evidence: ${citation.document_name}`}
    >
      <div className="space-y-4">
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-700">
          <div className="font-semibold text-slate-900 mb-1">Locator Information:</div>
          {citation.locator?.page_number && (
            <div>Page Number: {citation.locator.page_number}</div>
          )}
          {citation.locator?.start_s !== undefined && (
            <div>
              Timestamp Range: {citation.locator.start_s}s – {citation.locator.end_s}s
            </div>
          )}
          {citation.locator?.row_range && (
            <div>
              Row Range: {citation.locator.row_range[0]} – {citation.locator.row_range[1]} (Sheet: {citation.locator.sheet || "Sheet1"})
            </div>
          )}
        </div>

        <div>
          <div className="text-xs font-semibold text-slate-700 mb-1">Grounded Excerpt / Snippet:</div>
          <blockquote className="border-l-4 border-slate-900 bg-slate-50 p-3 text-xs text-slate-800 italic rounded-r-lg">
            {citation.snippet}
          </blockquote>
        </div>

        {documentUrl && (
          <div className="pt-2 flex justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open(documentUrl, "_blank")}
            >
              <ExternalLink className="h-4 w-4 mr-1.5" />
              Open Raw Document (Presigned S3 Link)
            </Button>
          </div>
        )}
      </div>
    </Modal>
  );
};
