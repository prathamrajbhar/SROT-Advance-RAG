import { apiFetch } from "@/lib/api-client";
import {
  CompletedPartItem,
  DocumentListResponse,
  MultipartInitiateResponse,
  PresignedPartItem,
} from "./types";

export async function listDocumentsApi(workspaceId: string): Promise<DocumentListResponse> {
  return apiFetch<DocumentListResponse>(`/documents?workspace_id=${workspaceId}`, {
    method: "GET",
  });
}

export async function deleteDocumentApi(documentId: string): Promise<void> {
  return apiFetch<void>(`/documents/${documentId}`, {
    method: "DELETE",
  });
}

export async function initiateMultipartUploadApi(
  workspaceId: string,
  filename: string,
  fileSizeBytes: number,
  contentType = "application/octet-stream",
): Promise<MultipartInitiateResponse> {
  return apiFetch<MultipartInitiateResponse>("/documents/multipart/initiate", {
    method: "POST",
    body: JSON.stringify({
      workspace_id: workspaceId,
      filename,
      file_size_bytes: fileSizeBytes,
      content_type: contentType,
    }),
  });
}

export async function presignPartsApi(
  documentId: string,
  uploadId: string,
  s3Key: string,
  partNumbers: number[],
): Promise<{ parts: PresignedPartItem[] }> {
  return apiFetch<{ parts: PresignedPartItem[] }>("/documents/multipart/presign-parts", {
    method: "POST",
    body: JSON.stringify({
      document_id: documentId,
      upload_id: uploadId,
      s3_key: s3Key,
      part_numbers: partNumbers,
    }),
  });
}

export async function completeMultipartUploadApi(
  documentId: string,
  uploadId: string,
  s3Key: string,
  parts: CompletedPartItem[],
): Promise<{ document_id: string; status: string; processing_job_id?: string }> {
  return apiFetch<{ document_id: string; status: string; processing_job_id?: string }>(
    "/documents/multipart/complete",
    {
      method: "POST",
      body: JSON.stringify({
        document_id: documentId,
        upload_id: uploadId,
        s3_key: s3Key,
        parts,
      }),
    },
  );
}
