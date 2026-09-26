import React, { useRef, useState } from "react";
import { UploadCloud, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface FileDropzoneProps {
  onFilesSelected: (files: File[]) => void;
  isUploading?: boolean;
}

export const FileDropzone: React.FC<FileDropzoneProps> = ({
  onFilesSelected,
  isUploading = false,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFilesSelected(Array.from(e.dataTransfer.files));
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFilesSelected(Array.from(e.target.files));
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
        isDragOver
          ? "border-slate-900 bg-slate-50"
          : "border-slate-300 bg-white hover:border-slate-400"
      }`}
    >
      <input
        type="file"
        ref={inputRef}
        onChange={handleChange}
        multiple
        className="hidden"
        accept=".pdf,.docx,.txt,.md,.xlsx,.csv,.mp3,.mp4"
      />
      <div className="flex flex-col items-center justify-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 mb-3">
          <UploadCloud className="h-6 w-6 text-slate-600" />
        </div>
        <h4 className="text-sm font-semibold text-slate-800">
          Upload project documents
        </h4>
        <p className="text-xs text-slate-500 mt-1 max-w-sm">
          Drag & drop your files here, or click to browse. Supported formats: PDF, DOCX, TXT, MD, XLSX, CSV, MP3, MP4.
        </p>

        <Button
          type="button"
          variant="outline"
          size="sm"
          className="mt-4"
          disabled={isUploading}
          isLoading={isUploading}
          onClick={() => inputRef.current?.click()}
        >
          <FileText className="h-4 w-4 mr-1.5" />
          Select Files
        </Button>
      </div>
    </div>
  );
};
