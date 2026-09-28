export type DocumentModality = "document" | "tabular" | "video" | "audio";
export type DocumentStatus = "INITIATED" | "UPLOADED" | "PROCESSING" | "READY" | "FAILED";

export interface DocumentItem {
  id: string;
  workspace_id: string;
  filename: string;
  file_type: DocumentModality | string;
  file_size_bytes: number;
  status: DocumentStatus | string;
  chunk_count: number;
  created_at: string;
  job_stage?: string;
  job_progress?: number;
  job_message?: string;
}

export interface DocumentListResponse {
  documents: DocumentItem[];
  total: number;
}

export interface MultipartInitiateResponse {
  document_id: string;
  upload_id: string;
  s3_key: string;
  chunk_size_bytes: number;
  total_parts: number;
}

export interface PresignedPartItem {
  part_number: number;
  presigned_url: string;
}

export interface CompletedPartItem {
  part_number: number;
  etag: string;
}

export interface FileUploadTask {
  id: string;
  file: File;
  documentId?: string;
  status: "idle" | "uploading" | "assembling" | "completed" | "error" | "paused";
  progressPercent: number;
  uploadedBytes: number;
  totalBytes: number;
  error?: string;
}
